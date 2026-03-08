"""
Test Step 8 — Gap Analyzer Agent.

Usage:
    cd backend
    python scripts/test_agent_gap.py
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.resume_parser import run_resume_parser
from app.agents.job_requirements import run_job_requirements
from app.agents.gap_analyzer import run_gap_analyzer

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "fixture_0.json")

def main():
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    print("Step 1/3 — Parsing resume...")
    profile = run_resume_parser(data["resume_text"], data["github_summaries"])

    print("Step 2/3 — Fetching job requirements...")
    reqs = run_job_requirements(data["job_title"])

    print("Step 3/3 — Analyzing gaps...")
    gap = run_gap_analyzer(profile, reqs)

    print(gap.model_dump_json(indent=2))

    levels = [sg.mastery_level for sg in gap.skill_gaps]
    invalid = [l for l in levels if l not in ("DONE", "LACK")]
    assert not invalid, f"Invalid mastery levels found: {invalid}"

    done  = levels.count("DONE")
    lack  = levels.count("LACK")
    print(f"\nDONE: {done}  LACK: {lack}  (CS grad → Cloud Eng should be mostly LACK)")
    print("PASSED")

if __name__ == "__main__":
    main()
