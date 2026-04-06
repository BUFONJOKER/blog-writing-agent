"use client";

import React, { useState, useRef, useEffect } from "react";
// Remove FormEvent and KeyboardEvent from the curly braces

// Types for our UI-only messages
type Message = {
    id: string;
    role: "user" | "agent";
    content: string;
};

export default function PromptPage() {
    const [prompt, setPrompt] = useState("");
    const [isLoading, setIsLoading] = useState(false); // Track loading state
    const [messages, setMessages] = useState<Message[]>([
        { id: "1", role: "agent", content: "Hello! I'm your Blog Writing Agent. What topic should we explore today?" }
    ]);

    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to the bottom when messages update
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = async (event: React.SyntheticEvent<HTMLFormElement>) => {
        event.preventDefault();
        const trimmedPrompt = prompt.trim();
        if (!trimmedPrompt || isLoading) return;

        setIsLoading(true); // Start loading

        // 1. Add User Message to UI
        const userMsg: Message = { id: Date.now().toString(), role: "user", content: trimmedPrompt };
        setMessages((prev) => [...prev, userMsg]);
        setPrompt("");

        try {
            // 2. Simulate API call delay (replace with your actual fetch logic later)
            await new Promise((resolve) => setTimeout(resolve, 1500));

            const agentMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: "agent",
                content: `That sounds like a great topic! I'll start researching "${trimmedPrompt}" once we connect the backend.`
            };
            setMessages((prev) => [...prev, agentMsg]);
        } catch (error) {
            console.error("Failed to fetch response", error);
        } finally {
            setIsLoading(false); // Stop loading regardless of success/fail
        }
    };

    const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            event.currentTarget.form?.requestSubmit();
        }
    };

    return (
        <main className="flex h-screen flex-col bg-black text-white">
            {/* 1. Header */}
            <header className="border-b border-zinc-800 p-4 text-center">
                <h1 className="text-xl font-bold tracking-tight">Blog Agent Chat</h1>
            </header>

            {/* 2. Messages Area (Scrollable) */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto px-4 py-8 scrollbar-hide"
            >
                <div className="mx-auto flex max-w-3xl flex-col gap-6">
                    {messages.map((m) => (
                        <div
                            key={m.id}
                            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 shadow-sm ${
                                m.role === "user"
                                ? "bg-blue-600 text-white rounded-tr-none"
                                : "bg-zinc-900 border border-zinc-800 text-zinc-200 rounded-tl-none"
                            }`}>
                                <p className="font-bold text-[10px] uppercase tracking-widest opacity-50 mb-1">
                                    {m.role}
                                </p>
                                {m.content}
                            </div>
                        </div>
                    ))}
                    {/* Visual indicator for typing */}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-zinc-900 border border-zinc-800 text-zinc-400 rounded-2xl rounded-tl-none px-4 py-3 text-xs italic animate-pulse">
                                Agent is thinking...
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 3. Input Area (Fixed at Bottom) */}
            <div className="border-t border-zinc-800 bg-black p-4 pb-8">
                <div className="mx-auto max-w-3xl">
                    <form onSubmit={handleSubmit} className="rounded-2xl border border-zinc-700 bg-zinc-900/90 p-2 shadow-2xl focus-within:border-zinc-500 transition-colors">
                        <div className="flex items-end gap-2">
                            <textarea
                                value={prompt}
                                rows={1}
                                disabled={isLoading}
                                placeholder={isLoading ? "Agent is processing..." : "Message Blog Agent..."}
                                onChange={(e) => setPrompt(e.target.value)}
                                onKeyDown={handleKeyDown}
                                className="max-h-32 w-full resize-none bg-transparent px-3 py-3 text-sm outline-none placeholder:text-zinc-500 disabled:opacity-50"
                            />
                            <button
                                type="submit"
                                disabled={!prompt.trim() || isLoading}
                                className="mb-1 flex h-10 w-10 items-center justify-center rounded-xl bg-white text-black transition hover:bg-zinc-200 disabled:bg-zinc-800 disabled:text-zinc-600"
                            >
                                {isLoading ? (
                                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-600 border-t-zinc-200" />
                                ) : (
                                    "↑"
                                )}
                            </button>
                        </div>
                    </form>
                    <p className="mt-2 text-center text-[10px] text-zinc-500">
                        Agent may produce inaccurate info. Verify your blog drafts.
                    </p>
                </div>
            </div>
        </main>
    );
}