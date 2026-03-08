"""
Agent 2 — JobRequirementsAgent
Input : job_title (str)
Output: JobRequirements
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import JobRequirements, SkillRequirement
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback: hardcoded skill sets per job category
# ──────────────────────────────────────────────────────────────────────────────

def _sr(skill_name: str, category: str, importance: str, description: str) -> SkillRequirement:
    return SkillRequirement(skill_name=skill_name, category=category,
                            importance=importance, description=description)  # type: ignore[arg-type]


_FALLBACK_SKILLS: dict[str, list[SkillRequirement]] = {
    "cloud": [
        _sr("AWS", "Cloud Platforms", "required", "Provision and manage core AWS services."),
        _sr("GCP", "Cloud Platforms", "preferred", "Deploy workloads on Google Cloud Platform."),
        _sr("Azure", "Cloud Platforms", "preferred", "Operate resources on Microsoft Azure."),
        _sr("Terraform", "Infrastructure as Code", "required", "Write repeatable IaC modules."),
        _sr("Ansible", "Configuration Management", "preferred", "Automate server configuration."),
        _sr("Docker", "Containerization", "required", "Build and run containerized services."),
        _sr("Kubernetes", "Container Orchestration", "required", "Manage container clusters."),
        _sr("Linux", "Operating Systems", "required", "Administer Linux servers."),
        _sr("Bash", "Scripting", "required", "Write shell scripts for automation."),
        _sr("Python", "Programming Languages", "required", "Automate cloud tasks with Python."),
        _sr("CI/CD", "DevOps", "required", "Build and maintain deployment pipelines."),
        _sr("Networking", "Networking", "required", "Understand VPCs, subnets, and routing."),
        _sr("IAM", "Security", "required", "Manage identity and access policies."),
        _sr("Monitoring", "Observability", "preferred", "Use Prometheus/Grafana or CloudWatch."),
        _sr("SQL", "Databases", "preferred", "Query relational databases."),
    ],
    "data": [
        _sr("Python", "Programming Languages", "required", "Write data pipelines in Python."),
        _sr("SQL", "Databases", "required", "Write complex analytical SQL queries."),
        _sr("Spark", "Big Data", "required", "Process large datasets with Apache Spark."),
        _sr("Airflow", "Orchestration", "required", "Schedule and monitor data workflows."),
        _sr("dbt", "Data Transformation", "preferred", "Transform data inside the warehouse."),
        _sr("Kafka", "Streaming", "preferred", "Build real-time data pipelines with Kafka."),
        _sr("Snowflake", "Data Warehousing", "preferred", "Load and query data in Snowflake."),
        _sr("BigQuery", "Data Warehousing", "preferred", "Analyse large datasets in BigQuery."),
        _sr("Docker", "Containerization", "required", "Containerize pipeline components."),
        _sr("Git", "Version Control", "required", "Track code and collaborate via Git."),
        _sr("AWS", "Cloud Platforms", "preferred", "Use S3, Glue, Redshift, and EMR."),
        _sr("Pandas", "Data Processing", "required", "Wrangle data with Pandas."),
        _sr("Data Modeling", "Architecture", "required", "Design star/snowflake schemas."),
        _sr("CI/CD", "DevOps", "preferred", "Automate testing of data pipelines."),
        _sr("Linux", "Operating Systems", "required", "Work in a Unix environment."),
    ],
    "frontend": [
        _sr("JavaScript", "Programming Languages", "required", "Build interactive UIs."),
        _sr("TypeScript", "Programming Languages", "required", "Add type safety to JS code."),
        _sr("React", "Frameworks", "required", "Build component-based UIs with React."),
        _sr("HTML", "Web Fundamentals", "required", "Write semantic HTML markup."),
        _sr("CSS", "Web Fundamentals", "required", "Style and layout web pages."),
        _sr("Next.js", "Frameworks", "preferred", "Build server-side rendered React apps."),
        _sr("REST APIs", "Integration", "required", "Consume JSON APIs from the browser."),
        _sr("Git", "Version Control", "required", "Track and review code changes."),
        _sr("Tailwind CSS", "Styling", "preferred", "Use utility-first CSS framework."),
        _sr("Testing", "Quality Assurance", "preferred", "Write unit and integration tests."),
        _sr("Webpack/Vite", "Build Tools", "required", "Bundle and optimize frontend assets."),
        _sr("Accessibility", "Web Standards", "preferred", "Build WCAG-compliant interfaces."),
        _sr("Performance", "Optimization", "preferred", "Optimize Core Web Vitals scores."),
        _sr("State Management", "Architecture", "required", "Manage global state (Redux/Zustand)."),
        _sr("CI/CD", "DevOps", "preferred", "Automate frontend build and deployment."),
    ],
    "backend": [
        _sr("Python", "Programming Languages", "required", "Build APIs and services."),
        _sr("REST APIs", "Integration", "required", "Design and implement RESTful services."),
        _sr("SQL", "Databases", "required", "Design schemas and write complex queries."),
        _sr("PostgreSQL", "Databases", "required", "Operate a production Postgres database."),
        _sr("Docker", "Containerization", "required", "Package services in containers."),
        _sr("Git", "Version Control", "required", "Track code and collaborate via Git."),
        _sr("Redis", "Caching", "preferred", "Cache data and manage sessions with Redis."),
        _sr("Authentication", "Security", "required", "Implement JWT/OAuth2 auth flows."),
        _sr("Linux", "Operating Systems", "required", "Deploy services on Linux servers."),
        _sr("CI/CD", "DevOps", "required", "Build deployment pipelines."),
        _sr("Microservices", "Architecture", "preferred", "Design decoupled service systems."),
        _sr("Message Queues", "Integration", "preferred", "Use Kafka or RabbitMQ for async tasks."),
        _sr("Testing", "Quality Assurance", "required", "Write unit and integration tests."),
        _sr("AWS", "Cloud Platforms", "preferred", "Deploy services on AWS."),
        _sr("Monitoring", "Observability", "preferred", "Set up logging and alerting."),
    ],
    "ml": [
        _sr("Python", "Programming Languages", "required", "Build ML pipelines in Python."),
        _sr("PyTorch", "ML Frameworks", "required", "Train and evaluate deep learning models."),
        _sr("TensorFlow", "ML Frameworks", "preferred", "Serve models with TensorFlow Serving."),
        _sr("scikit-learn", "ML Libraries", "required", "Apply classical ML algorithms."),
        _sr("SQL", "Databases", "required", "Query training data from databases."),
        _sr("Pandas", "Data Processing", "required", "Wrangle tabular datasets."),
        _sr("NumPy", "Numerical Computing", "required", "Perform vectorised computations."),
        _sr("MLflow", "MLOps", "preferred", "Track experiments and register models."),
        _sr("Docker", "Containerization", "required", "Containerize training and serving jobs."),
        _sr("Cloud ML", "Cloud Platforms", "preferred", "Use SageMaker, Vertex AI, or AzureML."),
        _sr("Statistics", "Mathematics", "required", "Apply probability and statistics."),
        _sr("Feature Engineering", "Data Science", "required", "Design informative model features."),
        _sr("Git", "Version Control", "required", "Version control code and notebooks."),
        _sr("Spark", "Big Data", "preferred", "Process large training datasets."),
        _sr("LLM APIs", "AI Integration", "preferred", "Integrate and fine-tune large LLMs."),
    ],
}

_GENERIC_SKILLS: list[SkillRequirement] = [
    _sr("Python", "Programming Languages", "required", "Write automation and backend code."),
    _sr("SQL", "Databases", "required", "Query and manage relational databases."),
    _sr("Git", "Version Control", "required", "Track code changes and collaborate."),
    _sr("Linux", "Operating Systems", "required", "Work in a Unix command-line environment."),
    _sr("REST APIs", "Integration", "required", "Consume and build RESTful services."),
    _sr("Docker", "Containerization", "preferred", "Package applications in containers."),
    _sr("CI/CD", "DevOps", "preferred", "Automate build and deployment pipelines."),
    _sr("Testing", "Quality Assurance", "preferred", "Write automated tests."),
    _sr("Cloud Basics", "Cloud Platforms", "preferred", "Use a major cloud provider."),
    _sr("Communication", "Soft Skills", "required", "Communicate clearly in a team."),
]


def _fallback_job_requirements(job_title: str) -> JobRequirements:
    """Return hardcoded skill list when LLM is unavailable."""
    title_lower = job_title.lower()
    if any(k in title_lower for k in ("cloud", "devops", "sre", "infrastructure", "platform")):
        skills = _FALLBACK_SKILLS["cloud"]
    elif any(k in title_lower for k in ("data engineer", "data eng", "etl", "pipeline")):
        skills = _FALLBACK_SKILLS["data"]
    elif any(k in title_lower for k in ("frontend", "front-end", "front end", "ui engineer")):
        skills = _FALLBACK_SKILLS["frontend"]
    elif any(k in title_lower for k in ("backend", "back-end", "back end", "api engineer")):
        skills = _FALLBACK_SKILLS["backend"]
    elif any(k in title_lower for k in ("machine learning", "ml engineer", "ai engineer", "deep learning", "data scientist")):
        skills = _FALLBACK_SKILLS["ml"]
    else:
        skills = _GENERIC_SKILLS
    return JobRequirements(job_title=job_title, required_skills=skills)

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


def _validate_and_repair_job_requirements(reqs: JobRequirements) -> JobRequirements:
    """Deduplicate skills (case-insensitive) and fix any invalid importance values."""
    seen: set[str] = set()
    deduped: list[SkillRequirement] = []
    for skill in reqs.required_skills:
        key = skill.skill_name.strip().lower()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        # Coerce any non-standard importance to "preferred"
        importance = skill.importance if skill.importance in ("required", "preferred") else "preferred"
        deduped.append(SkillRequirement(
            skill_name=skill.skill_name.strip(),
            category=skill.category.strip() or "General",
            importance=importance,  # type: ignore[arg-type]
            description=skill.description.strip() or f"Proficiency in {skill.skill_name}.",
        ))
    return JobRequirements(job_title=reqs.job_title, required_skills=deduped)


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

    def _parse_result(raw: str) -> JobRequirements:
        reqs = JobRequirements.model_validate_json(extract_json(raw))
        reqs = _validate_and_repair_job_requirements(reqs)
        if len(reqs.required_skills) < 10:
            raise ValueError(
                f"Too few skills returned: {len(reqs.required_skills)} (expected ≥10)"
            )
        return reqs

    try:
        result = crew.kickoff()
        raw = result.raw if hasattr(result, "raw") else str(result)
        try:
            return _parse_result(raw)
        except Exception as first_exc:
            print(f"[RETRY] job_requirements: first attempt failed ({first_exc!r}), retrying")
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)
            return _parse_result(raw)
    except Exception as exc:
        print(f"[FALLBACK] job_requirements: AI failed ({exc!r}), using hardcoded skill set")
        return _fallback_job_requirements(job_title)
