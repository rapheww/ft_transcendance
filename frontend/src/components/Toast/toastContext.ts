// Small toast system: show a short message in a corner for a few seconds.
// Usage in any component:   const toast = useToast();   toast.success("Saved");
import { createContext, useContext } from "react";

export type ToastKind = "success" | "error";

export interface ToastApi {
  success: (message: string) => void;
  error: (message: string) => void;
}

// Default: does nothing (if a component is used outside the ToastProvider, nothing breaks).
export const ToastContext = createContext<ToastApi>({
  success: () => {},
  error: () => {},
});

export function useToast(): ToastApi {
  return useContext(ToastContext);
}
