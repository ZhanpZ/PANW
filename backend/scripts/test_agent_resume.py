"""
Test Step 6 — Resume Parser Agent.

Usage:
    cd backend
    python scripts/test_agent_resume.py
"""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.agents.resume_parser import run_resume_parser

FIXTURE = os.path.join(os.path.dirname(__file__), "..", "fixtures", "fixture_0.json")

def main():
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Parsing fixture: {FIXTURE}")
    print(f"Job title: {data['job_title']}\n")

    profile = run_resume_parser(data["resume_text"], data["github_summaries"])

    print("ParsedProfile:")
    print(profile.model_dump_json(indent=2))
    assert len(profile.skills) > 0, "No skills extracted!"
    print(f"\nExtracted {len(profile.skills)} skills. PASSED")

if __name__ == "__main__":
    main()
