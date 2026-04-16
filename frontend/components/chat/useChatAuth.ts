"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { logoutUser } from "@/lib/api";

type UseChatAuthOptions = {
    onClear?: () => void;
};

export function useChatAuth(options: UseChatAuthOptions = {}) {
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [authReady, setAuthReady] = useState(false);
    const [userEmail, setUserEmail] = useState<string | null>(null);

    useEffect(() => {
        if (typeof window === "undefined") return;
        const storedEmail = localStorage.getItem("auth_user_email");
        if (storedEmail) {
            setUserEmail(storedEmail);
        }
        setAuthReady(true);
    }, []);

    const isLoggedIn = useMemo(() => Boolean(userEmail), [userEmail]);

    const clearAuth = useCallback(() => {
        setUserEmail(null);

        if (typeof window !== "undefined") {
            localStorage.removeItem("auth_user_email");
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

    return {
        drawerOpen,
        setDrawerOpen,
        authReady,
        userEmail,
        setUserEmail,
        isLoggedIn,
        clearAuth,
        handleLogout,
    };
}