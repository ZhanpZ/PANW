from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Profile, Roadmap, RoadmapStatus, SkillNode
from app.schemas.roadmap import (
    GenerateRoadmapRequest,
    JobStatusResponse,
    RoadmapOut,
    UpdateNodeMasteryRequest,
)
from app.services.crew_service import generate_roadmap_background

router = APIRouter()


@router.post("/roadmap/generate", response_model=JobStatusResponse)
def generate_roadmap(
    body: GenerateRoadmapRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    from app.db.models import Session as SessionModel
    session = db.query(SessionModel).filter(SessionModel.id == body.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    profile = Profile(
        session_id=body.session_id,
        resume_text=body.resume_text,
        github_summaries=body.github_summaries,
        job_title=body.job_title,
    )
    db.add(profile)
    db.flush()

    roadmap = Roadmap(
        session_id=body.session_id,
        profile_id=profile.id,
        status=RoadmapStatus.pending,
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)

    background_tasks.add_task(generate_roadmap_background, roadmap.id, body)

    return JobStatusResponse(job_id=roadmap.id, status=roadmap.status.value)


@router.get("/roadmap/job/{job_id}", response_model=JobStatusResponse)
def poll_job(job_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(Roadmap).filter(Roadmap.id == job_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=roadmap.id,
        status=roadmap.status.value,
        error_message=roadmap.error_message,
    )


@router.get("/roadmap/session/{session_id}", response_model=RoadmapOut)
def get_roadmap_by_session(session_id: int, db: Session = Depends(get_db)):
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.session_id == session_id, Roadmap.status == RoadmapStatus.complete)
        .order_by(Roadmap.created_at.desc())
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="No completed roadmap for this session")
    return roadmap


@router.get("/roadmap/{roadmap_id}", response_model=RoadmapOut)
def get_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    if roadmap.status != RoadmapStatus.complete:
        raise HTTPException(
            status_code=409,
            detail=f"Roadmap is not complete yet (status: {roadmap.status.value})",
        )
    return roadmap


@router.patch("/roadmap/node/{node_id}", response_model=dict)
def update_node_mastery(
    node_id: int,
    body: UpdateNodeMasteryRequest,
    db: Session = Depends(get_db),
):
    node = db.query(SkillNode).filter(SkillNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Skill node not found")
    node.mastery_level = body.mastery_level
    db.commit()
    return {"id": node.id, "mastery_level": node.mastery_level.value}
