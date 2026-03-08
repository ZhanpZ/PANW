from datetime import datetime  # kept for RoadmapOut.created_at
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# API request
# ──────────────────────────────────────────────────────────────────────────────

class GenerateRoadmapRequest(BaseModel):
    session_id: int
    resume_text: str
    github_summaries: str = ""
    job_title: str

    @field_validator("resume_text")
    @classmethod
    def resume_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("resume_text must not be empty")
        return v

    @field_validator("job_title")
    @classmethod
    def job_title_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("job_title must not be empty")
        return v


class UpdateNodeMasteryRequest(BaseModel):
    mastery_level: Literal["DONE", "LACK"]


# ──────────────────────────────────────────────────────────────────────────────
# API responses
# ──────────────────────────────────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    error_message: str | None = None


class ResourceOut(BaseModel):
    id: int
    title: str
    url: str | None
    resource_type: str
    platform: str | None

    model_config = ConfigDict(from_attributes=True)


class SkillNodeOut(BaseModel):
    id: int
    skill_name: str
    mastery_level: Literal["DONE", "LACK"]
    category: str | None
    description: str | None
    estimated_hours: int | None
    position_x: float
    position_y: float
    parent_id: int | None
    reasoning: str | None
    resources: list[ResourceOut]

    model_config = ConfigDict(from_attributes=True)


class RoadmapOut(BaseModel):
    id: int
    session_id: int
    profile_id: int
    status: str
    error_message: str | None
    created_at: datetime
    job_title: str | None
    skill_nodes: list[SkillNodeOut]

    model_config = ConfigDict(from_attributes=True)


class ProofUploadOut(BaseModel):
    id: int
    skill_node_id: int
    filename: str | None
    filepath: str | None
    uploaded_at: datetime
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
