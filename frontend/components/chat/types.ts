export type ThreadItem = {
    threadId: string;
    preview: string;
    prompt?: string;
    createdAt?: string;
    status: "ready" | "queued" | "running" | "waiting_approval" | "completed" | "failed";
};

export type WorkflowNodeEntry = {
    nodeName: string;
    output: string;
    updatedAt: string;
    status: "pending" | "running" | "completed";
};
