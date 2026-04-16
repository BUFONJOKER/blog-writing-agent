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
    startTime?: number; // Timestamp when node started
    endTime?: number; // Timestamp when node completed
    duration?: number; // Duration in seconds
};
