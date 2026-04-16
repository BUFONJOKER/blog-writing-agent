import Link from "next/link";
import React from "react";
import { AuthPageShell } from "@/components/auth/AuthPageShell";
import { PasswordField } from "@/components/auth/PasswordField";
import { TextField } from "@/components/auth/TextField";

type SignupViewProps = {
    name: string;
    email: string;
    password: string;
    showPassword: boolean;
    isSubmitting: boolean;
    errorMessage: string;
    onNameChange: (value: string) => void;
    onEmailChange: (value: string) => void;
    onPasswordChange: (value: string) => void;
    onToggleShowPassword: () => void;
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function SignupView({
    name,
    email,
    password,
    showPassword,
    isSubmitting,
    errorMessage,
    onNameChange,
    onEmailChange,
    onPasswordChange,
    onToggleShowPassword,
    onSubmit,
}: SignupViewProps) {
    return (
        <AuthPageShell
            title="Create Account"
            description="Sign up to start managing your chats."
            footer={
                <p className="mt-5 text-sm text-zinc-400">
                    Already have an account? <Link href="/login" className="font-medium text-blue-400 hover:text-blue-300">Login</Link>
                </p>
            }
        >
            <form onSubmit={onSubmit} className="mt-6 space-y-4">
                <TextField
                    label="Name"
                    value={name}
                    placeholder="Your name"
                    onChange={onNameChange}
                />

                <TextField
                    label="Email"
                    type="email"
                    value={email}
                    placeholder="you@example.com"
                    onChange={onEmailChange}
                />

                <PasswordField
                    label="Password"
                    value={password}
                    placeholder="At least 8 characters"
                    showPassword={showPassword}
                    onChange={onPasswordChange}
                    onToggleShowPassword={onToggleShowPassword}
                />

                {errorMessage && <p className="text-sm text-rose-400">{errorMessage}</p>}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:bg-zinc-700"
                >
                    {isSubmitting ? "Creating account..." : "Sign up"}
                </button>
            </form>
        </AuthPageShell>
    );
}
