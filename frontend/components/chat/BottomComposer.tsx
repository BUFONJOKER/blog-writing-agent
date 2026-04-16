import React from "react";

type BottomComposerProps = {
    prompt: string;
    isCreatingChat: boolean;
    disabled?: boolean;
    disabledHint?: string;
    onPromptChange: (value: string) => void;
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function BottomComposer({
    prompt,
    isCreatingChat,
    disabled = false,
    disabledHint = "This chat is closed. Click New Chat to start another prompt.",
    onPromptChange,
    onSubmit,
}: BottomComposerProps) {
    const isDisabled = disabled || isCreatingChat;

    const handleTextareaKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (event.key !== "Enter" || event.shiftKey) {
            return;
        }

        event.preventDefault();

        if (isDisabled || !prompt.trim()) {
            return;
        }

        event.currentTarget.form?.requestSubmit();
    };

    return (
        <div className="fixed bottom-4 left-1/2 z-20 w-[calc(100%-2rem)] max-w-4xl -translate-x-1/2 md:bottom-8 md:w-[calc(100%-4rem)]">
            <form
                onSubmit={onSubmit}
                className="flex items-end gap-3 rounded-2xl border border-zinc-700 bg-zinc-900/90 p-3 shadow-2xl backdrop-blur transition focus-within:border-blue-500"
            >
                <textarea
                    value={prompt}
                    rows={1}
                    disabled={isDisabled}
                    onChange={(e) => onPromptChange(e.target.value)}
                    onKeyDown={handleTextareaKeyDown}
                    placeholder={isDisabled ? disabledHint : "Type your prompt to create a new chat..."}
                    className="min-h-12 w-full resize-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-zinc-600 disabled:opacity-50"
                />
                <button
                    type="submit"
                    disabled={!prompt.trim() || isDisabled}
                    className="h-11 shrink-0 rounded-xl bg-blue-600 px-5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:bg-zinc-700"
                >
                    {isCreatingChat ? "Creating..." : "Send"}
                </button>
            </form>
        </div>
    );
}
