import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ThreadItem } from "@/components/chat/types";

type ChatSidebarProps = {
    drawerOpen: boolean;
    isLoggedIn: boolean;
    isCreatingChat: boolean;
    threadsLoading: boolean;
    threads: ThreadItem[];
    activeThreadId: string | null;
    userEmail: string | null;
    userName: string | null;
    onClose: () => void;
    onQuickNewChat: () => void;
    onSelectThread: (threadId: string) => void;
    onDeleteThread: (threadId: string) => Promise<void>;
    onLogout: () => void;
};

export function ChatSidebar({
    drawerOpen,
    isLoggedIn,
    isCreatingChat,
    threadsLoading,
    threads,
    activeThreadId,
    userEmail,
    userName,
    onClose,
    onQuickNewChat,
    onSelectThread,
    onDeleteThread,
    onLogout,
}: ChatSidebarProps) {
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef<HTMLDivElement | null>(null);

    const displayName = userName?.trim() || "User";

    useEffect(() => {
        if (!isProfileMenuOpen) return;

        const handleClickOutside = (event: MouseEvent) => {
            if (!profileMenuRef.current?.contains(event.target as Node)) {
                setIsProfileMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [isProfileMenuOpen]);

    return (
        <aside
            className={`fixed left-0 top-0 z-40 flex h-screen w-80 flex-col border-r border-zinc-800 bg-zinc-950/95 p-4 shadow-2xl backdrop-blur transition-transform duration-200 ${drawerOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Chats</h2>
                <button
                    type="button"
                    onClick={onClose}
                    className="cursor-pointer rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 transition hover:border-zinc-500"
                >
                    Close
                </button>
            </div>

            <button
                type="button"
                onClick={onQuickNewChat}
                disabled={!isLoggedIn || isCreatingChat}
                className="mb-4 cursor-pointer rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700"
            >
                {isCreatingChat ? "Creating..." : "New Chat"}
            </button>

            <div className="min-h-0 flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/60 p-2">
                {!isLoggedIn && <p className="p-2 text-sm text-zinc-500">Login to view your chats.</p>}
                {isLoggedIn && threadsLoading && <p className="p-2 text-sm text-zinc-500">Loading chats...</p>}
                {isLoggedIn && !threadsLoading && threads.length === 0 && (
                    <p className="p-2 text-sm text-zinc-500">No chats yet. Create your first one.</p>
                )}

                {threads.map((thread) => (
                    <div key={thread.threadId} className="mb-2 flex items-stretch gap-2">
                        <button
                            type="button"
                            onClick={() => onSelectThread(thread.threadId)}
                            className={`min-w-0 flex-1 cursor-pointer rounded-lg border px-3 py-2 text-left transition ${
                                activeThreadId === thread.threadId
                                    ? "border-blue-500 bg-blue-500/10"
                                    : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
                            }`}
                        >
                            <p className="truncate text-xs font-semibold text-zinc-200">{thread.prompt || thread.preview || "Blog post"}</p>
                            <p className="mt-1 truncate text-xs text-zinc-500">{thread.preview}</p>
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                const shouldDelete = window.confirm("Are you sure you want to delete this thread?");
                                if (!shouldDelete) {
                                    return;
                                }
                                void onDeleteThread(thread.threadId);
                            }}
                            className="flex h-auto w-12 shrink-0 cursor-pointer items-center justify-center rounded-lg border border-red-700/50 bg-red-900/20 text-lg leading-none text-red-400 transition hover:border-red-600 hover:bg-red-900/40"
                            title="Delete thread"
                        >
                            🗑️
                        </button>
                    </div>
                ))}
            </div>

            <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
                {isLoggedIn && userEmail ? (
                    <>
                        <p className="text-center text-xs uppercase tracking-wide text-zinc-500">Profile</p>
                        <div ref={profileMenuRef} className="relative mt-2 flex flex-col items-center">
                            <button
                                type="button"
                                onClick={() => setIsProfileMenuOpen((prev) => !prev)}
                                className="max-w-full truncate rounded-full border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-500"
                                aria-label="Open profile menu"
                                title={userEmail}
                            >
                                {displayName}
                            </button>

                            {isProfileMenuOpen && (
                                <div className="absolute bottom-14 right-0 w-44 rounded-xl border border-zinc-700 bg-zinc-900 p-1 shadow-2xl">
                                    <Link
                                        href="/update_password"
                                        onClick={() => setIsProfileMenuOpen(false)}
                                        className="block w-full cursor-pointer rounded-lg px-3 py-2 text-left text-sm text-zinc-200 transition hover:bg-zinc-800"
                                    >
                                        Update password
                                    </Link>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setIsProfileMenuOpen(false);
                                            onLogout();
                                        }}
                                        className="block w-full cursor-pointer rounded-lg px-3 py-2 text-left text-sm text-rose-300 transition hover:bg-zinc-800"
                                    >
                                        Logout
                                    </button>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="space-y-2">
                        <Link
                            href="/login"
                            className="block w-full cursor-pointer rounded-lg border border-zinc-700 px-3 py-2 text-center text-sm text-zinc-200 transition hover:border-zinc-500"
                        >
                            Login
                        </Link>
                        <Link
                            href="/signup"
                            className="block w-full cursor-pointer rounded-lg bg-blue-600 px-3 py-2 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
                        >
                            Signup
                        </Link>
                    </div>
                )}
            </div>
        </aside>
    );
}
