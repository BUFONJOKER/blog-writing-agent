import { ThreadItem } from "@/components/chat/types";
import { UserPost } from "@/lib/api";

export function toThreadItems(posts: UserPost[]): ThreadItem[] {
    return posts.map((post) => ({
        threadId: post.thread_id,
        preview: post.final_post_markdown?.slice(0, 90).trim() || post.prompt?.slice(0, 90).trim() || "Blog post",
        prompt: post.prompt || "",
        createdAt: post.created_at,
        status: "ready",
    }));
}

export function toText(value: unknown): string {
    if (typeof value === "string") return value;

    if (Array.isArray(value)) {
        return value
            .map((item) => {
                if (typeof item === "string") return item;
                if (item && typeof item === "object" && "text" in item) {
                    return String((item as { text?: unknown }).text ?? "");
                }
                return "";
            })
            .filter(Boolean)
            .join("\n");
    }

    return "";
}

export function summarizeNodeOutput(nodeName: string, payload: unknown): string {
    if (!payload || typeof payload !== "object") {
        return `${nodeName} updated.`;
    }

    const payloadObj = payload as Record<string, unknown>;

    // Check for research results first (most important for display)
    if ("research_results" in payloadObj && Array.isArray(payloadObj.research_results)) {
        const results = payloadObj.research_results as Array<unknown>;
        if (results.length > 0) {
            try {
                // Summarize research results
                const summary = results
                    .slice(0, 3) // Show top 3 results
                    .map((r) => {
                        if (typeof r === "object" && r !== null) {
                            const res = r as Record<string, unknown>;
                            const title = res.title || res.name || "Source";
                            const content = String(res.content || res.text || "").slice(0, 100);
                            return `- ${title}: ${content}...`;
                        }
                        return String(r);
                    })
                    .join("\n");
                return summary || `${nodeName} found ${results.length} research sources.`;
            } catch {
                return `${nodeName} found ${results.length} research sources.`;
            }
        }
    }

    // Check for research summary (condensed text)
    if ("research_summary" in payloadObj && typeof payloadObj.research_summary === "string") {
        const summary = payloadObj.research_summary.trim();
        if (summary) {
            return summary;
        }
    }

    // Check for blog plan
    if ("blog_plan" in payloadObj && payloadObj.blog_plan && typeof payloadObj.blog_plan === "object") {
        const plan = payloadObj.blog_plan as Record<string, unknown>;
        if (Object.keys(plan).length > 0) {
            try {
                return JSON.stringify(plan, null, 2);
            } catch {
                return `${nodeName} created blog plan.`;
            }
        }
    }

    // Check for tasks output
    if ("tasks_output" in payloadObj && payloadObj.tasks_output && typeof payloadObj.tasks_output === "object") {
        const tasksOutput = payloadObj.tasks_output as Record<string, unknown>;
        const taskCount = Object.keys(tasksOutput).length;
        if (taskCount > 0) {
            return `${nodeName} completed ${taskCount} writing tasks.`;
        }
    }

    // Check for draft or final_post
    if ("draft" in payloadObj && typeof payloadObj.draft === "string") {
        const draft = payloadObj.draft.trim();
        if (draft) {
            return draft;
        }
    }

    if ("final_post" in payloadObj && typeof payloadObj.final_post === "string") {
        const finalPost = payloadObj.final_post.trim();
        if (finalPost) {
            return finalPost;
        }
    }

    // Check for messages with actual content
    const messages = payloadObj.messages;
    if (Array.isArray(messages) && messages.length > 0) {
        for (let i = messages.length - 1; i >= 0; i--) {
            const msg = messages[i] as Record<string, unknown>;
            const content = msg?.content;
            if (content && typeof content === "string" && content.trim()) {
                const text = content.trim();
                return text;
            }
        }
    }

    // Fallback: show what fields were updated
    const updateFields = Object.keys(payloadObj).filter((k) => !["messages"].includes(k));
    if (updateFields.length > 0) {
        return `${nodeName} updated: ${updateFields.join(", ")}`;
    }

    return `${nodeName} completed.`;
}