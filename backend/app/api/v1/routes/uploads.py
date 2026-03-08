import logging
import os
import uuid

_log = logging.getLogger(__name__)

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.db.models import ProofUpload, SkillNode
from app.schemas.roadmap import ProofUploadOut

router = APIRouter()


@router.post("/uploads/{node_id}", response_model=ProofUploadOut, status_code=201)
async def upload_proof(
    node_id: int,
    file: UploadFile = File(...),
    notes: str = Form(default=""),
    db: Session = Depends(get_db),
):
    node = db.query(SkillNode).filter(SkillNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Skill node not found")

    # Size check
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # Save file with unique name
    ext = os.path.splitext(file.filename or "upload")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(settings.UPLOAD_DIR, str(node_id))
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, unique_name)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(contents)

    record = ProofUpload(
        skill_node_id=node_id,
        filename=file.filename,
        filepath=filepath,
        notes=notes or None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/uploads/{node_id}", response_model=list[ProofUploadOut])
def list_uploads(node_id: int, db: Session = Depends(get_db)):
    node = db.query(SkillNode).filter(SkillNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Skill node not found")
    return db.query(ProofUpload).filter(ProofUpload.skill_node_id == node_id).all()


@router.delete("/uploads/{upload_id}", status_code=204)
def delete_upload(upload_id: int, db: Session = Depends(get_db)):
    record = db.query(ProofUpload).filter(ProofUpload.id == upload_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Remove file from disk if it exists
    if record.filepath and os.path.exists(record.filepath):
        try:
            os.remove(record.filepath)
        except OSError as exc:
            _log.warning("Could not delete file %s: %s", record.filepath, exc)
            raise HTTPException(
                status_code=500,
                detail=f"File removal failed: {exc}",
            )

    db.delete(record)
    db.commit()
