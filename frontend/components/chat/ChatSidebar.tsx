import Link from "next/link";
import { ThreadItem } from "@/components/chat/types";

type ChatSidebarProps = {
    drawerOpen: boolean;
    isLoggedIn: boolean;
    isCreatingChat: boolean;
    threadsLoading: boolean;
    threads: ThreadItem[];
    activeThreadId: string | null;
    userEmail: string | null;
    onClose: () => void;
    onQuickNewChat: () => void;
    onSelectThread: (threadId: string) => void;
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
    onClose,
    onQuickNewChat,
    onSelectThread,
    onLogout,
}: ChatSidebarProps) {
    return (
        <aside
            className={`fixed left-0 top-0 z-40 flex h-screen w-80 flex-col border-r border-zinc-800 bg-zinc-950/95 p-4 shadow-2xl backdrop-blur transition-transform duration-200 ${drawerOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-zinc-400">Chats</h2>
                <button
                    type="button"
                    onClick={onClose}
                    className="rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 transition hover:border-zinc-500"
                >
                    Close
                </button>
            </div>

            <button
                type="button"
                onClick={onQuickNewChat}
                disabled={!isLoggedIn || isCreatingChat}
                className="mb-4 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-zinc-700"
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
                    <button
                        key={thread.threadId}
                        type="button"
                        onClick={() => onSelectThread(thread.threadId)}
                        className={`mb-2 w-full rounded-lg border px-3 py-2 text-left transition ${
                            activeThreadId === thread.threadId
                                ? "border-blue-500 bg-blue-500/10"
                                : "border-zinc-800 bg-zinc-900 hover:border-zinc-700"
                        }`}
                    >
                        <p className="truncate text-xs font-semibold text-zinc-200">{thread.prompt || thread.preview || "Blog post"}</p>
                        <p className="mt-1 truncate text-xs text-zinc-500">{thread.preview}</p>
                    </button>
                ))}
            </div>

            <div className="mt-4 rounded-xl border border-zinc-800 bg-zinc-900/70 p-3">
                {isLoggedIn && userEmail ? (
                    <>
                        <p className="text-xs uppercase tracking-wide text-zinc-500">Profile</p>
                        <p className="mt-1 truncate text-sm font-medium text-zinc-200">{userEmail}</p>
                        <button
                            type="button"
                            onClick={onLogout}
                            className="mt-3 w-full rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200 transition hover:border-zinc-500"
                        >
                            Logout
                        </button>
                    </>
                ) : (
                    <div className="space-y-2">
                        <Link
                            href="/login"
                            className="block w-full rounded-lg border border-zinc-700 px-3 py-2 text-center text-sm text-zinc-200 transition hover:border-zinc-500"
                        >
                            Login
                        </Link>
                        <Link
                            href="/signup"
                            className="block w-full rounded-lg bg-blue-600 px-3 py-2 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
                        >
                            Signup
                        </Link>
                    </div>
                )}
            </div>
        </aside>
    );
}
