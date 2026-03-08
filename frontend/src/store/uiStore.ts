import { create } from "zustand";
import type { Toast } from "../types";

interface UiStore {
  selectedNodeId: number | null;
  isPanelOpen: boolean;
  toasts: Toast[];

  setSelectedNodeId: (id: number | null) => void;
  setIsPanelOpen: (open: boolean) => void;
  addToast: (message: string, type?: Toast["type"]) => void;
  removeToast: (id: string) => void;
}

export const useUiStore = create<UiStore>((set) => ({
  selectedNodeId: null,
  isPanelOpen: false,
  toasts: [],

  setSelectedNodeId: (id) =>
    set({ selectedNodeId: id, isPanelOpen: id !== null }),

  setIsPanelOpen: (open) =>
    set((state) => ({
      isPanelOpen: open,
      selectedNodeId: open ? state.selectedNodeId : null,
    })),

  addToast: (message, type = "info") => {
    const id = Math.random().toString(36).slice(2);
    set((state) => ({ toasts: [...state.toasts, { id, message, type }] }));
    // Auto-dismiss after 4s
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },

  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
