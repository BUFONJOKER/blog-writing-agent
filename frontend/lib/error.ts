type ErrorDetail = {
    code?: string;
    message?: string;
};

function extractMessage(detail: unknown): string | null {
    if (typeof detail === "string" && detail.trim()) {
        return detail.trim();
    }

    if (detail && typeof detail === "object") {
        const payload = detail as ErrorDetail;
        if (typeof payload.message === "string" && payload.message.trim()) {
            return payload.message.trim();
        }
    }

    return null;
}

export function getErrorMessage(error: unknown, fallbackMessage: string): string {
    if (error && typeof error === "object" && "response" in error) {
        const response = (error as { response?: { data?: { detail?: unknown; error?: unknown } } }).response;
        const detail = response?.data?.detail ?? response?.data?.error;
        const parsedDetail = extractMessage(detail);
        if (parsedDetail) {
            return parsedDetail;
        }
    }

    if (error instanceof Error && error.message.trim()) {
        return error.message.trim();
    }

    return fallbackMessage;
}