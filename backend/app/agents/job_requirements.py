"""
Agent 2 — JobRequirementsAgent
Input : job_title (str)
Output: JobRequirements
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import JobRequirements
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

SCHEMA_HINT = json.dumps(
    {
        "job_title": "Cloud Engineer",
        "required_skills": [
            {
                "skill_name": "AWS",
                "category": "Cloud Platforms",
                "importance": "required",
                "description": "Ability to provision and manage core AWS services (EC2, S3, IAM, VPC).",
            },
            {
                "skill_name": "Terraform",
                "category": "Infrastructure as Code",
                "importance": "required",
                "description": "Write and manage Terraform modules for repeatable infrastructure.",
            },
        ],
    },
    indent=2,
)


def run_job_requirements(job_title: str) -> JobRequirements:
    llm = get_llm()

    agent = Agent(
        role="Job Market Analyst",
        goal=(
            f"Produce a comprehensive, accurate list of technical skills required "
            f"for a {job_title} role based on industry knowledge."
        ),
        backstory=(
            "You are a technical hiring manager who has reviewed thousands of job "
            "descriptions. You know exactly what skills are expected for each engineering "
            "role at modern tech companies."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
Based on your knowledge of the current job market, list all technical skills
typically required or strongly preferred for a **{job_title}** role.

Aim for 15–25 skills covering multiple categories (e.g. Cloud Platforms,
Networking, Security, CI/CD, Programming Languages, Databases, Monitoring, etc.).

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}

Rules:
- importance must be exactly "required" or "preferred" — no other values
- category groups related skills (each skill belongs to exactly one category)
- description: 1–2 sentences explaining what proficiency looks like in practice
- Produce at least 15 skills total
""",
        expected_output=(
            "A JSON object with job_title (str) and required_skills (list of objects "
            "with skill_name, category, importance, description)."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)
    return JobRequirements.model_validate_json(extract_json(raw))
