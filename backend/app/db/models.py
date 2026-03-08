import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import backref, relationship

from app.db.database import Base


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class MasteryLevel(str, enum.Enum):
    DONE = "DONE"
    LACK = "LACK"


class RoadmapStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    complete = "complete"
    failed = "failed"


class ResourceType(str, enum.Enum):
    free = "free"
    paid = "paid"


# ──────────────────────────────────────────────────────────────────────────────
# Session
# ──────────────────────────────────────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profiles = relationship("Profile", back_populates="session", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="session", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────────────────────────────────────

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    resume_text = Column(Text, nullable=True)
    github_summaries = Column(Text, nullable=True)
    job_title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="profiles")
    roadmaps = relationship("Roadmap", back_populates="profile")


# ──────────────────────────────────────────────────────────────────────────────
# Roadmap
# ──────────────────────────────────────────────────────────────────────────────

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    status = Column(Enum(RoadmapStatus), default=RoadmapStatus.pending, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="roadmaps")
    profile = relationship("Profile", back_populates="roadmaps")
    skill_nodes = relationship("SkillNode", back_populates="roadmap", cascade="all, delete-orphan")

    @property
    def job_title(self) -> str | None:
        return self.profile.job_title if self.profile else None


# ──────────────────────────────────────────────────────────────────────────────
# SkillNode (self-referential DAG via parent_id)
# ──────────────────────────────────────────────────────────────────────────────

class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id"), nullable=False)
    skill_name = Column(String, nullable=False)
    mastery_level = Column(Enum(MasteryLevel), nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    estimated_hours = Column(Integer, nullable=True)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    parent_id = Column(Integer, ForeignKey("skill_nodes.id"), nullable=True)
    reasoning = Column(Text, nullable=True)

    roadmap = relationship("Roadmap", back_populates="skill_nodes")
    children = relationship(
        "SkillNode",
        backref=backref("parent", remote_side="SkillNode.id"),
    )
    resources = relationship("Resource", back_populates="skill_node", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# Resource
# ──────────────────────────────────────────────────────────────────────────────

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    skill_node_id = Column(Integer, ForeignKey("skill_nodes.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    resource_type = Column(Enum(ResourceType), nullable=False)
    platform = Column(String, nullable=True)

    skill_node = relationship("SkillNode", back_populates="resources")

