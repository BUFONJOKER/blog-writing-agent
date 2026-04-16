"use client";

import { useEffect } from "react";
import { useChatAuth } from "@/components/chat/useChatAuth";
import { useChatRuntime } from "@/components/chat/useChatRuntime";

export function useChatWorkflow() {
    const auth = useChatAuth();
    const runtime = useChatRuntime({
        userEmail: auth.userEmail,
        clearAuth: auth.clearAuth,
        setDrawerOpen: auth.setDrawerOpen,
    });
    const { resetRuntime } = runtime;

    useEffect(() => {
        if (!auth.userEmail) {
            resetRuntime();
        }
    }, [auth.userEmail, resetRuntime]);

    return {
        ...auth,
        ...runtime,
    };
}