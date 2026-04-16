import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL;

const api = axios.create({
    baseURL,
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor to include JWT token
api.interceptors.request.use(
    (config) => {
        if (typeof window !== "undefined") {
            const token = localStorage.getItem("token");
            if (token && config.headers) {
                config.headers.Authorization = `Bearer ${token}`;
            }
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
    (response: any) => response,
    (error: any) => {
        if (error.response && error.response.status === 401) {
            // Handle unauthorized access, e.g., redirect to login page
            console.error("Unauthorized access - redirecting to login");
        }

        return Promise.reject(error);
    }
);

export default api;

export type UserPost = {
    thread_id: string;
    user_id: string;
    prompt: string;
    final_post_markdown: string;
    meta?: Record<string, unknown>;
    created_at?: string;
};

export type GenerateResponse = {
    user_id: string;
    thread_id: string;
    status: string;
    stream_url: string;
};

export type FinalPostResponse = {
    thread_id: string;
    final_post_markdown: string;
    meta?: Record<string, unknown>;
};

export type BlogStatusResponse = {
    status: string;
    is_waiting_for_you: boolean;
    error: string | null;
};

export type ReviewResponse = {
    message: string;
};

export async function loginUser(payload: { email: string; password: string }) {
    return api.post<{ message: string; email: string }>("/auth/login", payload);
}

export async function signupUser(payload: { name: string; email: string; password: string }) {
    return api.post<{ message: string }>("/auth/register", payload);
}

export async function logoutUser() {
    return api.post<{ message: string }>("/auth/logout");
}

export async function fetchUserThreads(userId: string) {
    return api.get<UserPost[]>(`/blog/user_posts/${encodeURIComponent(userId)}`);
}

export async function createChatThread(payload: { user_id: string; prompt: string }) {
    return api.post<GenerateResponse>("/blog/generate", payload);
}

export async function fetchFinalPost(payload: { user_id: string; thread_id: string }) {
    return api.post<FinalPostResponse>("/blog/final_post", payload);
}

export async function fetchBlogStatus(threadId: string) {
    return api.get<BlogStatusResponse>(`/blog/status/${encodeURIComponent(threadId)}`);
}

export async function submitBlogReview(payload: { thread_id: string; approved: boolean }) {
    return api.post<ReviewResponse>("/blog/review", payload);
}