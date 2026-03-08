"""
Internal Pydantic shapes passed between CrewAI agents.
These are NOT exposed via the API — they are the data contracts
for the 4-agent pipeline.
"""

from typing import Literal

from pydantic import BaseModel, field_validator


# ──────────────────────────────────────────────────────────────────────────────
# Agent 1 output: ResumeParserAgent → ParsedProfile
# ──────────────────────────────────────────────────────────────────────────────

class ParsedProfile(BaseModel):
    skills: list[str]
    experience_years: float
    education: list[str]
    projects: list[str]
    certifications: list[str]


# ──────────────────────────────────────────────────────────────────────────────
# Agent 2 output: JobRequirementsAgent → JobRequirements
# ──────────────────────────────────────────────────────────────────────────────

class SkillRequirement(BaseModel):
    skill_name: str
    category: str
    importance: Literal["required", "preferred"]
    description: str


class JobRequirements(BaseModel):
    job_title: str
    required_skills: list[SkillRequirement]


# ──────────────────────────────────────────────────────────────────────────────
# Agent 3 output: GapAnalyzerAgent → GapAnalysis
# ──────────────────────────────────────────────────────────────────────────────

class SkillGap(BaseModel):
    skill_name: str
    category: str
    mastery_level: Literal["DONE", "LACK"]
    reasoning: str
    importance: Literal["required", "preferred"]

    @field_validator("mastery_level")
    @classmethod
    def must_be_binary(cls, v: str) -> str:
        if v not in ("DONE", "LACK"):
            raise ValueError(f"mastery_level must be DONE or LACK, got: {v!r}")
        return v


class GapAnalysis(BaseModel):
    profile_summary: str
    skill_gaps: list[SkillGap]


# ──────────────────────────────────────────────────────────────────────────────
# Agent 4 output: RoadmapGeneratorAgent → GeneratedRoadmap
# ──────────────────────────────────────────────────────────────────────────────

class ResourceSpec(BaseModel):
    title: str
    url: str
    resource_type: Literal["free", "paid"]
    platform: str


class RoadmapNode(BaseModel):
    skill_name: str
    category: str
    mastery_level: Literal["DONE", "LACK"]
    reasoning: str
    description: str
    estimated_hours: int
    parent_skill: str | None  # None = top-level node; must reference another skill_name in the list
    resources: list[ResourceSpec]

    @field_validator("mastery_level")
    @classmethod
    def must_be_binary(cls, v: str) -> str:
        if v not in ("DONE", "LACK"):
            raise ValueError(f"mastery_level must be DONE or LACK, got: {v!r}")
        return v


class GeneratedRoadmap(BaseModel):
    nodes: list[RoadmapNode]
