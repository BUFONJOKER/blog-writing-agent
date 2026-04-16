import React from "react";

type AuthPageShellProps = {
    title: string;
    description: string;
    children: React.ReactNode;
    footer: React.ReactNode;
};

export function AuthPageShell({ title, description, children, footer }: AuthPageShellProps) {
    return (
        <main className="flex min-h-screen items-center justify-center bg-black px-4 py-10 text-white">
            <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 shadow-2xl">
                <h1 className="text-2xl font-bold tracking-tight text-blue-400">{title}</h1>
                <p className="mt-1 text-sm text-zinc-400">{description}</p>

                {children}

                {footer}
            </div>
        </main>
    );
}
