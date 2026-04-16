import Link from "next/link";
import React from "react";
import { AuthPageShell } from "@/components/auth/AuthPageShell";
import { PasswordField } from "@/components/auth/PasswordField";
import { TextField } from "@/components/auth/TextField";

type UpdatePasswordViewProps = {
    email: string;
    currentPassword: string;
    newPassword: string;
    showCurrentPassword: boolean;
    showNewPassword: boolean;
    isSubmitting: boolean;
    errorMessage: string;
    successMessage: string;
    onEmailChange: (value: string) => void;
    onCurrentPasswordChange: (value: string) => void;
    onNewPasswordChange: (value: string) => void;
    onToggleCurrentPassword: () => void;
    onToggleNewPassword: () => void;
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
};

export function UpdatePasswordView({
    email,
    currentPassword,
    newPassword,
    showCurrentPassword,
    showNewPassword,
    isSubmitting,
    errorMessage,
    successMessage,
    onEmailChange,
    onCurrentPasswordChange,
    onNewPasswordChange,
    onToggleCurrentPassword,
    onToggleNewPassword,
    onSubmit,
}: UpdatePasswordViewProps) {
    return (
        <AuthPageShell
            title="Update Password"
            description="Change the password for your account."
            footer={
                <p className="mt-5 text-sm text-zinc-400">
                    <Link href="/" className="font-medium text-blue-400 hover:text-blue-300">
                        Back to chats
                    </Link>
                </p>
            }
        >
            <form onSubmit={onSubmit} className="mt-6 space-y-4">
                <div>
                    <TextField
                        label="Email"
                        type="email"
                        value={email}
                        placeholder="you@example.com"
                        onChange={onEmailChange}
                    />
                    <p className="mt-1 text-xs text-zinc-500">Use the email associated with your signed-in session.</p>
                </div>

                <PasswordField
                    label="Current password"
                    value={currentPassword}
                    placeholder="••••••••"
                    showPassword={showCurrentPassword}
                    onChange={onCurrentPasswordChange}
                    onToggleShowPassword={onToggleCurrentPassword}
                    autoComplete="current-password"
                />

                <PasswordField
                    label="New password"
                    value={newPassword}
                    placeholder="Choose a new password"
                    showPassword={showNewPassword}
                    onChange={onNewPasswordChange}
                    onToggleShowPassword={onToggleNewPassword}
                    autoComplete="new-password"
                />

                {errorMessage && <p className="text-sm text-rose-400">{errorMessage}</p>}
                {successMessage && <p className="text-sm text-emerald-400">{successMessage}</p>}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:bg-zinc-700"
                >
                    {isSubmitting ? "Updating..." : "Update password"}
                </button>
            </form>
        </AuthPageShell>
    );
}