import axios from "axios";
import type {
  GenerateRoadmapRequest,
  JobStatus,
  MasteryLevel,
  Roadmap,
  Session,
} from "../types";

const api = axios.create({
  baseURL: "/",  // Vite proxy forwards /api/* to localhost:8000
  timeout: 15000,
});

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionApi = {
  list: () => api.get<Session[]>("/api/v1/sessions"),
  create: (name: string) =>
    api.post<Session>("/api/v1/sessions", { name }),
  delete: (id: number) => api.delete(`/api/v1/sessions/${id}`),
};

// ── Roadmap ───────────────────────────────────────────────────────────────────

export const roadmapApi = {
  generate: (payload: GenerateRoadmapRequest) =>
    api.post<{ job_id: number; status: JobStatus }>(
      "/api/v1/roadmap/generate",
      payload
    ),
  pollJob: (jobId: number) =>
    api.get<{ job_id: number; status: JobStatus; error_message: string | null }>(
      `/api/v1/roadmap/job/${jobId}`
    ),
  get: (roadmapId: number) => api.get<Roadmap>(`/api/v1/roadmap/${roadmapId}`),
  updateNodeMastery: (nodeId: number, mastery_level: MasteryLevel) =>
    api.patch(`/api/v1/roadmap/node/${nodeId}`, { mastery_level }),
};

// ── Global error interceptor ──────────────────────────────────────────────────

api.interceptors.response.use(
  (res) => res,
  (error) => {
    // Re-throw so individual callers can handle; stores add toasts on catch
    return Promise.reject(error);
  }
);

export default api;
