// Shows the toasts. Put it once around the whole app (App.tsx).
import { useCallback, useMemo, useRef, useState, type ReactNode } from "react";
import { CircleAlert, CircleCheck, X } from "lucide-react";
import { ToastContext, type ToastKind } from "./toastContext";

interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
}

const TOAST_MS = 3000; // each toast stays 3 s

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const remove = useCallback((id: number) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (kind: ToastKind, message: string) => {
      const id = nextId.current++;
      setToasts((list) => [...list.slice(-2), { id, kind, message }]); // at most 3 on screen
      window.setTimeout(() => remove(id), TOAST_MS);
    },
    [remove],
  );

  const api = useMemo(
    () => ({
      success: (message: string) => show("success", message),
      error: (message: string) => show("error", message),
    }),
    [show],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      {/* aria-live: screen readers read the message when it appears */}
      <div
        aria-live="polite"
        className="fixed z-50 bottom-4 right-4 left-4 sm:left-auto flex flex-col items-end gap-2 pointer-events-none"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto w-full sm:w-auto sm:max-w-sm flex items-center gap-2 px-4 py-3 rounded-md border bg-black/90 backdrop-blur-xs shadow-xl text-sm text-white ${
              t.kind === "success" ? "border-green-500/50" : "border-red-500/50"
            }`}
          >
            {t.kind === "success" ? (
              <CircleCheck size={18} className="shrink-0 text-green-400" />
            ) : (
              <CircleAlert size={18} className="shrink-0 text-red-400" />
            )}
            <span className="flex-1">{t.message}</span>
            <button
              type="button"
              aria-label="Close"
              onClick={() => remove(t.id)}
              className="shrink-0 opacity-60 hover:opacity-100 cursor-pointer"
            >
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
