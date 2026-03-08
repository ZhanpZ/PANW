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

# In-memory cache keyed by normalized job title (lives for the server process lifetime)
_job_reqs_cache: dict[str, JobRequirements] = {}

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback: hardcoded skill sets per job category
# ──────────────────────────────────────────────────────────────────────────────

def _sr(skill_name: str, category: str, importance: str, description: str) -> SkillRequirement:
    return SkillRequirement(skill_name=skill_name, category=category,
                            importance=importance, description=description)  # type: ignore[arg-type]


_FALLBACK_SKILLS: dict[str, list[SkillRequirement]] = {
    "cloud": [
        _sr("AWS", "Cloud Platforms", "required", "Provision and manage core AWS services (EC2, S3, VPC, RDS)."),
        _sr("GCP", "Cloud Platforms", "preferred", "Deploy workloads on Google Cloud Platform."),
        _sr("Azure", "Cloud Platforms", "preferred", "Operate resources on Microsoft Azure."),
        _sr("Terraform", "Infrastructure as Code", "required", "Write repeatable IaC modules for cloud resources."),
        _sr("Ansible", "Configuration Management", "preferred", "Automate server configuration at scale."),
        _sr("Docker", "Containerization", "required", "Build and run containerized services."),
        _sr("Kubernetes", "Container Orchestration", "required", "Manage container clusters and workloads."),
        _sr("Linux", "Operating Systems", "required", "Administer Linux servers and troubleshoot issues."),
        _sr("Bash", "Scripting", "required", "Write shell scripts for automation and ops tasks."),
        _sr("Python", "Programming Languages", "required", "Automate cloud tasks and build tooling in Python."),
        _sr("CI/CD", "DevOps", "required", "Build and maintain deployment pipelines."),
        _sr("Networking", "Networking", "required", "Understand VPCs, subnets, routing, and load balancers."),
        _sr("IAM", "Security", "required", "Manage identity and access policies securely."),
        _sr("Monitoring", "Observability", "required", "Use Prometheus/Grafana or CloudWatch for alerting."),
        _sr("SQL", "Databases", "preferred", "Query relational databases and diagnose performance."),
        _sr("Helm", "Package Management", "preferred", "Manage Kubernetes releases with Helm charts."),
        _sr("Git", "Version Control", "required", "Track infrastructure code and collaborate."),
        _sr("Security", "Security", "required", "Implement secrets management and security best practices."),
        _sr("Cost Optimization", "Cloud Management", "preferred", "Analyze and optimize cloud spend."),
        _sr("DNS", "Networking", "preferred", "Configure and troubleshoot DNS records and routing."),
        _sr("Load Balancing", "Networking", "required", "Set up and manage application load balancers."),
        _sr("Object Storage", "Cloud Services", "required", "Manage object storage (S3/GCS) for data and artifacts."),
        _sr("Serverless", "Cloud Services", "preferred", "Build event-driven functions with Lambda or Cloud Functions."),
        _sr("Auto Scaling", "Cloud Services", "required", "Configure auto-scaling policies for high availability."),
        _sr("Cloud Certifications", "Professional Development", "preferred", "Pursue AWS/GCP/Azure associate certifications."),
    ],
    "data": [
        _sr("Python", "Programming Languages", "required", "Write data pipelines and ETL jobs in Python."),
        _sr("SQL", "Databases", "required", "Write complex analytical SQL queries and optimize performance."),
        _sr("Spark", "Big Data", "required", "Process large datasets with Apache Spark."),
        _sr("Airflow", "Orchestration", "required", "Schedule and monitor data workflows with Airflow."),
        _sr("dbt", "Data Transformation", "preferred", "Transform data inside the warehouse using dbt."),
        _sr("Kafka", "Streaming", "preferred", "Build real-time data pipelines with Kafka."),
        _sr("Snowflake", "Data Warehousing", "preferred", "Load and query data in Snowflake."),
        _sr("BigQuery", "Data Warehousing", "preferred", "Analyse large datasets using BigQuery."),
        _sr("Docker", "Containerization", "required", "Containerize pipeline components and jobs."),
        _sr("Git", "Version Control", "required", "Track code and collaborate on data pipelines."),
        _sr("AWS", "Cloud Platforms", "preferred", "Use S3, Glue, Redshift, and EMR for data workflows."),
        _sr("Pandas", "Data Processing", "required", "Wrangle and explore data with Pandas."),
        _sr("Data Modeling", "Architecture", "required", "Design star/snowflake schemas for analytics."),
        _sr("CI/CD", "DevOps", "preferred", "Automate testing and deployment of data pipelines."),
        _sr("Linux", "Operating Systems", "required", "Work effectively in a Unix command-line environment."),
        _sr("Data Quality", "Data Engineering", "required", "Implement data validation and quality checks."),
        _sr("NoSQL Databases", "Databases", "preferred", "Work with MongoDB, DynamoDB, or Cassandra."),
        _sr("Delta Lake / Iceberg", "Data Formats", "preferred", "Use open table formats for reliable data lakes."),
        _sr("NumPy", "Numerical Computing", "preferred", "Perform vectorised computations on arrays."),
        _sr("Data Governance", "Architecture", "preferred", "Understand data lineage, cataloguing, and compliance."),
        _sr("Visualization", "Analytics", "preferred", "Build dashboards with Tableau, Looker, or similar tools."),
        _sr("Statistics", "Mathematics", "preferred", "Apply statistical methods to analyze data distributions."),
        _sr("Terraform", "Infrastructure as Code", "preferred", "Provision data infrastructure repeatably."),
        _sr("Testing", "Quality Assurance", "required", "Write unit and integration tests for pipelines."),
        _sr("REST APIs", "Integration", "preferred", "Ingest data from third-party REST APIs."),
    ],
    "frontend": [
        _sr("JavaScript", "Programming Languages", "required", "Build interactive UIs in vanilla JS."),
        _sr("TypeScript", "Programming Languages", "required", "Add static type safety to JavaScript code."),
        _sr("React", "Frameworks", "required", "Build component-based UIs with React."),
        _sr("HTML", "Web Fundamentals", "required", "Write semantic, accessible HTML markup."),
        _sr("CSS", "Web Fundamentals", "required", "Style and layout web pages with modern CSS."),
        _sr("Next.js", "Frameworks", "preferred", "Build server-side rendered and static React apps."),
        _sr("REST APIs", "Integration", "required", "Consume JSON APIs from the browser."),
        _sr("Git", "Version Control", "required", "Track and review code changes effectively."),
        _sr("Tailwind CSS", "Styling", "preferred", "Use utility-first CSS framework for rapid styling."),
        _sr("Testing", "Quality Assurance", "preferred", "Write unit, integration, and E2E tests."),
        _sr("Webpack/Vite", "Build Tools", "required", "Bundle and optimize frontend assets."),
        _sr("Accessibility", "Web Standards", "preferred", "Build WCAG-compliant, inclusive interfaces."),
        _sr("Performance", "Optimization", "preferred", "Optimize Core Web Vitals and page load speeds."),
        _sr("State Management", "Architecture", "required", "Manage global state with Redux, Zustand, or Context."),
        _sr("CI/CD", "DevOps", "preferred", "Automate frontend build, test, and deployment."),
        _sr("GraphQL", "Integration", "preferred", "Consume GraphQL APIs from React components."),
        _sr("Browser DevTools", "Tooling", "required", "Debug and profile apps using browser developer tools."),
        _sr("Responsive Design", "Web Fundamentals", "required", "Build layouts that work across all screen sizes."),
        _sr("SEO Fundamentals", "Web Standards", "preferred", "Implement on-page SEO and structured data."),
        _sr("Web Security", "Security", "required", "Prevent XSS, CSRF, and understand Content Security Policy."),
        _sr("Node.js", "Backend Basics", "preferred", "Understand the Node.js runtime for tooling and SSR."),
        _sr("Docker", "Containerization", "preferred", "Containerize frontend applications for deployment."),
        _sr("Design Systems", "Architecture", "preferred", "Build and consume reusable component libraries."),
        _sr("Progressive Web Apps", "Web Standards", "preferred", "Add offline support and installability with PWA."),
        _sr("Animation / Motion", "UI/UX", "preferred", "Use CSS animations or Framer Motion for interactions."),
    ],
    "backend": [
        _sr("Python", "Programming Languages", "required", "Build APIs and backend services in Python."),
        _sr("REST APIs", "Integration", "required", "Design and implement RESTful services."),
        _sr("SQL", "Databases", "required", "Design schemas and write complex queries."),
        _sr("PostgreSQL", "Databases", "required", "Operate and optimize a production Postgres database."),
        _sr("Docker", "Containerization", "required", "Package services in containers for deployment."),
        _sr("Git", "Version Control", "required", "Track code and collaborate via Git."),
        _sr("Redis", "Caching", "preferred", "Cache data and manage sessions with Redis."),
        _sr("Authentication", "Security", "required", "Implement JWT/OAuth2 auth flows securely."),
        _sr("Linux", "Operating Systems", "required", "Deploy and troubleshoot services on Linux servers."),
        _sr("CI/CD", "DevOps", "required", "Build automated deployment pipelines."),
        _sr("Microservices", "Architecture", "preferred", "Design and operate decoupled service systems."),
        _sr("Message Queues", "Integration", "preferred", "Use Kafka or RabbitMQ for async task processing."),
        _sr("Testing", "Quality Assurance", "required", "Write unit, integration, and contract tests."),
        _sr("AWS", "Cloud Platforms", "preferred", "Deploy and scale services on AWS."),
        _sr("Monitoring", "Observability", "preferred", "Set up logging, tracing, and alerting."),
        _sr("GraphQL", "Integration", "preferred", "Design and implement GraphQL APIs."),
        _sr("NoSQL Databases", "Databases", "preferred", "Work with MongoDB, DynamoDB, or Redis as a database."),
        _sr("API Design", "Architecture", "required", "Apply REST best practices, versioning, and pagination."),
        _sr("Security", "Security", "required", "Harden APIs against OWASP Top 10 vulnerabilities."),
        _sr("Performance Tuning", "Optimization", "preferred", "Profile and optimize slow queries and endpoints."),
        _sr("WebSockets", "Integration", "preferred", "Build real-time features using WebSockets."),
        _sr("Celery / Task Queues", "Integration", "preferred", "Run background tasks asynchronously with Celery."),
        _sr("ORM", "Databases", "required", "Use SQLAlchemy or Django ORM for database interactions."),
        _sr("Bash", "Scripting", "preferred", "Write shell scripts for operational automation."),
        _sr("Data Serialization", "Architecture", "required", "Work with JSON, Protobuf, or Avro for data exchange."),
    ],
    "fullstack": [
        _sr("JavaScript", "Programming Languages", "required", "Build interactive UIs and Node.js services."),
        _sr("TypeScript", "Programming Languages", "required", "Add type safety to both frontend and backend code."),
        _sr("React", "Frontend Frameworks", "required", "Build component-based UIs with React."),
        _sr("Node.js", "Backend Frameworks", "required", "Build REST APIs and server-side logic with Node.js."),
        _sr("REST APIs", "Integration", "required", "Design and consume RESTful services end-to-end."),
        _sr("SQL", "Databases", "required", "Design schemas and write complex database queries."),
        _sr("PostgreSQL", "Databases", "required", "Operate a production Postgres database."),
        _sr("HTML/CSS", "Web Fundamentals", "required", "Write semantic HTML and modern CSS layouts."),
        _sr("Docker", "Containerization", "required", "Containerize frontend and backend services."),
        _sr("Git", "Version Control", "required", "Track code and collaborate via Git workflows."),
        _sr("Authentication", "Security", "required", "Implement JWT/OAuth2 auth flows on both layers."),
        _sr("CI/CD", "DevOps", "required", "Automate build, test, and deployment pipelines."),
        _sr("State Management", "Architecture", "required", "Manage global state with Redux/Zustand/Context."),
        _sr("Testing", "Quality Assurance", "required", "Write unit and integration tests for frontend and backend."),
        _sr("AWS", "Cloud Platforms", "preferred", "Deploy full-stack apps on AWS."),
        _sr("GraphQL", "Integration", "preferred", "Build and consume GraphQL APIs."),
        _sr("Next.js", "Frontend Frameworks", "preferred", "Build SSR/SSG apps for performance and SEO."),
        _sr("NoSQL Databases", "Databases", "preferred", "Use MongoDB or Redis for non-relational data."),
        _sr("Tailwind CSS", "Styling", "preferred", "Build UIs quickly with utility-first CSS."),
        _sr("WebSockets", "Integration", "preferred", "Add real-time functionality with WebSockets."),
        _sr("Linux", "Operating Systems", "required", "Deploy and manage services on Linux servers."),
        _sr("Security", "Security", "required", "Secure both API and frontend against common vulnerabilities."),
        _sr("Performance Optimization", "Optimization", "preferred", "Improve load times and API response speeds."),
        _sr("Microservices", "Architecture", "preferred", "Break down monoliths into independent services."),
        _sr("Monitoring", "Observability", "preferred", "Add logging and alerting across the full stack."),
    ],
    "devops": [
        _sr("Linux", "Operating Systems", "required", "Administer Linux servers and troubleshoot systems deeply."),
        _sr("Bash", "Scripting", "required", "Write shell scripts for automation and operational tasks."),
        _sr("Docker", "Containerization", "required", "Build, ship, and run containerized services."),
        _sr("Kubernetes", "Container Orchestration", "required", "Deploy and manage production workloads on Kubernetes."),
        _sr("Terraform", "Infrastructure as Code", "required", "Write repeatable, version-controlled IaC with Terraform."),
        _sr("Ansible", "Configuration Management", "required", "Automate configuration and application deployment."),
        _sr("CI/CD", "DevOps", "required", "Build pipelines with GitHub Actions, Jenkins, or GitLab CI."),
        _sr("AWS", "Cloud Platforms", "required", "Provision and manage core AWS services at scale."),
        _sr("Networking", "Networking", "required", "Understand VPCs, subnets, DNS, and load balancers."),
        _sr("Monitoring", "Observability", "required", "Set up Prometheus, Grafana, and PagerDuty alerting."),
        _sr("Python", "Programming Languages", "required", "Automate operational tasks and build tooling in Python."),
        _sr("Git", "Version Control", "required", "Track infrastructure code and collaborate across teams."),
        _sr("Security", "Security", "required", "Implement IAM policies, secrets management, and hardening."),
        _sr("Helm", "Package Management", "preferred", "Manage Kubernetes application releases with Helm."),
        _sr("GCP", "Cloud Platforms", "preferred", "Deploy workloads on Google Cloud Platform."),
        _sr("Azure", "Cloud Platforms", "preferred", "Operate infrastructure on Microsoft Azure."),
        _sr("Service Mesh", "Networking", "preferred", "Use Istio or Linkerd for microservice traffic management."),
        _sr("Log Aggregation", "Observability", "required", "Centralize logs with the ELK stack or Loki."),
        _sr("Incident Response", "Operations", "required", "Manage on-call rotations, runbooks, and post-mortems."),
        _sr("Cost Optimization", "Cloud Management", "preferred", "Analyse and reduce cloud infrastructure spend."),
        _sr("GitOps", "DevOps", "preferred", "Apply GitOps principles with ArgoCD or Flux."),
        _sr("Vault", "Security", "preferred", "Manage secrets securely with HashiCorp Vault."),
        _sr("Load Testing", "Quality Assurance", "preferred", "Stress test infrastructure with k6 or JMeter."),
        _sr("DNS Management", "Networking", "required", "Configure Route53 or Cloud DNS for service discovery."),
        _sr("Backup & Recovery", "Operations", "required", "Design backup strategies and practice disaster recovery."),
    ],
    "sre": [
        _sr("Linux", "Operating Systems", "required", "Deep Linux internals for incident diagnosis and tuning."),
        _sr("Python", "Programming Languages", "required", "Write automation, tooling, and runbooks in Python."),
        _sr("Kubernetes", "Container Orchestration", "required", "Operate and troubleshoot production Kubernetes clusters."),
        _sr("Docker", "Containerization", "required", "Build and manage containerized services."),
        _sr("Monitoring", "Observability", "required", "Instrument services with Prometheus, Grafana, and PagerDuty."),
        _sr("Distributed Systems", "Architecture", "required", "Understand CAP theorem, SLOs, SLAs, and error budgets."),
        _sr("Networking", "Networking", "required", "Debug DNS, load balancers, and network performance issues."),
        _sr("Terraform", "Infrastructure as Code", "required", "Manage infrastructure reliably and repeatably."),
        _sr("CI/CD", "DevOps", "required", "Build and maintain reliable, automated deployment pipelines."),
        _sr("AWS", "Cloud Platforms", "required", "Operate and secure production workloads on AWS."),
        _sr("Bash", "Scripting", "required", "Automate operational and incident-response tasks."),
        _sr("Incident Response", "Operations", "required", "Lead on-call rotations, blameless post-mortems, and runbooks."),
        _sr("SQL", "Databases", "required", "Query and diagnose database performance issues."),
        _sr("Go", "Programming Languages", "preferred", "Write high-performance SRE tooling in Go."),
        _sr("Chaos Engineering", "Reliability", "preferred", "Design and run fault-injection experiments."),
        _sr("Log Aggregation", "Observability", "required", "Centralize and query logs with ELK or Loki."),
        _sr("Tracing", "Observability", "preferred", "Use OpenTelemetry or Jaeger for distributed tracing."),
        _sr("Capacity Planning", "Operations", "required", "Model growth and plan infrastructure capacity proactively."),
        _sr("Service Mesh", "Networking", "preferred", "Use Istio for traffic management and mTLS."),
        _sr("Error Budgets", "Reliability", "required", "Define and enforce SLO error budgets across services."),
        _sr("Load Testing", "Quality Assurance", "required", "Simulate production load with k6 or Locust."),
        _sr("Backup & Recovery", "Operations", "required", "Automate backups and validate disaster recovery procedures."),
        _sr("Security", "Security", "required", "Apply defence-in-depth and manage access controls."),
        _sr("Toil Reduction", "Operations", "required", "Identify and automate repetitive operational toil."),
        _sr("On-Call Practices", "Operations", "required", "Design sustainable on-call rotations and escalation policies."),
    ],
    "ml": [
        _sr("Python", "Programming Languages", "required", "Build ML pipelines, scripts, and services in Python."),
        _sr("PyTorch", "ML Frameworks", "required", "Train, evaluate, and deploy deep learning models."),
        _sr("TensorFlow", "ML Frameworks", "preferred", "Build and serve production models with TensorFlow."),
        _sr("scikit-learn", "ML Libraries", "required", "Apply classical ML algorithms for tabular data."),
        _sr("SQL", "Databases", "required", "Query and retrieve training data from relational databases."),
        _sr("Pandas", "Data Processing", "required", "Wrangle and explore tabular datasets."),
        _sr("NumPy", "Numerical Computing", "required", "Perform vectorised numerical computations."),
        _sr("MLflow", "MLOps", "preferred", "Track experiments, register, and serve models with MLflow."),
        _sr("Docker", "Containerization", "required", "Containerize training jobs and serving endpoints."),
        _sr("Cloud ML", "Cloud Platforms", "preferred", "Use SageMaker, Vertex AI, or AzureML for managed training."),
        _sr("Statistics", "Mathematics", "required", "Apply probability, hypothesis testing, and statistics."),
        _sr("Feature Engineering", "Data Science", "required", "Design and select informative model features."),
        _sr("Git", "Version Control", "required", "Version control code, configs, and notebooks."),
        _sr("Spark", "Big Data", "preferred", "Process large-scale training datasets with Spark."),
        _sr("LLM APIs", "AI Integration", "preferred", "Integrate and fine-tune large language models."),
        _sr("Model Evaluation", "ML Engineering", "required", "Define and compute correct metrics for each task type."),
        _sr("A/B Testing", "Analytics", "preferred", "Design and analyze controlled ML model experiments."),
        _sr("Data Pipelines", "Data Engineering", "required", "Build reliable data ingestion and preprocessing pipelines."),
        _sr("Hugging Face", "ML Libraries", "preferred", "Use Transformers library for NLP tasks."),
        _sr("Kubernetes", "Container Orchestration", "preferred", "Deploy ML workloads on Kubernetes with Kubeflow."),
        _sr("Linear Algebra", "Mathematics", "required", "Understand matrix operations, gradients, and tensors."),
        _sr("Model Serving", "MLOps", "required", "Deploy models as REST or gRPC APIs for production."),
        _sr("CI/CD for ML", "MLOps", "preferred", "Automate model training, testing, and deployment pipelines."),
        _sr("Monitoring ML Models", "MLOps", "preferred", "Detect data drift, model decay, and anomalies in production."),
        _sr("Jupyter Notebooks", "Tooling", "required", "Use Jupyter for exploratory data analysis and prototyping."),
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
    if any(k in title_lower for k in ("site reliability", "sre")):
        skills = _FALLBACK_SKILLS["sre"]
    elif any(k in title_lower for k in ("devops", "platform engineer", "infrastructure engineer")):
        skills = _FALLBACK_SKILLS["devops"]
    elif any(k in title_lower for k in ("cloud engineer", "cloud infrastructure")):
        skills = _FALLBACK_SKILLS["cloud"]
    elif any(k in title_lower for k in ("data engineer", "data eng", "etl", "pipeline")):
        skills = _FALLBACK_SKILLS["data"]
    elif any(k in title_lower for k in ("full stack", "fullstack", "full-stack")):
        skills = _FALLBACK_SKILLS["fullstack"]
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
    cache_key = job_title.strip().lower()
    if cache_key in _job_reqs_cache:
        print(f"[cache] job_requirements: returning cached result for '{job_title}'")
        return _job_reqs_cache[cache_key]

    llm = get_llm(max_tokens=3000)

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
Based on your knowledge of the current job market, produce a COMPREHENSIVE list of
ALL technical skills typically required or strongly preferred for a **{job_title}** role.

This list will be used to build a complete career roadmap. Be thorough — include every
skill a hiring manager would look for, from fundamentals to advanced specializations.

Aim for 15–20 skills covering the most important categories (e.g. Cloud Platforms,
Networking, Security, CI/CD, Programming Languages, Databases, Monitoring,
Architecture, Tools, Frameworks, etc.).

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}

Rules:
- importance must be exactly "required" or "preferred" — no other values
- category groups related skills (each skill belongs to exactly one category)
- description: 1–2 sentences explaining what proficiency looks like in practice
- Produce AT LEAST 12 skills total — focus on the highest-impact skills for the role
- Prioritize foundational and frequently assessed skills over niche specializations
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
        if len(reqs.required_skills) < 12:
            raise ValueError(
                f"Too few skills returned: {len(reqs.required_skills)} (expected ≥12)"
            )
        return reqs

    try:
        result = crew.kickoff()
        raw = result.raw if hasattr(result, "raw") else str(result)
        try:
            reqs = _parse_result(raw)
        except Exception as first_exc:
            print(f"[RETRY] job_requirements: first attempt failed ({first_exc!r}), retrying")
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)
            reqs = _parse_result(raw)
    except Exception as exc:
        print(f"[FALLBACK] job_requirements: AI failed ({exc!r}), using hardcoded skill set")
        reqs = _fallback_job_requirements(job_title)

    _job_reqs_cache[cache_key] = reqs
    return reqs
