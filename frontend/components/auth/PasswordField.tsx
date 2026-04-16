import React from "react";

type PasswordFieldProps = {
    label: string;
    value: string;
    placeholder: string;
    showPassword: boolean;
    onChange: (value: string) => void;
    onToggleShowPassword: () => void;
};

function EyeIcon() {
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
            <circle cx="12" cy="12" r="3" />
        </svg>
    );
}

function EyeOffIcon() {
    return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19C5 19 1 12 1 12a21.76 21.76 0 0 1 5.06-6.94" />
            <path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 8 11 8a21.8 21.8 0 0 1-3.1 4.28" />
            <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
            <path d="M1 1l22 22" />
        </svg>
    );
}

export function PasswordField({
    label,
    value,
    placeholder,
    showPassword,
    onChange,
    onToggleShowPassword,
}: PasswordFieldProps) {
    return (
        <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-400">{label}</span>
            <div className="relative">
                <input
                    type={showPassword ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 pr-16 text-sm outline-none transition focus:border-blue-500"
                    placeholder={placeholder}
                    required
                />
                <button
                    type="button"
                    onClick={onToggleShowPassword}
                    className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-2 text-zinc-400 transition hover:bg-zinc-800 hover:text-zinc-200"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
            </div>
        </label>
    );
}