from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.session import SessionCreate, SessionOut
from app.services.session_service import create_session, delete_session, get_all_sessions

router = APIRouter()


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return get_all_sessions(db)


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_new_session(body: SessionCreate, db: Session = Depends(get_db)):
    return create_session(db, body.name)


@router.delete("/sessions/{session_id}", status_code=204)
def remove_session(session_id: int, db: Session = Depends(get_db)):
    deleted = delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
