"use client";

import { useRouter } from "next/navigation";
import React, { useState } from "react";
import { SignupView } from "@/components/auth/SignupView";
import { loginUser, signupUser } from "@/lib/api";
import { getErrorMessage } from "@/lib/error";

export default function SignupPage() {
    const router = useRouter();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!name.trim() || !email.trim() || !password.trim() || isSubmitting) return;

        setIsSubmitting(true);
        setErrorMessage("");

        try {
            await signupUser({ name: name.trim(), email: email.trim(), password });
            const loginResponse = await loginUser({ email: email.trim(), password });
            localStorage.setItem("auth_user_email", loginResponse.data.email);
            localStorage.setItem("auth_user_name", loginResponse.data.name || name.trim());
            router.push("/");
            router.refresh();
        } catch (error: unknown) {
            setErrorMessage(getErrorMessage(error, "Signup failed. Please verify your details and try again."));
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <SignupView
            name={name}
            email={email}
            password={password}
            showPassword={showPassword}
            isSubmitting={isSubmitting}
            errorMessage={errorMessage}
            onNameChange={setName}
            onEmailChange={setEmail}
            onPasswordChange={setPassword}
            onToggleShowPassword={() => setShowPassword((prev) => !prev)}
            onSubmit={handleSubmit}
        />
    );
}
