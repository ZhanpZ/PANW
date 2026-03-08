import { create } from "zustand";
import { sessionApi } from "../api/client";
import type { Session } from "../types";

interface SessionStore {
  sessions: Session[];
  activeSessionId: number | null;
  loading: boolean;

  loadSessions: () => Promise<void>;
  createSession: (name: string) => Promise<Session>;
  deleteSession: (id: number) => Promise<void>;
  setActiveSessionId: (id: number | null) => void;
}

export const useSessionStore = create<SessionStore>((set, _get) => ({
  sessions: [],
  activeSessionId: null,
  loading: false,

  loadSessions: async () => {
    set({ loading: true });
    try {
      const res = await sessionApi.list();
      set({ sessions: res.data });
    } finally {
      set({ loading: false });
    }
  },

  createSession: async (name: string) => {
    const res = await sessionApi.create(name);
    const newSession = res.data;
    set((state) => ({
      sessions: [newSession, ...state.sessions],
      activeSessionId: newSession.id,
    }));
    return newSession;
  },

  deleteSession: async (id: number) => {
    await sessionApi.delete(id);
    set((state) => {
      const sessions = state.sessions.filter((s) => s.id !== id);
      const activeSessionId =
        state.activeSessionId === id
          ? (sessions[0]?.id ?? null)
          : state.activeSessionId;
      return { sessions, activeSessionId };
    });
  },

  setActiveSessionId: (id) => set({ activeSessionId: id }),
}));
