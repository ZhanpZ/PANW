"""
Agent 4 — RoadmapGeneratorAgent
Input : GapAnalysis, job_title (str)
Output: GeneratedRoadmap
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import GapAnalysis, GeneratedRoadmap
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

SCHEMA_HINT = json.dumps(
    {
        "nodes": [
            {
                "skill_name": "Linux Fundamentals",
                "category": "Core Infrastructure",
                "mastery_level": "LACK",
                "reasoning": "No Linux experience found in the profile.",
                "description": "Understanding of Linux filesystem, processes, networking, and shell scripting.",
                "estimated_hours": 20,
                "parent_skill": None,
                "resources": [
                    {
                        "title": "The Linux Command Line (free book)",
                        "url": "https://linuxcommand.org/tlcl.php",
                        "resource_type": "free",
                        "platform": "linuxcommand.org",
                    },
                    {
                        "title": "Linux for Beginners — Udemy",
                        "url": "https://www.udemy.com/course/linux-for-beginners/",
                        "resource_type": "paid",
                        "platform": "Udemy",
                    },
                ],
            },
            {
                "skill_name": "Docker",
                "category": "Containerization",
                "mastery_level": "LACK",
                "reasoning": "Docker not mentioned anywhere in the resume.",
                "description": "Building, running, and managing Docker containers and images.",
                "estimated_hours": 15,
                "parent_skill": "Linux Fundamentals",
                "resources": [
                    {
                        "title": "Docker Official Get Started Guide",
                        "url": "https://docs.docker.com/get-started/",
                        "resource_type": "free",
                        "platform": "Docker Docs",
                    },
                    {
                        "title": "Docker and Kubernetes: The Complete Guide — Udemy",
                        "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
                        "resource_type": "paid",
                        "platform": "Udemy",
                    },
                ],
            },
        ]
    },
    indent=2,
)


def run_roadmap_generator(gap_analysis: GapAnalysis, job_title: str) -> GeneratedRoadmap:
    llm = get_llm()

    agent = Agent(
        role="Learning Roadmap Architect",
        goal=(
            f"Design an ordered, dependency-aware learning roadmap for a candidate "
            f"targeting a {job_title} role, based on their skill gap analysis."
        ),
        backstory=(
            "You are a senior engineering educator who designs curriculum for bootcamps "
            "and online learning platforms. You know the optimal order to learn skills "
            "and the best free and paid resources for each one."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    gap_json = gap_analysis.model_dump_json(indent=2)

    task = Task(
        description=f"""
You are given a skill gap analysis for a candidate targeting a {job_title} role.

Gap Analysis:
{gap_json}

Create a learning roadmap as a list of skill nodes. Include ALL skills from the gap
analysis (both DONE and LACK). For each node:

1. mastery_level: copy exactly from the gap analysis ("DONE" or "LACK" only)
2. parent_skill: the name of the prerequisite skill node (must match another node's
   skill_name exactly), or null if it is a foundational skill
3. resources: provide at least 1 free AND at least 1 paid resource per node.
   Use real, well-known resources:
   - Free: YouTube, freeCodeCamp, official docs, MIT OpenCourseWare, roadmap.sh
   - Paid: Udemy, Coursera, Pluralsight, Linux Foundation, A Cloud Guru
4. estimated_hours: realistic hours to reach job-ready proficiency
5. description: what the skill covers and why it matters for {job_title}

IMPORTANT:
- parent_skill values MUST exactly match a skill_name from another node in the list
- mastery_level must be "DONE" or "LACK" only
- Every node must have >= 1 free resource and >= 1 paid resource

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}
""",
        expected_output=(
            "A JSON object with a 'nodes' array. Each node has: skill_name, category, "
            "mastery_level (DONE|LACK), reasoning, description, estimated_hours (int), "
            "parent_skill (str|null), resources (list with resource_type free|paid)."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)
    roadmap = GeneratedRoadmap.model_validate_json(extract_json(raw))

    # Validate parent_skill references
    skill_names = {n.skill_name for n in roadmap.nodes}
    for node in roadmap.nodes:
        if node.parent_skill and node.parent_skill not in skill_names:
            # Nullify dangling references rather than hard-fail
            node.parent_skill = None

    return roadmap
