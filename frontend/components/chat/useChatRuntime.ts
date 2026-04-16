"use client";

import { AxiosError } from "axios";
import { useCallback, useEffect, useRef, useState } from "react";
import { ThreadItem, WorkflowNodeEntry } from "@/components/chat/types";
import {
    createChatThread,
    fetchBlogStatus,
    fetchFinalPost,
    fetchUserThreads,
    submitBlogReview,
    deleteThread,
} from "@/lib/api";
import { summarizeNodeOutput, toThreadItems } from "@/components/chat/chatWorkflow.helpers";

type UseChatRuntimeOptions = {
    userEmail: string | null;
    clearAuth: () => void;
    setDrawerOpen: (open: boolean) => void;
};

const WORKFLOW_NODE_ORDER = [
    "router_node",
    "research_query_gen_node",
    "researcher_node",
    "researcher_tools",
    "summarizer_node",
    "research_loop",
    "planner_node",
    "task_executer_node",
    "assembler_node",
    "editor_node",
    "critic_node",
    "human_review",
    "finalize_node",
] as const;

const WORKFLOW_NODE_TOTAL = WORKFLOW_NODE_ORDER.length;

const inferNextNodeFromUpdate = (nodeName: string, payloadObj: Record<string, unknown>) => {
    if (nodeName === "router_node") {
        const needsResearch = payloadObj.needs_research;
        if (typeof needsResearch === "boolean") {
            return needsResearch ? "research_query_gen_node" : "summarizer_node";
        }
    }

    if (nodeName === "research_loop") {
        const moreResearchNeeded = payloadObj.more_research_needed;
        if (typeof moreResearchNeeded === "boolean") {
            return moreResearchNeeded ? "router_node" : "planner_node";
        }
    }

    if (nodeName === "critic_node") {
        return "human_review";
    }

    return null;
};

export function useChatRuntime({ userEmail, clearAuth, setDrawerOpen }: UseChatRuntimeOptions) {
    const [threads, setThreads] = useState<ThreadItem[]>([]);
    const [threadsLoading, setThreadsLoading] = useState(false);

    const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
    const [activeThreadPrompt, setActiveThreadPrompt] = useState("");
    const [activeThreadMarkdown, setActiveThreadMarkdown] = useState("");
    const [activeThreadLoading, setActiveThreadLoading] = useState(false);

    const [prompt, setPrompt] = useState("");
    const [isCreatingChat, setIsCreatingChat] = useState(false);
    const [lastPrompt, setLastPrompt] = useState("");
    const [globalError, setGlobalError] = useState("");

    const [workflowNodes, setWorkflowNodes] = useState<WorkflowNodeEntry[]>([]);
    const [currentNode, setCurrentNode] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [waitingForApproval, setWaitingForApproval] = useState(false);
    const [approvalSubmitting, setApprovalSubmitting] = useState(false);
    const [activeApprovalAction, setActiveApprovalAction] = useState<"approve" | "reject" | null>(null);
    const [criticOutput, setCriticOutput] = useState("");
    const [editedDraft, setEditedDraft] = useState("");
    const [workflowStartTime, setWorkflowStartTime] = useState<number | null>(null);
    const [workflowTotalTime, setWorkflowTotalTime] = useState<number | null>(null);

    const streamRef = useRef<EventSource | null>(null);
    const streamThreadIdRef = useRef<string | null>(null);
    const threadsRef = useRef<ThreadItem[]>([]);
    const loadThreadByIdRef = useRef<((threadId: string) => Promise<void>) | null>(null);
    const hasSelectedInitialThreadRef = useRef(false);

    useEffect(() => {
        threadsRef.current = threads;
    }, [threads]);

    const closeStream = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.close();
            streamRef.current = null;
        }
        streamThreadIdRef.current = null;
    }, []);

    useEffect(() => {
        return () => {
            closeStream();
        };
    }, [closeStream]);

    const updateThreadStatus = useCallback((threadId: string, status: ThreadItem["status"]) => {
        setThreads((prev) => prev.map((thread) => (thread.threadId === threadId ? { ...thread, status } : thread)));
    }, []);

    const upsertWorkflowNode = useCallback((nodeName: string, output: string) => {
        const timestamp = new Date().toISOString();
        const now = Date.now();

        setWorkflowNodes((prev) => {
            const completedOlderRunning = prev.map((node) =>
                node.nodeName !== nodeName && node.status === "running" ? { ...node, status: "completed" as const, endTime: now, duration: (now - (node.startTime || now)) / 1000 } : node,
            );

            const existingIndex = completedOlderRunning.findIndex((node) => node.nodeName === nodeName);

            const updatedNode: WorkflowNodeEntry = {
                nodeName,
                output,
                updatedAt: timestamp,
                status: "running",
                startTime: existingIndex !== -1 ? completedOlderRunning[existingIndex].startTime : now,
            };

            if (existingIndex === -1) {
                return [...completedOlderRunning, updatedNode];
            }

            const updated = [...completedOlderRunning];
            updated.splice(existingIndex, 1);
            updated.push(updatedNode);
            return updated;
        });
    }, []);

    const markAllWorkflowNodesCompleted = useCallback(() => {
        const now = Date.now();
        setWorkflowNodes((prev) => prev.map((node) => ({
            ...node,
            status: "completed",
            endTime: node.endTime || now,
            duration: node.duration !== undefined ? node.duration : (now - (node.startTime || now)) / 1000
        })));
    }, []);

    const markCurrentNodeCompleted = useCallback((nodeName: string) => {
        if (!nodeName) return;
        const now = Date.now();
        setWorkflowNodes((prev) => prev.map((node) => (node.nodeName === nodeName ? {
            ...node,
            status: "completed",
            endTime: now,
            duration: (now - (node.startTime || now)) / 1000
        } : node)));
    }, []);

    const checkApprovalStatus = useCallback(
        async (threadId: string) => {
            try {
                const response = await fetchBlogStatus(threadId);
                const isWaiting = response.data.is_waiting_for_you;
                setWaitingForApproval(isWaiting);
                updateThreadStatus(threadId, isWaiting ? "waiting_approval" : "running");
            } catch (error: unknown) {
                console.error("Failed to check approval status", error);
            }
        },
        [updateThreadStatus],
    );

    const loadFinalThreadOutput = useCallback(
        async (threadId: string) => {
            if (!userEmail) return;

            try {
                const response = await fetchFinalPost({ user_id: userEmail, thread_id: threadId });
                setActiveThreadMarkdown(response.data.final_post_markdown || "No content returned for this thread.");
                updateThreadStatus(threadId, "completed");
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                if (maybeAxiosError.response?.status === 401) {
                    clearAuth();
                    return;
                }

                if (maybeAxiosError.response?.status === 404) {
                    setActiveThreadMarkdown("");
                    return;
                }

                console.error("Failed to load final thread output", error);
                setGlobalError("Unable to load final output for this thread.");
            }
        },
        [clearAuth, updateThreadStatus, userEmail],
    );

    const processStreamUpdate = useCallback(
        async (threadId: string, eventPayload: unknown) => {
            if (!eventPayload || typeof eventPayload !== "object") return;

            const payload = eventPayload as Record<string, unknown>;
            console.log("⚙️  Processing stream update:", payload.type);

            if (payload.event === "stream_end") {
                console.log("🏁 Stream end received");
                setIsStreaming(false);
                setActiveThreadLoading(false);
                closeStream();
                return;
            }

            const type = payload.type;

            if (type === "error") {
                console.error("❌ Workflow error:", payload.message);
                setIsStreaming(false);
                setActiveThreadLoading(false);
                setGlobalError(String(payload.message || "Streaming failed."));
                updateThreadStatus(threadId, "failed");
                closeStream();
                return;
            }

            if (type === "waiting_approval") {
                console.log("⏸️  Workflow waiting for approval");
                setIsStreaming(false);
                setActiveThreadLoading(false);
                markCurrentNodeCompleted(currentNode);
                setCurrentNode("human_review");
                await checkApprovalStatus(threadId);
                return;
            }

            if (type === "completed") {
                console.log("✅ Workflow completed");
                setIsStreaming(false);
                setActiveThreadLoading(false);
                setWaitingForApproval(false);
                setEditedDraft("");
                markAllWorkflowNodesCompleted();
                setCurrentNode("");

                // Calculate total workflow time
                if (workflowStartTime) {
                    const totalTime = (Date.now() - workflowStartTime) / 1000;
                    setWorkflowTotalTime(totalTime);
                }

                updateThreadStatus(threadId, "completed");
                await loadFinalThreadOutput(threadId);
                return;
            }

            if (type === "update") {
                console.log("📝 Workflow update received");

                // Set workflow start time on first update
                if (!workflowStartTime) {
                    setWorkflowStartTime(Date.now());
                }

                setActiveThreadLoading(true);
                setIsStreaming(true);
                updateThreadStatus(threadId, "running");
                if (!currentNode) {
                    setCurrentNode(WORKFLOW_NODE_ORDER[0]);
                }

                const data = payload.data;
                if (!data || typeof data !== "object") {
                    console.log("⚠️  No data in update payload");
                    return;
                }

                const nodeUpdates = Object.entries(data as Record<string, unknown>);
                console.log(`🔄 Processing ${nodeUpdates.length} nodes:`, nodeUpdates.map(([name]) => name));

                nodeUpdates.forEach(([nodeName, nodePayload]) => {
                    // Track the latest node update directly so the UI does not lag behind.
                    setCurrentNode(nodeName);

                    const payloadObj = nodePayload && typeof nodePayload === "object"
                        ? (nodePayload as Record<string, unknown>)
                        : {};
                    const inferredNextNode = inferNextNodeFromUpdate(nodeName, payloadObj);

                    if ("edited_draft" in payloadObj) {
                        const draftValue = payloadObj.edited_draft;
                        if (typeof draftValue === "string") {
                            setEditedDraft(draftValue);
                        }
                    }

                    const summary = summarizeNodeOutput(nodeName, nodePayload);
                    console.log(`📦 Node "${nodeName}" summary:`, summary.slice(0, 100) + "...");
                    upsertWorkflowNode(nodeName, summary);

                    if (inferredNextNode && inferredNextNode !== nodeName) {
                        const now = Date.now();
                        const timestamp = new Date(now).toISOString();

                        setWorkflowNodes((prev) => {
                            const withCurrentCompleted = prev.map((node) => {
                                if (node.nodeName !== nodeName || node.status !== "running") {
                                    return node;
                                }

                                return {
                                    ...node,
                                    status: "completed" as const,
                                    endTime: now,
                                    duration: node.duration !== undefined ? node.duration : (now - (node.startTime || now)) / 1000,
                                };
                            });

                            const nextIndex = withCurrentCompleted.findIndex((node) => node.nodeName === inferredNextNode);
                            if (nextIndex === -1) {
                                return [
                                    ...withCurrentCompleted,
                                    {
                                        nodeName: inferredNextNode,
                                        output: "",
                                        updatedAt: timestamp,
                                        status: "running",
                                        startTime: now,
                                    },
                                ];
                            }

                            const nextNode = withCurrentCompleted[nextIndex];
                            const updated = [...withCurrentCompleted];
                            updated[nextIndex] = {
                                ...nextNode,
                                status: "running",
                                updatedAt: timestamp,
                                startTime: nextNode.startTime ?? now,
                            };
                            return updated;
                        });

                        setCurrentNode(inferredNextNode);
                    }

                    if (nodeName.toLowerCase().includes("critic")) {
                        setCriticOutput(summary);
                        void checkApprovalStatus(threadId);
                    }
                });
            }
        },
        [
            checkApprovalStatus,
            closeStream,
            currentNode,
            loadFinalThreadOutput,
            markAllWorkflowNodesCompleted,
            markCurrentNodeCompleted,
            updateThreadStatus,
            workflowStartTime,
            upsertWorkflowNode,
        ],
    );

    const startThreadStream = useCallback(
        (threadId: string, streamUrl?: string) => {
            if (
                streamRef.current &&
                streamThreadIdRef.current === threadId &&
                (streamRef.current.readyState === EventSource.OPEN ||
                    streamRef.current.readyState === EventSource.CONNECTING)
            ) {
                return;
            }

            closeStream();
            setIsStreaming(true);
            setActiveThreadLoading(true);
            setCurrentNode(WORKFLOW_NODE_ORDER[0]);
            setWorkflowNodes([]);
            setWorkflowStartTime(null);
            setWorkflowTotalTime(null);

            const computedStreamUrl = streamUrl || `${process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "")}/blog/stream/${threadId}`;
            console.log("🔥 Starting stream for thread:", threadId, "URL:", computedStreamUrl);
            const source = new EventSource(computedStreamUrl, { withCredentials: true });
            streamRef.current = source;
            streamThreadIdRef.current = threadId;

            source.onmessage = (event) => {
                try {
                    const parsed = JSON.parse(event.data);
                    console.log("📡 Stream event received:", parsed.type, parsed);
                    void processStreamUpdate(threadId, parsed);
                } catch (error) {
                    console.log("⏭️  Skipping non-JSON event (heartbeat)");
                }
            };

            source.onerror = (error) => {
                console.error("❌ Stream error:", error);
                setIsStreaming(false);
                setActiveThreadLoading(false);
                closeStream();
            };

            source.onopen = () => {
                console.log("✅ Stream connection opened");
            };
        },
        [closeStream, processStreamUpdate],
    );

    const loadThreads = useCallback(
        async (email: string) => {
            setThreadsLoading(true);
            setGlobalError("");

            try {
                const response = await fetchUserThreads(email);
                console.log("📥 API returned threads:", response.data.length, "threads for user:", email);
                const items = toThreadItems(response.data);
                console.log("✨ Converted to thread items:", items);
                setThreads(items);
                // Don't auto-select a thread - let user start with a new chat
                hasSelectedInitialThreadRef.current = true;
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                const status = maybeAxiosError.response?.status;

                if (status === 404) {
                    console.log("ℹ️  No posts found for user");
                    setThreads([]);
                } else if (status === 401) {
                    console.error("🔐 Unauthorized access");
                    clearAuth();
                } else {
                    console.error("❌ Failed to load threads:", error);
                    setGlobalError("Unable to load your chats right now.");
                }
            } finally {
                setThreadsLoading(false);
            }
        },
        [clearAuth],
    );

    const loadThreadById = useCallback(
        async (threadId: string) => {
            if (!userEmail) return;

            setActiveThreadLoading(true);
            setGlobalError("");
            setWaitingForApproval(false);
            setWorkflowNodes([]);
            setCurrentNode("");
            setWorkflowStartTime(null);
            setWorkflowTotalTime(null);

            const activeThread = threadsRef.current.find((thread) => thread.threadId === threadId);
            if (activeThread && ["queued", "running", "waiting_approval"].includes(activeThread.status)) {
                setActiveThreadPrompt(activeThread.prompt ?? "");
                setActiveThreadMarkdown("");
                if (activeThread.status === "waiting_approval") {
                    await checkApprovalStatus(threadId);
                    setActiveThreadLoading(false);
                } else {
                    startThreadStream(threadId);
                }
                return;
            }

            closeStream();
            setIsStreaming(false);

            try {
                const response = await fetchFinalPost({ user_id: userEmail, thread_id: threadId });
                setActiveThreadMarkdown(response.data.final_post_markdown || "No content returned for this thread.");
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                const status = maybeAxiosError.response?.status;

                if (status === 404) {
                    setActiveThreadMarkdown("");
                    return;
                }

                if (status === 401) {
                    clearAuth();
                    return;
                }

                console.error("Failed to load thread", error);
                setActiveThreadMarkdown("Unable to load this chat at the moment.");
            } finally {
                setActiveThreadLoading(false);
            }
        },
        [checkApprovalStatus, clearAuth, closeStream, startThreadStream, userEmail],
    );

    useEffect(() => {
        loadThreadByIdRef.current = loadThreadById;
    }, [loadThreadById]);

    useEffect(() => {
        if (!userEmail) return;
        void loadThreads(userEmail);
    }, [loadThreads, userEmail]);

    useEffect(() => {
        if (!activeThreadId) {
            setActiveThreadMarkdown("");
            return;
        }

        if (!userEmail) return;
        const run = loadThreadByIdRef.current;
        if (!run) return;
        void run(activeThreadId);
    }, [activeThreadId, userEmail]);

    const handleCreateNewChat = useCallback(
        async (seedPrompt: string) => {
            if (!userEmail || isCreatingChat) return;

            const normalizedPrompt = seedPrompt.trim();
            if (!normalizedPrompt) return;

            setIsCreatingChat(true);
            setGlobalError("");
            setActiveThreadMarkdown("");
            setActiveThreadLoading(true);
            setWaitingForApproval(false);
            setCriticOutput("");
            setWorkflowNodes([]);
            setCurrentNode("");

            try {
                const response = await createChatThread({
                    user_id: userEmail,
                    prompt: normalizedPrompt,
                });

                const newThread: ThreadItem = {
                    threadId: response.data.thread_id,
                    preview: normalizedPrompt.slice(0, 90),
                    prompt: normalizedPrompt,
                    status: "queued",
                };

                setThreads((prev) => {
                    if (prev.some((thread) => thread.threadId === newThread.threadId)) {
                        return prev;
                    }
                    return [newThread, ...prev];
                });

                setActiveThreadId(newThread.threadId);
                setActiveThreadPrompt(normalizedPrompt);
                setActiveThreadMarkdown("");
                setDrawerOpen(false);
                startThreadStream(newThread.threadId, response.data.stream_url);
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                const status = maybeAxiosError.response?.status;

                if (status === 401) {
                    clearAuth();
                } else {
                    console.error("Failed to create a new chat", error);
                    setGlobalError("Unable to create a new chat right now.");
                }

                setActiveThreadLoading(false);
                setIsStreaming(false);
            } finally {
                setIsCreatingChat(false);
            }
        },
        [clearAuth, isCreatingChat, setDrawerOpen, startThreadStream, userEmail],
    );

    const handlePromptSubmit = useCallback(
        async (event: React.FormEvent<HTMLFormElement>) => {
            event.preventDefault();

            if (activeThreadId) {
                setGlobalError("This chat has ended. Click New Chat to start another prompt.");
                return;
            }

            const trimmedPrompt = prompt.trim();
            if (!trimmedPrompt) return;

            setLastPrompt(trimmedPrompt);
            setPrompt("");
            await handleCreateNewChat(trimmedPrompt);
        },
        [activeThreadId, handleCreateNewChat, prompt],
    );

    const handleQuickNewChat = useCallback(() => {
        closeStream();
        setIsStreaming(false);
        setActiveThreadLoading(false);
        setGlobalError("");
        setPrompt("");
        setLastPrompt("");
        setActiveThreadPrompt("");
        setActiveThreadId(null);
        setActiveThreadMarkdown("");
        setWorkflowNodes([]);
        setCurrentNode("");
        setWaitingForApproval(false);
        setCriticOutput("");
        setEditedDraft("");
        setDrawerOpen(false);
    }, [closeStream, setDrawerOpen]);

    const handleReviewDecision = useCallback(
        async (approved: boolean) => {
            if (!activeThreadId || activeApprovalAction !== null) return;

            setActiveApprovalAction(approved ? "approve" : "reject");
            setApprovalSubmitting(true);
            setGlobalError("");

            try {
                await submitBlogReview({ thread_id: activeThreadId, approved });
                setWaitingForApproval(false);
                setActiveThreadLoading(true);
                setIsStreaming(true);
                updateThreadStatus(activeThreadId, "running");
                startThreadStream(activeThreadId);
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                if (maybeAxiosError.response?.status === 401) {
                    clearAuth();
                    return;
                }

                console.error("Failed to submit review", error);
                setGlobalError("Unable to submit your review decision.");
            } finally {
                setApprovalSubmitting(false);
                setActiveApprovalAction(null);
            }
        },
        [activeApprovalAction, activeThreadId, clearAuth, startThreadStream, updateThreadStatus],
    );

    const handleDeleteThread = useCallback(
        async (threadId: string) => {
            if (!userEmail) return;

            try {
                await deleteThread({ user_id: userEmail, thread_id: threadId });

                // Remove thread from list
                setThreads((prev) => prev.filter((thread) => thread.threadId !== threadId));

                // If the deleted thread was active, clear the view
                if (activeThreadId === threadId) {
                    setActiveThreadId(null);
                    setActiveThreadMarkdown("");
                    setActiveThreadPrompt("");
                }

                console.log("✅ Thread deleted successfully");
            } catch (error: unknown) {
                const maybeAxiosError = error as AxiosError;
                if (maybeAxiosError.response?.status === 401) {
                    clearAuth();
                    return;
                }

                console.error("Failed to delete thread", error);
                setGlobalError("Unable to delete thread. Please try again.");
            }
        },
        [activeThreadId, clearAuth, userEmail],
    );

    const resetRuntime = useCallback(() => {
        closeStream();
        setThreads([]);
        setThreadsLoading(false);
        setActiveThreadId(null);
        setActiveThreadMarkdown("");
        setActiveThreadLoading(false);
        setPrompt("");
        setIsCreatingChat(false);
        setLastPrompt("");
        setActiveThreadPrompt("");
        setGlobalError("");
        setWorkflowNodes([]);
        setCurrentNode("");
        setIsStreaming(false);
        setWaitingForApproval(false);
        setApprovalSubmitting(false);
        setActiveApprovalAction(null);
        setCriticOutput("");
        setEditedDraft("");
        hasSelectedInitialThreadRef.current = false;
    }, [closeStream]);

    return {
        threads,
        threadsLoading,
        activeThreadId,
        activeThreadPrompt,
        activeThreadMarkdown,
        activeThreadLoading,
        prompt,
        isCreatingChat,
        lastPrompt,
        globalError,
        workflowNodes,
        currentNode,
        isStreaming,
        waitingForApproval,
        approvalSubmitting,
        activeApprovalAction,
        criticOutput,
        editedDraft,
        workflowTotalNodes: WORKFLOW_NODE_TOTAL,
        workflowStartTime,
        workflowTotalTime,
        setActiveThreadId,
        setPrompt,
        handlePromptSubmit,
        handleQuickNewChat,
        handleReviewDecision,
        handleDeleteThread,
        resetRuntime,
    };
}