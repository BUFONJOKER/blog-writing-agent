import Link from "next/link";

export function AuthRequiredCard() {
    return (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-8 text-center">
            <h2 className="text-xl font-semibold text-zinc-100">Authentication required</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm text-zinc-400">
                Login or create an account to access your chat window, thread list, and new chat creation.
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                <Link href="/login" className="rounded-xl border border-zinc-700 px-5 py-2.5 text-sm text-zinc-100 transition hover:border-zinc-500">
                    Go to Login
                </Link>
                <Link href="/signup" className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500">
                    Go to Signup
                </Link>
            </div>
        </div>
    );
}
