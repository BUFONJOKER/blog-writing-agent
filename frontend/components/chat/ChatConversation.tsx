"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { WorkflowNodeEntry } from "@/components/chat/types";

const NODE_DESCRIPTIONS: Record<string, string> = {
    router_node: "Classifies prompt intent and routes workflow path.",
    research_query_gen_node: "Builds focused search queries from prompt and gaps.",
    researcher_node: "Runs research and gathers source information.",
    researcher_tools: "Invokes tool calls for web lookup and data fetch.",
    summarizer_node: "Condenses collected research into actionable notes.",
    research_loop: "Checks gaps and decides if more research is needed.",
    planner_node: "Creates article outline and section-level writing plan.",
    task_executer_node: "Drafts content for each planned section task.",
    assembler_node: "Combines section outputs into a single draft.",
    editor_node: "Polishes wording, clarity, and structure of the draft.",
    critic_node: "Evaluates quality and flags issues before approval.",
    human_review: "Pauses for your approval decision to continue.",
    __interrupt__: "Workflow pause/interrupt checkpoint awaiting resume decision.",
    finalize_node: "Produces the final publish-ready markdown output.",
};

type ChatConversationProps = {
    globalError: string;
    activeThreadPrompt: string;
    activeThreadId: string | null;
    activeThreadLoading: boolean;
    activeThreadMarkdown: string;
    isStreaming: boolean;
    currentNode: string;
    workflowNodes: WorkflowNodeEntry[];
    workflowTotalNodes: number;
    workflowStartTime: number | null;
    workflowTotalTime: number | null;
    waitingForApproval: boolean;
    approvalSubmitting: boolean;
    activeApprovalAction: "approve" | "reject" | null;
    criticOutput: string;
    editedDraft: string;
    onApprove: () => void;
    onReject: () => void;
};

export function ChatConversation({
    globalError,
    activeThreadPrompt,
    activeThreadId,
    activeThreadLoading,
    activeThreadMarkdown,
    isStreaming,
    currentNode,
    workflowNodes,
    workflowTotalNodes,
    workflowStartTime,
    workflowTotalTime,
    waitingForApproval,
    approvalSubmitting,
    activeApprovalAction,
    criticOutput,
    editedDraft,
    onApprove,
    onReject,
}: ChatConversationProps) {
    const [copyStatus, setCopyStatus] = useState<"idle" | "copied" | "error">("idle");
    const [runningNow, setRunningNow] = useState(() => Date.now());
    const workflowEndRef = useRef<HTMLDivElement | null>(null);
    const hasActiveContent = Boolean(activeThreadId && activeThreadMarkdown);

    const completedNodes = useMemo(
        () => workflowNodes.filter((node) => node.status === "completed").length,
        [workflowNodes],
    );
    const hasNodeOutput = useMemo(
        () => workflowNodes.some((node) => node.output.trim().length > 0),
        [workflowNodes],
    );
    const progressPct = workflowTotalNodes > 0 ? Math.round((completedNodes / workflowTotalNodes) * 100) : 0;
    const runningNodeName = useMemo(() => {
        for (let i = workflowNodes.length - 1; i >= 0; i--) {
            if (workflowNodes[i].status === "running") {
                return workflowNodes[i].nodeName;
            }
        }
        return "";
    }, [workflowNodes]);
    const displayedCurrentNode = waitingForApproval ? "human_review" : runningNodeName || currentNode;

    useEffect(() => {
        if (!activeThreadId || workflowNodes.length === 0) return;
        workflowEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }, [activeThreadId, currentNode, workflowNodes]);

    useEffect(() => {
        const hasRunningNode = workflowNodes.some((node) => node.status === "running");
        if (!hasRunningNode) return;

        setRunningNow(Date.now());
        const timerId = window.setInterval(() => {
            setRunningNow(Date.now());
        }, 1000);

        return () => {
            window.clearInterval(timerId);
        };
    }, [workflowNodes]);

    const statusBadgeClass = (status: WorkflowNodeEntry["status"]) => {
        if (status === "completed") return "border-emerald-500/40 bg-emerald-500/15 text-emerald-300";
        if (status === "running") return "border-blue-500/40 bg-blue-500/15 text-blue-300";
        return "border-zinc-700 bg-zinc-800/70 text-zinc-400";
    };

    const statusText = (status: WorkflowNodeEntry["status"]) => {
        if (status === "completed") return "completed";
        if (status === "running") return "running";
        return "pending";
    };

    const formatDuration = (seconds: number) => {
        const total = Math.max(0, Math.floor(seconds));
        const mins = Math.floor(total / 60);
        const secs = total % 60;
        return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    const getNodeElapsedSeconds = (node: WorkflowNodeEntry, index: number) => {
        if (node.status === "running") {
            const fallbackStart = node.updatedAt ? new Date(node.updatedAt).getTime() : runningNow;
            const startMs = node.startTime ?? fallbackStart;
            return Math.max(0, (runningNow - startMs) / 1000);
        }

        if (node.duration !== undefined && node.duration > 0) {
            return node.duration;
        }

        const previousNode = index > 0 ? workflowNodes[index - 1] : undefined;
        if (node.updatedAt && previousNode?.updatedAt) {
            const estimated = (new Date(node.updatedAt).getTime() - new Date(previousNode.updatedAt).getTime()) / 1000;
            if (estimated > 0) {
                return estimated;
            }
        }

        return node.duration;
    };

    const getNodePreview = (output: string) => {
        const compact = output.replace(/\s+/g, " ").trim();
        if (!compact) return "No output yet";
        return compact.length > 72 ? `${compact.slice(0, 72)}...` : compact;
    };

    const handleCopyMarkdown = async () => {
        if (!activeThreadMarkdown) return;

        try {
            await navigator.clipboard.writeText(activeThreadMarkdown);
            setCopyStatus("copied");
            window.setTimeout(() => setCopyStatus("idle"), 1600);
        } catch {
            setCopyStatus("error");
            window.setTimeout(() => setCopyStatus("idle"), 1600);
        }
    };

    const handleDownloadMarkdown = () => {
        if (!activeThreadMarkdown) return;

        const blob = new Blob([activeThreadMarkdown], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${activeThreadId || "blog-post"}.md`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex-1 space-y-4">
            {globalError && <p className="text-sm text-rose-400">{globalError}</p>}

            {activeThreadPrompt && (
                <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl border border-zinc-700 bg-zinc-800/70 px-4 py-3">
                        <p className="mb-1 text-xs uppercase tracking-wide text-zinc-400">You</p>
                        <p className="text-sm text-zinc-100">{activeThreadPrompt}</p>
                    </div>
                </div>
            )}

            {!activeThreadId && (
                <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 text-sm text-zinc-400">
                    Select a chat from the menu, or start a new chat.
                </div>
            )}

            {activeThreadLoading && activeThreadId && (
                <div className="rounded-2xl border border-blue-500/30 bg-zinc-900/60 p-5 text-sm text-zinc-400">
                    Loading thread {activeThreadId}...
                </div>
            )}

            {activeThreadId && (isStreaming || workflowNodes.length > 0 || waitingForApproval) && (
                <details open className="rounded-2xl border border-zinc-700 bg-zinc-900/60 p-4">
                    <summary className="cursor-pointer text-sm font-semibold text-zinc-200">
                        📡 Workflow progress ({workflowNodes.length})
                    </summary>

                    <div className="mt-3 space-y-3">
                        <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
                            <div className="mb-2 flex items-center justify-between text-xs text-zinc-400">
                                <span>Overall progress</span>
                                <span>
                                    {completedNodes}/{workflowTotalNodes} completed ({progressPct}%)
                                </span>
                            </div>
                            <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
                                <div
                                    className="h-full rounded-full bg-blue-500 transition-all duration-500"
                                    style={{ width: `${progressPct}%` }}
                                />
                            </div>
                            {workflowTotalTime !== null && !isStreaming && (
                                <div className="mt-2 pt-2 border-t border-zinc-700 flex justify-between text-xs text-zinc-400">
                                    <span>Total workflow time:</span>
                                    <span className="font-semibold text-blue-400">⏱️ {workflowTotalTime.toFixed(2)}s</span>
                                </div>
                            )}
                        </div>

                        <p className="text-xs text-zinc-400">
                            {isStreaming
                                ? `Current node: ${displayedCurrentNode || "starting..."}`
                                : waitingForApproval
                                    ? "Current node: human_review (awaiting your approval)"
                                    : "Streaming complete"}
                        </p>

                        {workflowNodes.length === 0 && (
                            <p className="text-sm text-zinc-400">Waiting for first workflow update...</p>
                        )}

                        {hasNodeOutput && (
                            <div className="space-y-2 rounded-lg border border-zinc-800 bg-zinc-950/40 p-3">
                                <label className="text-xs font-semibold text-zinc-400">View Node Output:</label>
                                <select
                                    defaultValue=""
                                    onChange={(e) => {
                                        if (e.target.value) {
                                            const element = document.querySelector(`[data-node-id="${e.target.value}"]`);
                                            if (element instanceof HTMLDetailsElement) {
                                                element.open = true;
                                                element.scrollIntoView({ behavior: "smooth", block: "nearest" });
                                            }
                                        }
                                    }}
                                    className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 transition focus:border-blue-500 focus:outline-none hover:border-zinc-600"
                                >
                                    <option value="">📋 Select a node...</option>
                                    {workflowNodes.map((node) => (
                                        <option key={node.nodeName} value={node.nodeName}>
                                            {node.status === "completed" ? "✓" : node.status === "running" ? "⟳" : "○"} {node.nodeName} - {getNodePreview(node.output)}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {workflowNodes.map((node, index) => {
                            const nodeElapsedSeconds = getNodeElapsedSeconds(node, index);
                            const nodeDescription = NODE_DESCRIPTIONS[node.nodeName] || "Processes this workflow stage.";

                            return (
                                <details
                                    key={node.nodeName}
                                    data-node-id={node.nodeName}
                                    className={`rounded-xl border bg-zinc-950/70 ${
                                        node.nodeName === displayedCurrentNode
                                            ? "border-blue-500/60 shadow-[0_0_0_1px_rgba(59,130,246,0.35)]"
                                            : "border-zinc-800"
                                    }`}
                                >
                                    <summary className="cursor-pointer px-3 py-2.5 text-xs font-semibold uppercase tracking-wide text-zinc-200 hover:bg-zinc-900/50">
                                        <div className="flex flex-wrap items-center justify-between gap-2">
                                            <div className="min-w-0 flex-1">
                                                <div className="flex items-center gap-2">
                                                    <span>▶ {node.nodeName}</span>
                                                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${statusBadgeClass(node.status)}`}>
                                                        {statusText(node.status)}
                                                    </span>
                                                    {node.status === "running" && (
                                                        <span
                                                            className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-300 border-t-transparent"
                                                            aria-label="Running node"
                                                        />
                                                    )}
                                                </div>
                                                <p className="mt-1 truncate text-[11px] normal-case tracking-normal text-zinc-400">
                                                    {nodeDescription}
                                                </p>
                                            </div>
                                            <span className="flex gap-3 text-zinc-500 text-xs">
                                                <span>{node.output.length} chars</span>
                                                {nodeElapsedSeconds !== undefined && (
                                                    <span>⏱️ {formatDuration(nodeElapsedSeconds)}</span>
                                                )}
                                            </span>
                                        </div>
                                    </summary>
                                    <div className="border-t border-zinc-800 bg-black/40 px-3 py-3">
                                        {node.output ? (
                                            <pre className="max-h-96 overflow-y-auto whitespace-pre-wrap font-mono text-xs text-zinc-300">
                                                {node.output}
                                            </pre>
                                        ) : (
                                            <p className="text-xs text-zinc-500">No output yet.</p>
                                        )}
                                        <p className="mt-2 text-xs text-zinc-500">
                                            Updated: {node.updatedAt ? new Date(node.updatedAt).toLocaleTimeString() : "Not started"}
                                            {nodeElapsedSeconds !== undefined && (
                                                <span>
                                                    {node.status === "running" ? " | Running for: " : " | Duration: "}
                                                    {formatDuration(nodeElapsedSeconds)}
                                                </span>
                                            )}
                                        </p>
                                    </div>
                                </details>
                            );
                        })}
                        <div ref={workflowEndRef} />

                        {waitingForApproval && (
                            <div className="rounded-xl border border-amber-700/60 bg-amber-950/30 p-3">
                                <p className="text-xs font-semibold uppercase tracking-wide text-amber-300">Critic review required</p>
                                {criticOutput && <pre className="mt-2 whitespace-pre-wrap text-xs text-zinc-200">{criticOutput}</pre>}

                                <div className="mt-3 space-y-2">
                                    <label className="text-xs font-semibold uppercase tracking-wide text-zinc-300">
                                        Edited draft
                                    </label>
                                    {editedDraft ? (
                                        <pre className="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-200">
                                            {editedDraft}
                                        </pre>
                                    ) : (
                                        <p className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-xs text-zinc-500">
                                            Edited draft not available in workflow state yet.
                                        </p>
                                    )}
                                    <p className="text-xs text-zinc-500">Draft length: {editedDraft.length} chars</p>
                                </div>

                                <div className="mt-3 flex flex-wrap gap-2">
                                    <button
                                        type="button"
                                        onClick={onApprove}
                                        disabled={approvalSubmitting || activeApprovalAction !== null}
                                        className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500 disabled:bg-zinc-700"
                                    >
                                        {activeApprovalAction === "approve" ? "Submitting..." : "Approve"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={onReject}
                                        disabled={approvalSubmitting || activeApprovalAction !== null}
                                        className="rounded-lg bg-rose-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-rose-600 disabled:bg-zinc-700"
                                    >
                                        {activeApprovalAction === "reject" ? "Submitting..." : "Not Approve"}
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </details>
            )}

            {hasActiveContent && !activeThreadLoading && (
                <div className="flex justify-start">
                    <div className="w-full rounded-2xl border border-blue-500/30 bg-zinc-900/60 p-5">
                        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                            <p className="text-xs uppercase tracking-wide text-blue-400">Final Blog Generated</p>

                            {workflowTotalTime !== null && (
                                <p className="text-xs font-semibold text-zinc-300">⏱️ Generated in {workflowTotalTime.toFixed(2)}s</p>
                            )}

                            <div className="flex flex-wrap gap-2">
                                <button
                                    type="button"
                                    onClick={handleCopyMarkdown}
                                    className="rounded-lg border border-zinc-700 bg-zinc-950/80 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition hover:border-blue-500 hover:text-white"
                                >
                                    {copyStatus === "copied" ? "Copied" : copyStatus === "error" ? "Copy failed" : "Copy markdown"}
                                </button>
                                <button
                                    type="button"
                                    onClick={handleDownloadMarkdown}
                                    className="rounded-lg border border-zinc-700 bg-zinc-950/80 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition hover:border-blue-500 hover:text-white"
                                >
                                    Download markdown
                                </button>
                            </div>
                        </div>
                        {activeThreadPrompt && (
                            <div className="mb-4 rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
                                <p className="text-xs uppercase tracking-wide text-zinc-400">Prompt</p>
                                <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-100">{activeThreadPrompt}</p>
                            </div>
                        )}
                        <article className="prose prose-invert max-w-none">
                            <ReactMarkdown>{activeThreadMarkdown}</ReactMarkdown>
                        </article>
                    </div>
                </div>
            )}
        </div>
    );
}
