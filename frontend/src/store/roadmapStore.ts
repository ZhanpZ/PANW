import { create } from "zustand";
import { roadmapApi } from "../api/client";
import type { JobStatus, MasteryLevel, Roadmap } from "../types";

const POLL_INTERVAL_MS = 2000;

interface RoadmapStore {
  roadmap: Roadmap | null;
  jobId: number | null;
  jobStatus: JobStatus | null;
  jobError: string | null;
  isPolling: boolean;

  setJobId: (id: number) => void;
  startPolling: (jobId: number) => void;
  stopPolling: () => void;
  loadRoadmap: (roadmapId: number) => Promise<void>;
  updateNodeMastery: (nodeId: number, level: MasteryLevel) => Promise<void>;
  clearRoadmap: () => void;
}

let _pollTimer: ReturnType<typeof setInterval> | null = null;

export const useRoadmapStore = create<RoadmapStore>((set, get) => ({
  roadmap: null,
  jobId: null,
  jobStatus: null,
  jobError: null,
  isPolling: false,

  setJobId: (id) => set({ jobId: id }),

  startPolling: (jobId: number) => {
    if (_pollTimer) clearInterval(_pollTimer);
    set({ jobId, jobStatus: "pending", isPolling: true, jobError: null });

    _pollTimer = setInterval(async () => {
      try {
        const res = await roadmapApi.pollJob(jobId);
        const { status, error_message } = res.data;
        set({ jobStatus: status });

        if (status === "complete") {
          get().stopPolling();
          await get().loadRoadmap(jobId);
        } else if (status === "failed") {
          get().stopPolling();
          set({ jobError: error_message ?? "Roadmap generation failed." });
        }
      } catch {
        get().stopPolling();
        set({ jobError: "Lost connection to server." });
      }
    }, POLL_INTERVAL_MS);
  },

  stopPolling: () => {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
    set({ isPolling: false });
  },

  loadRoadmap: async (roadmapId: number) => {
    const res = await roadmapApi.get(roadmapId);
    set({ roadmap: res.data });
  },

  updateNodeMastery: async (nodeId: number, level: MasteryLevel) => {
    await roadmapApi.updateNodeMastery(nodeId, level);
    // Optimistic local update
    set((state) => {
      if (!state.roadmap) return {};
      return {
        roadmap: {
          ...state.roadmap,
          skill_nodes: state.roadmap.skill_nodes.map((n) =>
            n.id === nodeId ? { ...n, mastery_level: level } : n
          ),
        },
      };
    });
  },

  clearRoadmap: () => {
    get().stopPolling();
    set({ roadmap: null, jobId: null, jobStatus: null, jobError: null });
  },
}));
