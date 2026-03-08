"""
Test Step 10 — Full crew pipeline + DB persistence.

Creates a session + profile in the DB, runs the full 4-agent pipeline
synchronously, then queries the DB to verify nodes and resources were saved.

Usage:
    cd backend
    python scripts/test_crew_full.py
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import init_db, SessionLocal
from app.db.models import Session, Profile, Roadmap, SkillNode, Resource
from app.schemas.roadmap import GenerateRoadmapRequest
from app.services.crew_service import run_pipeline, _persist_roadmap

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "fixture_0.json")


def main():
    init_db()
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        # Create session + profile
        session = Session(name="test-crew-full")
        db.add(session)
        db.flush()

        profile = Profile(
            session_id=session.id,
            resume_text=data["resume_text"],
            github_summaries=data["github_summaries"],
            job_title=data["job_title"],
        )
        db.add(profile)
        db.flush()

        roadmap_row = Roadmap(session_id=session.id, profile_id=profile.id)
        db.add(roadmap_row)
        db.commit()
        db.refresh(roadmap_row)
        roadmap_id = roadmap_row.id
        print(f"Created roadmap row id={roadmap_id}")

        # Run pipeline
        request = GenerateRoadmapRequest(
            session_id=session.id,
            resume_text=data["resume_text"],
            github_summaries=data["github_summaries"],
            job_title=data["job_title"],
        )
        print("Running 4-agent pipeline...")
        generated = run_pipeline(request)
        print(f"Pipeline complete — {len(generated.nodes)} nodes generated")

        # Persist
        _persist_roadmap(db, roadmap_id, generated)

        # Verify
        nodes = db.query(SkillNode).filter(SkillNode.roadmap_id == roadmap_id).all()
        resources = db.query(Resource).join(SkillNode).filter(SkillNode.roadmap_id == roadmap_id).all()
        parents = [n for n in nodes if n.parent_id is not None]

        print(f"\nDB skill_nodes : {len(nodes)}")
        print(f"DB resources   : {len(resources)}")
        print(f"Nodes w/ parent: {len(parents)}")

        assert len(nodes) > 0, "No skill_nodes inserted!"
        assert len(resources) > 0, "No resources inserted!"

        # Check positions vary
        xs = {n.position_x for n in nodes}
        ys = {n.position_y for n in nodes}
        assert len(xs) > 1 or len(ys) > 1, "All nodes at same position — layout failed!"

        print("\nSample node:")
        n = nodes[0]
        print(f"  skill_name  : {n.skill_name}")
        print(f"  mastery     : {n.mastery_level}")
        print(f"  position    : ({n.position_x}, {n.position_y})")
        print(f"  parent_id   : {n.parent_id}")

        print("\nAll assertions passed. PASSED")
    finally:
        db.close()


if __name__ == "__main__":
    main()
