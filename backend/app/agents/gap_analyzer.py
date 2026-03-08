"""
Agent 3 — GapAnalyzerAgent
Input : ParsedProfile, JobRequirements
Output: GapAnalysis  (each skill is DONE or LACK — strictly binary)
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import GapAnalysis, JobRequirements, ParsedProfile
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

SCHEMA_HINT = json.dumps(
    {
        "profile_summary": "2–3 sentence summary of the candidate's current strengths and gaps.",
        "skill_gaps": [
            {
                "skill_name": "AWS",
                "category": "Cloud Platforms",
                "mastery_level": "LACK",
                "reasoning": "No AWS-related keywords, projects, or certifications found in the resume.",
                "importance": "required",
            },
            {
                "skill_name": "Python",
                "category": "Programming Languages",
                "mastery_level": "DONE",
                "reasoning": "Used Python in two projects and listed as primary language.",
                "importance": "required",
            },
        ],
    },
    indent=2,
)


def run_gap_analyzer(profile: ParsedProfile, job_reqs: JobRequirements) -> GapAnalysis:
    llm = get_llm()

    agent = Agent(
        role="Career Gap Analyst",
        goal=(
            "Compare a candidate's profile against job requirements and classify "
            "each required skill as exactly DONE or LACK."
        ),
        backstory=(
            "You are a technical career coach who objectively assesses skill gaps. "
            "You are direct and evidence-based: DONE means the candidate clearly "
            "demonstrates the skill; LACK means it is absent or insufficiently evidenced."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    profile_json = profile.model_dump_json(indent=2)
    reqs_json = job_reqs.model_dump_json(indent=2)

    task = Task(
        description=f"""
You are given:
1. A parsed candidate profile (JSON)
2. A list of job requirements (JSON)

Candidate Profile:
{profile_json}

Job Requirements:
{reqs_json}

For EVERY skill in the job requirements list, assign exactly one of:
  - "DONE"  — the candidate clearly demonstrates this skill in their resume/projects
  - "LACK"  — the skill is absent or not sufficiently evidenced

IMPORTANT:
- You MUST classify every single skill — do not skip any
- Use ONLY "DONE" or "LACK" — no other values ("MAYBE", "PARTIAL", etc. are INVALID)
- Base your classification only on evidence in the candidate profile

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}
""",
        expected_output=(
            "A JSON object with profile_summary (str) and skill_gaps (list where each "
            "item has skill_name, category, mastery_level (DONE|LACK), reasoning, importance)."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)
    gap = GapAnalysis.model_validate_json(extract_json(raw))

    # Hard-assert: no invalid mastery values slipped through
    for sg in gap.skill_gaps:
        if sg.mastery_level not in ("DONE", "LACK"):
            raise ValueError(
                f"Invalid mastery_level {sg.mastery_level!r} for skill {sg.skill_name!r}. "
                "Only DONE and LACK are permitted."
            )

    return gap
