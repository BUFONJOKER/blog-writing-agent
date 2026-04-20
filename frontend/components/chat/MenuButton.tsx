
type MenuButtonProps = {
    onOpen: () => void;
};

export function MenuButton({ onOpen }: MenuButtonProps) {
    return (
        <button
            type="button"
            aria-label="Open menu"
            onClick={onOpen}
            className="fixed left-4 top-4 z-40 rounded-lg border border-zinc-700 bg-zinc-900/90 p-2.5 text-zinc-100 shadow-xl transition hover:border-blue-500"
        >
            <div className="flex h-5 w-5 flex-col justify-between">
                <span className="block h-0.5 w-full bg-current" />
                <span className="block h-0.5 w-full bg-current" />
                <span className="block h-0.5 w-full bg-current" />
            </div>
        </button>
    );
}
