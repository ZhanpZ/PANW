"""
Agent 3 — GapAnalyzerAgent
Input : ParsedProfile, JobRequirements
Output: GapAnalysis  (each skill is DONE or LACK — strictly binary)
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import GapAnalysis, JobRequirements, ParsedProfile, SkillGap
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback
# ──────────────────────────────────────────────────────────────────────────────

def _fallback_gap_analyzer(profile: ParsedProfile, job_reqs: JobRequirements) -> GapAnalysis:
    """Conservative fallback: mark known skills DONE, everything else LACK."""
    known = {s.lower() for s in profile.skills}
    skill_gaps = []
    for req in job_reqs.required_skills:
        if req.skill_name.lower() in known:
            mastery = "DONE"
            reasoning = "Skill found in candidate profile (rule-based match)."
        else:
            mastery = "LACK"
            reasoning = "AI unavailable — skill not detected in profile text (rule-based fallback)."
        skill_gaps.append(SkillGap(
            skill_name=req.skill_name,
            category=req.category,
            mastery_level=mastery,  # type: ignore[arg-type]
            reasoning=reasoning,
            importance=req.importance,
        ))
    return GapAnalysis(
        profile_summary="AI analysis unavailable. Gap assessment performed by keyword matching.",
        skill_gaps=skill_gaps,
    )

SCHEMA_HINT = json.dumps(
    {
        "profile_summary": "2–3 sentence summary of the candidate's current strengths and gaps.",
        "skill_gaps": [
            {
                "skill_name": "AWS",
                "category": "Cloud Platforms",
                "mastery_level": "LACK",
                "reasoning": "No AWS-related keywords, projects, or certifications found in either the resume or GitHub repositories.",
                "importance": "required",
            },
            {
                "skill_name": "Python",
                "category": "Programming Languages",
                "mastery_level": "DONE",
                "reasoning": "Used Python in two work projects (resume) and primary language in 6 GitHub repositories.",
                "importance": "required",
            },
        ],
    },
    indent=2,
)


def _validate_and_repair_gap(gap: GapAnalysis, job_reqs: JobRequirements) -> GapAnalysis:
    """
    Guarantee correctness of GapAnalysis:
    1. Reject any skill with invalid mastery_level.
    2. Ensure every job-requirement skill is classified — add missing ones as LACK.
    3. Deduplicate by skill_name (first occurrence wins).
    """
    valid_gaps: list[SkillGap] = []
    for sg in gap.skill_gaps:
        if sg.mastery_level not in ("DONE", "LACK"):
            # Coerce invalid mastery to LACK (conservative)
            sg = SkillGap(
                skill_name=sg.skill_name,
                category=sg.category,
                mastery_level="LACK",
                reasoning=f"Invalid mastery_level {sg.mastery_level!r} coerced to LACK.",
                importance=sg.importance,
            )
        valid_gaps.append(sg)

    # Deduplicate by skill_name (case-insensitive, first occurrence wins)
    seen: set[str] = set()
    deduped: list[SkillGap] = []
    for sg in valid_gaps:
        key = sg.skill_name.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(sg)

    # Ensure every job-requirement skill has a classification
    classified_names = {sg.skill_name.lower() for sg in deduped}
    for req in job_reqs.required_skills:
        if req.skill_name.lower() not in classified_names:
            deduped.append(SkillGap(
                skill_name=req.skill_name,
                category=req.category,
                mastery_level="LACK",
                reasoning="Not classified by AI analysis; defaulting to LACK (coverage repair).",
                importance=req.importance,
            ))

    return GapAnalysis(profile_summary=gap.profile_summary, skill_gaps=deduped)


def run_gap_analyzer(profile: ParsedProfile, job_reqs: JobRequirements) -> GapAnalysis:
    llm = get_llm()

    agent = Agent(
        role="Career Gap Analyst",
        goal=(
            "Compare a candidate's profile against job requirements and classify "
            "each required skill as exactly DONE or LACK."
        ),
        backstory=(
            "You are a technical career coach who objectively assesses skill gaps from "
            "both traditional resumes and GitHub activity. You treat GitHub project history "
            "as equally valid evidence of skill mastery. DONE means the candidate clearly "
            "demonstrates the skill in either their resume or GitHub; LACK means it is absent "
            "from both sources."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    profile_json = profile.model_dump_json(indent=2)
    reqs_json = job_reqs.model_dump_json(indent=2)

    skill_list = "\n".join(
        f"  - {req.skill_name} ({req.category})"
        for req in job_reqs.required_skills
    )

    task = Task(
        description=f"""
You are given:
1. A parsed candidate profile derived from their RESUME and GITHUB activity (JSON)
2. A list of job requirements (JSON)

The candidate profile below was built from two sources:
  - Their written resume (work experience, education, certifications, listed skills)
  - Their GitHub summary (repositories, languages used, project descriptions, contributions)

Candidate Profile (from resume + GitHub):
{profile_json}

Job Requirements:
{reqs_json}

You MUST classify EVERY skill listed below — no exceptions:
{skill_list}

For each skill assign exactly one of:
  - "DONE"  — the candidate clearly demonstrates this skill in their resume OR GitHub activity.
              Evidence includes: listed as a skill, used in work experience, appears in GitHub repos/projects.
              A skill marked DONE is NOT a gap — they already have it.
  - "LACK"  — the skill is absent or not sufficiently evidenced in either the resume or GitHub.

IMPORTANT:
- Evidence from GitHub projects counts equally to resume experience — do not ignore it.
- Classify ALL {len(job_reqs.required_skills)} skills — do not skip any.
- Use ONLY "DONE" or "LACK" — no other values ("MAYBE", "PARTIAL", etc. are INVALID).
- "DONE" means the gap is closed — they have this skill. "LACK" means it is a real gap to address.
- Base your classification ONLY on the candidate profile provided (resume + GitHub evidence).

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}
""",
        expected_output=(
            "A JSON object with profile_summary (str) and skill_gaps (list where each "
            "item has skill_name, category, mastery_level (DONE|LACK), reasoning, importance). "
            f"The skill_gaps list must contain exactly {len(job_reqs.required_skills)} entries."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    try:
        result = crew.kickoff()
        raw = result.raw if hasattr(result, "raw") else str(result)
        gap = GapAnalysis.model_validate_json(extract_json(raw))
        return _validate_and_repair_gap(gap, job_reqs)
    except Exception as exc:
        print(f"[FALLBACK] gap_analyzer: AI failed ({exc!r}), using keyword-match fallback")
        return _fallback_gap_analyzer(profile, job_reqs)
