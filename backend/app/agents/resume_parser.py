"""
Agent 1 — ResumeParserAgent
Input : resume_text (str), github_summaries (str)
Output: ParsedProfile
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import ParsedProfile
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

SCHEMA_HINT = json.dumps(
    {
        "skills": ["Python", "SQL", "..."],
        "experience_years": 2.5,
        "education": ["B.S. Computer Science — State University, 2023"],
        "projects": ["Movie recommender built with scikit-learn and Flask"],
        "certifications": [],
    },
    indent=2,
)


def run_resume_parser(resume_text: str, github_summaries: str) -> ParsedProfile:
    llm = get_llm()

    agent = Agent(
        role="Technical Resume Parser",
        goal=(
            "Extract a structured profile of skills, experience, education, projects, "
            "and certifications from a candidate's resume and GitHub project summaries."
        ),
        backstory=(
            "You are a senior technical recruiter with 10+ years of experience reading "
            "software engineering resumes. You excel at identifying explicit and implied "
            "technical skills from unstructured text."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
Analyze the resume text and GitHub summaries below.
Extract ALL technical skills mentioned or clearly implied, years of total professional/
internship experience, education entries, notable project descriptions (1 sentence each),
and any certifications.

Resume:
\"\"\"
{resume_text}
\"\"\"

GitHub Summaries:
\"\"\"
{github_summaries if github_summaries.strip() else "None provided"}
\"\"\"

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}

Rules:
- skills: flat list of strings, each a distinct technology/concept (e.g. "Python", "REST APIs", "Docker")
- experience_years: total years of paid/internship work experience as a float
- certifications: empty list [] if none found
""",
        expected_output=(
            "A single JSON object with keys: skills (list), experience_years (float), "
            "education (list), projects (list), certifications (list)."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)
    return ParsedProfile.model_validate_json(extract_json(raw))
