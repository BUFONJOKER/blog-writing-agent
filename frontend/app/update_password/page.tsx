"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { UpdatePasswordView } from "@/components/auth/UpdatePasswordView";
import { logoutUser, updatePassword } from "@/lib/api";
import { getErrorMessage } from "@/lib/error";

export default function UpdatePasswordPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");

    useEffect(() => {
        if (typeof window === "undefined") return;

        const storedEmail = localStorage.getItem("auth_user_email");
        if (storedEmail) {
            setEmail(storedEmail);
        }
    }, []);

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        const trimmedEmail = email.trim();
        if (!trimmedEmail || !currentPassword.trim() || !newPassword.trim() || isSubmitting) {
            return;
        }

        if (newPassword.length < 8) {
            setErrorMessage("New password must be at least 8 characters long.");
            setSuccessMessage("");
            return;
        }

        setIsSubmitting(true);
        setErrorMessage("");
        setSuccessMessage("");

        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Request timeout - is the backend running?")), 10000)
        );

        try {
            await Promise.race([
                updatePassword({
                    email: trimmedEmail,
                    password: currentPassword,
                    new_password: newPassword,
                }),
                timeoutPromise,
            ]);

            try {
                await logoutUser();
            } catch {
                // Ignore logout failures after a successful password update.
            }

            if (typeof window !== "undefined") {
                localStorage.removeItem("auth_user_email");
                localStorage.removeItem("auth_user_name");
            }

            router.replace("/login");
            router.refresh();
        } catch (error: unknown) {
            const errorMsg =
                (error as Error)?.message === "Request timeout - is the backend running?"
                    ? "Password update timeout - is the backend running? Check that the API server is accessible."
                    : getErrorMessage(error, "Password update failed. Please try again.");
            setErrorMessage(errorMsg);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <UpdatePasswordView
            email={email}
            currentPassword={currentPassword}
            newPassword={newPassword}
            showCurrentPassword={showCurrentPassword}
            showNewPassword={showNewPassword}
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
            successMessage={successMessage}
            onEmailChange={setEmail}
            onCurrentPasswordChange={setCurrentPassword}
            onNewPasswordChange={setNewPassword}
            onToggleCurrentPassword={() => setShowCurrentPassword((prev) => !prev)}
            onToggleNewPassword={() => setShowNewPassword((prev) => !prev)}
            onSubmit={handleSubmit}
        />
    );
}