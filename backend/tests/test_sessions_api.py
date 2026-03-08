"""
Tests for /api/v1/sessions endpoints.
Scope: happy path + edge cases + standardized route coverage.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, get_db

# ── In-memory SQLite engine for tests ────────────────────────────────────────
# StaticPool forces all sessions to share one connection so the in-memory DB
# is visible across requests (default pool would create isolated connections).
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def fresh_db():
    """Drop and recreate all tables for a clean slate."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ── Happy path ────────────────────────────────────────────────────────────────

def test_create_session_happy_path():
    """POST /sessions with a valid name returns 201 and the session object."""
    fresh_db()
    response = client.post("/api/v1/sessions", json={"name": "My Test Session"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Test Session"
    assert "id" in data
    assert "created_at" in data


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_create_session_empty_name_returns_422():
    """POST /sessions with an empty name must return 422 (validation error)."""
    response = client.post("/api/v1/sessions", json={"name": ""})
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("name" in str(e) for e in errors)


def test_create_session_whitespace_only_name_returns_422():
    """POST /sessions with whitespace-only name collapses to empty → 422."""
    response = client.post("/api/v1/sessions", json={"name": "   "})
    assert response.status_code == 422


def test_create_session_name_too_long_returns_422():
    """POST /sessions with name > 100 chars returns 422."""
    response = client.post("/api/v1/sessions", json={"name": "x" * 101})
    assert response.status_code == 422


# ── Standardized route coverage ───────────────────────────────────────────────

def test_list_sessions_empty():
    """GET /sessions on a fresh DB returns an empty list."""
    fresh_db()
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    assert response.json() == []


def test_list_sessions_returns_created_sessions():
    """GET /sessions returns all sessions that were created."""
    fresh_db()
    client.post("/api/v1/sessions", json={"name": "Session A"})
    client.post("/api/v1/sessions", json={"name": "Session B"})
    response = client.get("/api/v1/sessions")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert "Session A" in names
    assert "Session B" in names


def test_delete_session_happy_path():
    """DELETE /sessions/{id} for an existing session returns 204."""
    fresh_db()
    create_resp = client.post("/api/v1/sessions", json={"name": "To Delete"})
    session_id = create_resp.json()["id"]
    delete_resp = client.delete(f"/api/v1/sessions/{session_id}")
    assert delete_resp.status_code == 204


def test_delete_session_not_found_returns_404():
    """DELETE /sessions/{id} for a nonexistent session returns 404."""
    response = client.delete("/api/v1/sessions/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_health_check():
    """GET /health returns status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
