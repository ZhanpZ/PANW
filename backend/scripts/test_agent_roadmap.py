"""
Test Step 9 — Roadmap Generator Agent.

Usage:
    cd backend
    python scripts/test_agent_roadmap.py
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.resume_parser import run_resume_parser
from app.agents.job_requirements import run_job_requirements
from app.agents.gap_analyzer import run_gap_analyzer
from app.agents.roadmap_generator import run_roadmap_generator

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "fixture_0.json")

def main():
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    print("1/4 — Parsing resume...")
    profile = run_resume_parser(data["resume_text"], data["github_summaries"])

    print("2/4 — Fetching job requirements...")
    reqs = run_job_requirements(data["job_title"])

    print("3/4 — Analyzing gaps...")
    gap = run_gap_analyzer(profile, reqs)

    print("4/4 — Generating roadmap...")
    roadmap = run_roadmap_generator(gap, data["job_title"])

    print(roadmap.model_dump_json(indent=2))

    skill_names = {n.skill_name for n in roadmap.nodes}

    for node in roadmap.nodes:
        assert node.mastery_level in ("DONE", "LACK"), \
            f"Invalid mastery_level: {node.mastery_level}"

        free_res  = [r for r in node.resources if r.resource_type == "free"]
        paid_res  = [r for r in node.resources if r.resource_type == "paid"]
        assert free_res,  f"Node '{node.skill_name}' has no free resources"
        assert paid_res,  f"Node '{node.skill_name}' has no paid resources"

        if node.parent_skill:
            assert node.parent_skill in skill_names, \
                f"parent_skill '{node.parent_skill}' not in node list"

    print(f"\nNodes: {len(roadmap.nodes)}")
    print("All assertions passed. PASSED")

if __name__ == "__main__":
    main()
