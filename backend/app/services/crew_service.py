"""
Crew service — JSON utility, 4-agent pipeline orchestration,
background task, and DB persistence.
"""

import concurrent.futures
import json
import re

from app.schemas.agent_contracts import GeneratedRoadmap, RoadmapNode
from app.schemas.roadmap import GenerateRoadmapRequest


# ──────────────────────────────────────────────────────────────────────────────
# JSON extraction utility
# ──────────────────────────────────────────────────────────────────────────────

def extract_json(raw_output: object) -> str:
    """Strip markdown code fences and extract the first valid JSON object/array."""
    text = str(raw_output).strip()

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass  # Fall through to regex extraction

    obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if obj_match:
        candidate = obj_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass  # Fall through to raw text

    print(f"[extract_json] WARNING: could not extract valid JSON; returning raw text ({len(text)} chars)")
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Full 4-agent pipeline
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(request: GenerateRoadmapRequest) -> GeneratedRoadmap:
    from app.agents.resume_parser import run_resume_parser
    from app.agents.job_requirements import run_job_requirements
    from app.agents.gap_analyzer import run_gap_analyzer
    from app.agents.roadmap_generator import run_roadmap_generator

    # Agent 1 (resume) and Agent 2 (job requirements) are independent — run in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_profile  = executor.submit(run_resume_parser, request.resume_text, request.github_summaries)
        future_job_reqs = executor.submit(run_job_requirements, request.job_title)
        profile  = future_profile.result()
        job_reqs = future_job_reqs.result()

    gap     = run_gap_analyzer(profile, job_reqs)
    roadmap = run_roadmap_generator(gap, request.job_title)
    return roadmap


# ──────────────────────────────────────────────────────────────────────────────
# DB persistence
# ──────────────────────────────────────────────────────────────────────────────

def _compute_category_grid(nodes: list[RoadmapNode]) -> dict[str, tuple[float, float]]:
    """Category-column grid layout: each category is a column, nodes stack vertically."""
    from collections import defaultdict

    NODE_W = 220
    NODE_H = 80
    H_GAP = 80
    V_GAP = 40

    by_category: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        by_category[node.category or "General"].append(node.skill_name)

    positions: dict[str, tuple[float, float]] = {}
    num_cols = len(by_category)
    total_width = num_cols * NODE_W + (num_cols - 1) * H_GAP
    start_x = -total_width / 2

    for col_idx, (category, names) in enumerate(sorted(by_category.items())):
        x = start_x + col_idx * (NODE_W + H_GAP)
        for row_idx, name in enumerate(names):
            y = row_idx * (NODE_H + V_GAP)
            positions[name] = (x, y)

    return positions


def _compute_positions(nodes: list[RoadmapNode]) -> dict[str, tuple[float, float]]:
    """Topological BFS layout: levels on Y-axis, siblings spread on X-axis."""
    from collections import defaultdict, deque

    NODE_W = 220
    NODE_H = 80
    H_GAP = 60
    V_GAP = 120

    skill_names = {n.skill_name for n in nodes}
    children_map: dict[str, list[str]] = defaultdict(list)

    for node in nodes:
        if node.parent_skill and node.parent_skill in skill_names:
            children_map[node.parent_skill].append(node.skill_name)

    roots = [n.skill_name for n in nodes
             if not n.parent_skill or n.parent_skill not in skill_names]

    level_map: dict[str, int] = {}
    queue: deque[str] = deque()
    for root in roots:
        level_map[root] = 0
        queue.append(root)

    while queue:
        name = queue.popleft()
        for child in children_map.get(name, []):
            if child not in level_map:
                level_map[child] = level_map[name] + 1
                queue.append(child)

    # Disconnected / cyclic nodes go to the last row
    max_level = max(level_map.values(), default=0)
    for node in nodes:
        if node.skill_name not in level_map:
            level_map[node.skill_name] = max_level + 1

    by_level: dict[int, list[str]] = defaultdict(list)
    for name, lvl in level_map.items():
        by_level[lvl].append(name)
    for lvl in by_level:
        by_level[lvl].sort()

    # Fall back to category grid when >50% of nodes land at the same level (flat layout)
    level0_count = len(by_level.get(0, []))
    if nodes and level0_count > len(nodes) * 0.5:
        return _compute_category_grid(nodes)

    positions: dict[str, tuple[float, float]] = {}
    for lvl, names in sorted(by_level.items()):
        count = len(names)
        total_width = count * NODE_W + (count - 1) * H_GAP
        start_x = -total_width / 2
        for i, name in enumerate(names):
            x = start_x + i * (NODE_W + H_GAP)
            y = lvl * (NODE_H + V_GAP)
            positions[name] = (x, y)

    return positions


def _persist_roadmap(db, roadmap_id: int, generated: GeneratedRoadmap) -> None:
    from app.db.models import Resource, SkillNode

    positions = _compute_positions(generated.nodes)

    # First pass: insert all nodes without parent_id
    skill_name_to_id: dict[str, int] = {}
    db_node_pairs: list[tuple[RoadmapNode, SkillNode]] = []

    for node in generated.nodes:
        pos = positions.get(node.skill_name, (0.0, 0.0))
        db_node = SkillNode(
            roadmap_id=roadmap_id,
            skill_name=node.skill_name,
            mastery_level=node.mastery_level,
            category=node.category,
            description=node.description,
            estimated_hours=node.estimated_hours,
            position_x=pos[0],
            position_y=pos[1],
            parent_id=None,
            reasoning=node.reasoning,
        )
        db.add(db_node)
        db.flush()
        skill_name_to_id[node.skill_name] = db_node.id
        db_node_pairs.append((node, db_node))

    # Second pass: resolve parent_id
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
