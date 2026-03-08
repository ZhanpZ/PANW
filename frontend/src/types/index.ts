export type MasteryLevel = "DONE" | "LACK";
export type ResourceType = "free" | "paid";
export type JobStatus = "pending" | "processing" | "complete" | "failed";

export interface Resource {
  id: number;
  title: string;
  url: string | null;
  resource_type: ResourceType;
  platform: string | null;
}

export interface SkillNode {
  id: number;
  skill_name: string;
  mastery_level: MasteryLevel;
  category: string | null;
  description: string | null;
  estimated_hours: number | null;
  position_x: number;
  position_y: number;
  parent_id: number | null;
  reasoning: string | null;
  resources: Resource[];
}

export interface Roadmap {
  id: number;
  session_id: number;
  profile_id: number;
  status: JobStatus;
  error_message: string | null;
  created_at: string;
  skill_nodes: SkillNode[];
}

export interface Session {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateRoadmapRequest {
  session_id: number;
  resume_text: string;
  github_summaries: string;
  job_title: string;
}

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}
