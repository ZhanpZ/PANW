"""
Agent 1 — ResumeParserAgent
Input : resume_text (str), github_summaries (str)
Output: ParsedProfile
"""

import json
import re

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import ParsedProfile
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback
# ──────────────────────────────────────────────────────────────────────────────

_COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    "React", "Vue", "Angular", "Next.js", "Svelte", "HTML", "CSS",
    "Node.js", "Django", "Flask", "FastAPI", "Spring", "Rails", "Express",
    "Docker", "Kubernetes", "Helm", "AWS", "GCP", "Azure", "Terraform", "Ansible",
    "SQL", "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
    "Linux", "Bash", "Git", "CI/CD", "GitHub Actions", "Jenkins", "CircleCI",
    "REST APIs", "GraphQL", "gRPC", "Kafka", "RabbitMQ",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Spark",
    "Prometheus", "Grafana", "DataDog", "Airflow",
]


def _fallback_resume_parser(resume_text: str, github_summaries: str) -> ParsedProfile:
    """Extract skills via keyword matching when LLM is unavailable."""
    combined = (resume_text + " " + (github_summaries or "")).lower()
    found_skills = [s for s in _COMMON_TECH_SKILLS if s.lower() in combined]

    years_match = re.search(r"(\d+(?:\.\d+)?)\s+years?", resume_text, re.IGNORECASE)
    experience_years = float(years_match.group(1)) if years_match else 1.0

    return ParsedProfile(
        skills=found_skills if found_skills else ["Programming"],
        experience_years=experience_years,
        education=[],
        projects=[],
        certifications=[],
    )

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


def _validate_and_repair_profile(profile: ParsedProfile) -> ParsedProfile:
    """Deduplicate skills (case-insensitive) and clamp experience_years to a sane range."""
    seen: set[str] = set()
    deduped: list[str] = []
    for s in profile.skills:
        s = s.strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            deduped.append(s)

    experience_years = max(0.0, min(50.0, profile.experience_years))

    return ParsedProfile(
        skills=deduped if deduped else ["Programming"],
        experience_years=experience_years,
        education=[e.strip() for e in profile.education if e.strip()],
        projects=[p.strip() for p in profile.projects if p.strip()],
        certifications=[c.strip() for c in profile.certifications if c.strip()],
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
    try:
        result = crew.kickoff()
        raw = result.raw if hasattr(result, "raw") else str(result)
        profile = ParsedProfile.model_validate_json(extract_json(raw))
        return _validate_and_repair_profile(profile)
    except Exception as exc:
        print(f"[FALLBACK] resume_parser: AI failed ({exc!r}), using rule-based extraction")
        return _fallback_resume_parser(resume_text, github_summaries)
