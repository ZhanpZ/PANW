from sqlalchemy.orm import Session as DBSession

from app.db.models import Session


def get_all_sessions(db: DBSession) -> list[Session]:
    return db.query(Session).order_by(Session.updated_at.desc()).all()


def create_session(db: DBSession, name: str) -> Session:
    session = Session(name=name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: DBSession, session_id: int) -> bool:
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True
