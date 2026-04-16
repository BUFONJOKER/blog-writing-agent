"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";
import { LoginView } from "@/components/auth/LoginView";
import { loginUser } from "@/lib/api";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!email.trim() || !password.trim() || isSubmitting) return;

        setIsSubmitting(true);
        setErrorMessage("");

        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Request timeout - is the backend running?")), 10000)
        );

        try {
            console.log("🔐 Attempting login with email:", email.trim());
            const response = await Promise.race([
                loginUser({ email: email.trim(), password }),
                timeoutPromise
            ]) as any;
            console.log("✅ Login successful:", response.data);
            localStorage.setItem("auth_user_email", response.data.email);
            router.push("/");
            router.refresh();
        } catch (error: unknown) {
            console.error("❌ Login failed:", error);
            const axiosError = (error as any)?.response;
            const errorMsg =
                (error as Error)?.message === "Request timeout - is the backend running?"
                    ? "Login timeout - is the backend running? Check that the API server is accessible."
                    : axiosError?.data?.detail ||
                      (error as Error)?.message ||
                      "Login failed. Please check your email and password.";
            setErrorMessage(errorMsg);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <LoginView
            email={email}
            password={password}
            showPassword={showPassword}
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onToggleShowPassword={() => setShowPassword((prev) => !prev)}
            onSubmit={handleSubmit}
        />
    );
}
