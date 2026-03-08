"""
Test Step 7 — Job Requirements Agent.

Usage:
    cd backend
    python scripts/test_agent_job.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.job_requirements import run_job_requirements

JOB_TITLE = "Cloud Engineer"

def main():
    print(f"Fetching requirements for: {JOB_TITLE}\n")
    reqs = run_job_requirements(JOB_TITLE)

    print(reqs.model_dump_json(indent=2))
    n = len(reqs.required_skills)
    print(f"\nTotal skills: {n}")
    assert n >= 15, f"Expected >= 15 skills, got {n}"

    bad = [s for s in reqs.required_skills if s.importance not in ("required", "preferred")]
    assert not bad, f"Invalid importance values: {bad}"

    print("PASSED")

if __name__ == "__main__":
    main()
