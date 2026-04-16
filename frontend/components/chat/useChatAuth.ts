"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { logoutUser } from "@/lib/api";
import type { OllamaSetupNotice } from "@/lib/api";

type UseChatAuthOptions = {
    onClear?: () => void;
};

const REQUIRED_OLLAMA_STEPS = [
    "curl -fsSL https://ollama.com/install.sh | sh",
    "winget install --id Ollama.Ollama -e",
    "ollama signin",
    "ollama pull qwen3.5:cloud",
    "ollama run qwen3.5:cloud",
];

function normalizeOllamaSetupNotice(notice: OllamaSetupNotice): OllamaSetupNotice {
    const existingSteps = Array.isArray(notice.steps)
        ? notice.steps.filter((step): step is string => typeof step === "string" && step.trim().length > 0)
        : [];
    const mergedSteps = [...existingSteps];

    for (const requiredStep of REQUIRED_OLLAMA_STEPS) {
        if (!mergedSteps.includes(requiredStep)) {
            mergedSteps.push(requiredStep);
        }
    }

    return {
        ...notice,
        steps: mergedSteps,
    };
}

export function useChatAuth(options: UseChatAuthOptions = {}) {
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [authReady, setAuthReady] = useState(false);
    const [userEmail, setUserEmail] = useState<string | null>(null);
    const [userName, setUserName] = useState<string | null>(null);
    const [ollamaSetupNotice, setOllamaSetupNotice] = useState<OllamaSetupNotice | null>(null);

    useEffect(() => {
        if (typeof window === "undefined") return;
        const storedEmail = localStorage.getItem("auth_user_email");
        const storedName = localStorage.getItem("auth_user_name");
        if (storedEmail) {
            setUserEmail(storedEmail);
        }
        if (storedName) {
            setUserName(storedName);
        }
        const rawNotice = localStorage.getItem("auth_ollama_setup_notice");
        if (rawNotice) {
            try {
                const parsed = JSON.parse(rawNotice) as OllamaSetupNotice;
                if (
                    parsed &&
                    typeof parsed.title === "string" &&
                    typeof parsed.description === "string" &&
                    Array.isArray(parsed.steps)
                ) {
                    const normalizedNotice = normalizeOllamaSetupNotice(parsed);
                    setOllamaSetupNotice(normalizedNotice);
                    localStorage.setItem("auth_ollama_setup_notice", JSON.stringify(normalizedNotice));
                }
            } catch (error: unknown) {
                console.warn("Invalid Ollama setup notice in storage", error);
                localStorage.removeItem("auth_ollama_setup_notice");
            }
        }
        setAuthReady(true);
    }, []);

    const isLoggedIn = useMemo(() => Boolean(userEmail), [userEmail]);

    const clearAuth = useCallback(() => {
        setUserEmail(null);
        setUserName(null);
        setOllamaSetupNotice(null);

        if (typeof window !== "undefined") {
            localStorage.removeItem("auth_user_email");
            localStorage.removeItem("auth_user_name");
            localStorage.removeItem("auth_ollama_setup_notice");
        }

        options.onClear?.();
    }, [options.onClear]);

    const handleLogout = useCallback(async () => {
        try {
            await logoutUser();
        } catch (error: unknown) {
            console.error("Logout failed", error);
        } finally {
            clearAuth();
            setDrawerOpen(false);
        }
    }, [clearAuth]);

    const dismissOllamaSetupNotice = useCallback(() => {
        setOllamaSetupNotice(null);
        if (typeof window !== "undefined") {
            localStorage.removeItem("auth_ollama_setup_notice");
        }
    }, []);

    return {
        drawerOpen,
        setDrawerOpen,
        authReady,
        userEmail,
        userName,
        setUserEmail,
        setUserName,
        ollamaSetupNotice,
        dismissOllamaSetupNotice,
        isLoggedIn,
        clearAuth,
        handleLogout,
    };
}