import React from "react";

type TextFieldProps = {
    label: string;
    type?: string;
    value: string;
    placeholder: string;
    onChange: (value: string) => void;
};

export function TextField({ label, type = "text", value, placeholder, onChange }: TextFieldProps) {
    return (
        <label className="block">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-400">{label}</span>
            <input
                type={type}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500"
                placeholder={placeholder}
                required
            />
        </label>
    );
}
