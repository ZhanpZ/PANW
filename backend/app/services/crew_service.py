"""
Crew service — JSON utility, 4-agent pipeline orchestration,
node layout algorithm, background task, and DB persistence.
"""

import re
from collections import defaultdict

from app.schemas.agent_contracts import GeneratedRoadmap, RoadmapNode
from app.schemas.roadmap import GenerateRoadmapRequest


# ──────────────────────────────────────────────────────────────────────────────
# JSON extraction utility
# ──────────────────────────────────────────────────────────────────────────────

def extract_json(raw_output: object) -> str:
    """Strip markdown code fences and extract the first JSON object/array."""
    text = str(raw_output).strip()

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        return fence_match.group(1).strip()

    obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if obj_match:
        return obj_match.group(1).strip()

    return text


# ──────────────────────────────────────────────────────────────────────────────
# Node position algorithm
# ──────────────────────────────────────────────────────────────────────────────

COL_WIDTH  = 300   # px between columns
ROW_HEIGHT = 160   # px between rows


def compute_node_positions(nodes: list[RoadmapNode]) -> list[tuple[RoadmapNode, float, float]]:
    """
    Returns list of (node, position_x, position_y).
    Groups by category → columns sorted by LACK count desc.
    Within each column: parent nodes before children.
    """
    categories: dict[str, list[RoadmapNode]] = defaultdict(list)
    for node in nodes:
        categories[node.category].append(node)

    sorted_cats = sorted(
        categories.items(),
        key=lambda kv: sum(1 for n in kv[1] if n.mastery_level == "LACK"),
        reverse=True,
    )

    result: list[tuple[RoadmapNode, float, float]] = []
    for col_idx, (_, cat_nodes) in enumerate(sorted_cats):
        sorted_nodes = _sort_by_dependency(cat_nodes, nodes)
        for row_idx, node in enumerate(sorted_nodes):
            x = float(col_idx * COL_WIDTH)
            y = float(row_idx * ROW_HEIGHT)
            result.append((node, x, y))

    return result


def _sort_by_dependency(
    cat_nodes: list[RoadmapNode], all_nodes: list[RoadmapNode]
) -> list[RoadmapNode]:
    cat_names = {n.skill_name for n in cat_nodes}
    top_level = [n for n in cat_nodes if n.parent_skill not in cat_names]
    children  = [n for n in cat_nodes if n.parent_skill in cat_names]
    return top_level + children


# ──────────────────────────────────────────────────────────────────────────────
# Full 4-agent pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(request: GenerateRoadmapRequest) -> GeneratedRoadmap:
    from app.agents.resume_parser import run_resume_parser
    from app.agents.job_requirements import run_job_requirements
    from app.agents.gap_analyzer import run_gap_analyzer
    from app.agents.roadmap_generator import run_roadmap_generator

    profile  = run_resume_parser(request.resume_text, request.github_summaries)
    job_reqs = run_job_requirements(request.job_title)
    gap      = run_gap_analyzer(profile, job_reqs)
    roadmap  = run_roadmap_generator(gap, request.job_title)
    return roadmap


# ──────────────────────────────────────────────────────────────────────────────
# DB persistence
# ──────────────────────────────────────────────────────────────────────────────

def _persist_roadmap(db, roadmap_id: int, generated: GeneratedRoadmap) -> None:
    from app.db.models import Resource, SkillNode

    positioned = compute_node_positions(generated.nodes)

    # First pass: insert all nodes without parent_id
    skill_name_to_id: dict[str, int] = {}
    db_node_pairs: list[tuple[RoadmapNode, SkillNode]] = []

    for node, x, y in positioned:
        db_node = SkillNode(
            roadmap_id=roadmap_id,
            skill_name=node.skill_name,
            mastery_level=node.mastery_level,
            category=node.category,
            description=node.description,
            estimated_hours=node.estimated_hours,
            position_x=x,
            position_y=y,
            parent_id=None,
            reasoning=node.reasoning,
        )
        db.add(db_node)
        db.flush()
        skill_name_to_id[node.skill_name] = db_node.id
        db_node_pairs.append((node, db_node))

    # Second pass: resolve parent_id FK
    for node, db_node in db_node_pairs:
        if node.parent_skill and node.parent_skill in skill_name_to_id:
            db_node.parent_id = skill_name_to_id[node.parent_skill]

    # Insert resources
    for node, db_node in db_node_pairs:
        for res in node.resources:
            db.add(Resource(
                skill_node_id=db_node.id,
                title=res.title,
                url=res.url,
                resource_type=res.resource_type,
                platform=res.platform,
            ))

    db.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Background task
# ──────────────────────────────────────────────────────────────────────────────

def generate_roadmap_background(roadmap_id: int, request: GenerateRoadmapRequest) -> None:
    from app.db.database import SessionLocal
    from app.db.models import Roadmap, RoadmapStatus

    db = SessionLocal()
    try:
        roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
        roadmap.status = RoadmapStatus.processing
        db.commit()

        generated = run_pipeline(request)
        _persist_roadmap(db, roadmap_id, generated)

        roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
        roadmap.status = RoadmapStatus.complete
        db.commit()

    except Exception as exc:
        db.rollback()
        try:
            roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
            if roadmap:
                from app.db.models import RoadmapStatus as RS
                roadmap.status = RS.failed
                roadmap.error_message = str(exc)[:2000]
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()
