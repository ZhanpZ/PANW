"""
Agent 4 — RoadmapGeneratorAgent
Input : GapAnalysis, job_title (str)
Output: GeneratedRoadmap
"""

import json

from crewai import Agent, Crew, Task

from app.schemas.agent_contracts import GapAnalysis, GeneratedRoadmap, ResourceSpec, RoadmapNode
from app.services.crew_service import extract_json
from app.services.llm_factory import get_llm

# ──────────────────────────────────────────────────────────────────────────────
# Rule-based fallback resource library
# ──────────────────────────────────────────────────────────────────────────────

# Each entry: (keywords, [free resources], [paid resources])
_RESOURCE_TEMPLATES: list[tuple[list[str], list[ResourceSpec], list[ResourceSpec]]] = [
    (["cloud", "aws", "gcp", "azure", "infrastructure"], [
        ResourceSpec(title="AWS Getting Started (free tier)", url="https://aws.amazon.com/getting-started/", resource_type="free", platform="AWS"),
        ResourceSpec(title="Google Cloud Skills Boost (free tier)", url="https://www.cloudskillsboost.google/", resource_type="free", platform="Google Cloud"),
        ResourceSpec(title="Microsoft Azure Fundamentals (free learning path)", url="https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/", resource_type="free", platform="Microsoft Learn"),
        ResourceSpec(title="roadmap.sh DevOps Roadmap", url="https://roadmap.sh/devops", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="AWS Certified Cloud Practitioner — Udemy", url="https://www.udemy.com/course/aws-certified-cloud-practitioner-new/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Google Cloud Professional Engineer — Coursera", url="https://www.coursera.org/professional-certificates/gcp-cloud-engineer", resource_type="paid", platform="Coursera"),
        ResourceSpec(title="ACloudGuru Cloud Fundamentals", url="https://acloudguru.com/", resource_type="paid", platform="A Cloud Guru"),
    ]),
    (["docker", "container", "kubernetes", "helm", "orchestrat"], [
        ResourceSpec(title="Docker Official Get Started", url="https://docs.docker.com/get-started/", resource_type="free", platform="Docker Docs"),
        ResourceSpec(title="Kubernetes Official Interactive Tutorial", url="https://kubernetes.io/docs/tutorials/", resource_type="free", platform="kubernetes.io"),
        ResourceSpec(title="Play with Docker (free online labs)", url="https://labs.play-with-docker.com/", resource_type="free", platform="Docker"),
    ], [
        ResourceSpec(title="Docker and Kubernetes: The Complete Guide — Udemy", url="https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Certified Kubernetes Administrator (CKA) — Linux Foundation", url="https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/", resource_type="paid", platform="Linux Foundation"),
        ResourceSpec(title="KodeKloud Kubernetes Course", url="https://kodekloud.com/courses/certified-kubernetes-administrator-cka/", resource_type="paid", platform="KodeKloud"),
    ]),
    (["python"], [
        ResourceSpec(title="Python Official Tutorial — python.org", url="https://docs.python.org/3/tutorial/", resource_type="free", platform="python.org"),
        ResourceSpec(title="freeCodeCamp Python for Everybody", url="https://www.freecodecamp.org/news/python-for-everybody/", resource_type="free", platform="freeCodeCamp"),
        ResourceSpec(title="Real Python tutorials", url="https://realpython.com/", resource_type="free", platform="Real Python"),
        ResourceSpec(title="Python roadmap.sh", url="https://roadmap.sh/python", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Complete Python Bootcamp — Udemy", url="https://www.udemy.com/course/complete-python-bootcamp/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Python 3 Programming Specialization — Coursera", url="https://www.coursera.org/specializations/python-3-programming", resource_type="paid", platform="Coursera"),
    ]),
    (["sql", "database", "postgres", "mysql"], [
        ResourceSpec(title="SQLZoo (free interactive SQL)", url="https://sqlzoo.net/", resource_type="free", platform="SQLZoo"),
        ResourceSpec(title="Mode SQL Tutorial", url="https://mode.com/sql-tutorial/", resource_type="free", platform="Mode"),
        ResourceSpec(title="PostgreSQL Official Documentation", url="https://www.postgresql.org/docs/current/tutorial.html", resource_type="free", platform="PostgreSQL"),
        ResourceSpec(title="roadmap.sh PostgreSQL DBA", url="https://roadmap.sh/postgresql-dba", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="The Complete SQL Bootcamp — Udemy", url="https://www.udemy.com/course/the-complete-sql-bootcamp/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="SQL for Data Science — Coursera", url="https://www.coursera.org/learn/sql-for-data-science", resource_type="paid", platform="Coursera"),
    ]),
    (["javascript", "typescript", "react", "frontend", "node"], [
        ResourceSpec(title="javascript.info (free, comprehensive)", url="https://javascript.info/", resource_type="free", platform="javascript.info"),
        ResourceSpec(title="The Odin Project (full-stack free curriculum)", url="https://www.theodinproject.com/", resource_type="free", platform="The Odin Project"),
        ResourceSpec(title="React Official Tutorial", url="https://react.dev/learn", resource_type="free", platform="react.dev"),
        ResourceSpec(title="roadmap.sh Frontend Roadmap", url="https://roadmap.sh/frontend", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="The Complete JavaScript Course — Udemy", url="https://www.udemy.com/course/the-complete-javascript-course/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Frontend Masters JavaScript Path", url="https://frontendmasters.com/learn/javascript/", resource_type="paid", platform="Frontend Masters"),
        ResourceSpec(title="Zero to Mastery: React Developer — Udemy", url="https://www.udemy.com/course/complete-react-developer-zero-to-mastery/", resource_type="paid", platform="Udemy"),
    ]),
    (["linux", "bash", "shell", "unix"], [
        ResourceSpec(title="The Linux Command Line (free book)", url="https://linuxcommand.org/tlcl.php", resource_type="free", platform="linuxcommand.org"),
        ResourceSpec(title="OverTheWire: Bandit (Linux wargame)", url="https://overthewire.org/wargames/bandit/", resource_type="free", platform="OverTheWire"),
        ResourceSpec(title="freeCodeCamp: Linux for Beginners", url="https://www.freecodecamp.org/news/introduction-to-linux/", resource_type="free", platform="freeCodeCamp"),
    ], [
        ResourceSpec(title="Linux for Beginners — Udemy", url="https://www.udemy.com/course/linux-for-beginners/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Linux Foundation System Administrator — edX", url="https://www.edx.org/professional-certificate/linuxfoundationx-linux-system-administration", resource_type="paid", platform="edX"),
    ]),
    (["machine learning", "ml", "deep learning", "pytorch", "tensorflow", "scikit"], [
        ResourceSpec(title="fast.ai Practical Deep Learning (free)", url="https://course.fast.ai/", resource_type="free", platform="fast.ai"),
        ResourceSpec(title="Google ML Crash Course (free)", url="https://developers.google.com/machine-learning/crash-course", resource_type="free", platform="Google"),
        ResourceSpec(title="Kaggle Learn — free ML micro-courses", url="https://www.kaggle.com/learn", resource_type="free", platform="Kaggle"),
        ResourceSpec(title="roadmap.sh AI/ML Roadmap", url="https://roadmap.sh/ai-ml-roadmap", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Machine Learning Specialization — Coursera (Andrew Ng)", url="https://www.coursera.org/specializations/machine-learning-introduction", resource_type="paid", platform="Coursera"),
        ResourceSpec(title="Deep Learning Specialization — Coursera", url="https://www.coursera.org/specializations/deep-learning", resource_type="paid", platform="Coursera"),
        ResourceSpec(title="Zero to Mastery ML & Data Science Bootcamp — Udemy", url="https://www.udemy.com/course/complete-machine-learning-and-data-science-zero-to-mastery/", resource_type="paid", platform="Udemy"),
    ]),
    (["data", "spark", "airflow", "kafka", "etl", "pipeline", "dbt", "snowflake"], [
        ResourceSpec(title="roadmap.sh Data Engineer Roadmap", url="https://roadmap.sh/data-engineer", resource_type="free", platform="roadmap.sh"),
        ResourceSpec(title="Apache Spark Official Getting Started", url="https://spark.apache.org/docs/latest/quick-start.html", resource_type="free", platform="Apache"),
        ResourceSpec(title="dbt Learn (free fundamentals course)", url="https://courses.getdbt.com/courses/fundamentals", resource_type="free", platform="dbt"),
        ResourceSpec(title="Kafka Official Quickstart", url="https://kafka.apache.org/quickstart", resource_type="free", platform="Apache Kafka"),
    ], [
        ResourceSpec(title="Data Engineering Nanodegree — Udacity", url="https://www.udacity.com/course/data-engineer-nanodegree--nd027", resource_type="paid", platform="Udacity"),
        ResourceSpec(title="The Complete dbt Bootcamp — Udemy", url="https://www.udemy.com/course/complete-dbt-data-build-tool-bootcamp-zero-to-hero/", resource_type="paid", platform="Udemy"),
    ]),
    (["terraform", "ansible", "iac", "ci/cd", "devops", "github actions", "jenkins"], [
        ResourceSpec(title="HashiCorp Learn: Terraform (free)", url="https://developer.hashicorp.com/terraform/tutorials", resource_type="free", platform="HashiCorp"),
        ResourceSpec(title="GitHub Actions Official Docs", url="https://docs.github.com/en/actions", resource_type="free", platform="GitHub"),
        ResourceSpec(title="roadmap.sh DevOps Roadmap", url="https://roadmap.sh/devops", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="DevOps Bootcamp — Udemy", url="https://www.udemy.com/course/devops-bootcamp/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Terraform Associate Certification — HashiCorp (exam)", url="https://developer.hashicorp.com/certifications/infrastructure-automation", resource_type="paid", platform="HashiCorp"),
        ResourceSpec(title="Linux Foundation CI/CD Certificate", url="https://training.linuxfoundation.org/training/introduction-to-devops-and-site-reliability-engineering-lfs162/", resource_type="paid", platform="Linux Foundation"),
    ]),
    (["go", "golang"], [
        ResourceSpec(title="A Tour of Go (official interactive)", url="https://go.dev/tour/", resource_type="free", platform="go.dev"),
        ResourceSpec(title="Go by Example", url="https://gobyexample.com/", resource_type="free", platform="gobyexample.com"),
        ResourceSpec(title="roadmap.sh Go Roadmap", url="https://roadmap.sh/golang", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Go: The Complete Developer's Guide — Udemy", url="https://www.udemy.com/course/go-the-complete-developers-guide/", resource_type="paid", platform="Udemy"),
    ]),
    (["rust"], [
        ResourceSpec(title="The Rust Programming Language (free book)", url="https://doc.rust-lang.org/book/", resource_type="free", platform="rust-lang.org"),
        ResourceSpec(title="Rustlings exercises", url="https://github.com/rust-lang/rustlings", resource_type="free", platform="GitHub"),
    ], [
        ResourceSpec(title="Ultimate Rust Crash Course — Udemy", url="https://www.udemy.com/course/ultimate-rust-crash-course/", resource_type="paid", platform="Udemy"),
    ]),
    (["java", "spring", "jvm"], [
        ResourceSpec(title="Java Programming MOOC — University of Helsinki (free)", url="https://java-programming.mooc.fi/", resource_type="free", platform="MOOC.fi"),
        ResourceSpec(title="Spring Official Getting Started Guides", url="https://spring.io/guides", resource_type="free", platform="Spring"),
        ResourceSpec(title="roadmap.sh Java Roadmap", url="https://roadmap.sh/java", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Java Masterclass — Udemy", url="https://www.udemy.com/course/java-the-complete-java-developer-course/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Spring Framework 6: Beginner to Guru — Udemy", url="https://www.udemy.com/course/spring-framework-6-beginner-to-guru/", resource_type="paid", platform="Udemy"),
    ]),
    (["networking", "network", "tcp", "http", "dns", "load balanc"], [
        ResourceSpec(title="Computer Networking: A Top-Down Approach (free lectures)", url="https://gaia.cs.umass.edu/kurose_ross/online_lectures.htm", resource_type="free", platform="UMass"),
        ResourceSpec(title="Cloudflare Learning Center (free)", url="https://www.cloudflare.com/learning/", resource_type="free", platform="Cloudflare"),
    ], [
        ResourceSpec(title="The Complete Networking Fundamentals — Udemy", url="https://www.udemy.com/course/complete-networking-fundamentals-course-ccna-start/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="CompTIA Network+ Certification — Professor Messer (paid)", url="https://www.professormesser.com/network-plus/n10-008/n10-008-video/n10-008-training-course/", resource_type="paid", platform="Professor Messer"),
    ]),
    (["security", "cybersecurity", "devsecops", "owasp", "iam"], [
        ResourceSpec(title="OWASP Top 10 (free)", url="https://owasp.org/www-project-top-ten/", resource_type="free", platform="OWASP"),
        ResourceSpec(title="TryHackMe free learning paths", url="https://tryhackme.com/", resource_type="free", platform="TryHackMe"),
        ResourceSpec(title="roadmap.sh Cybersecurity Roadmap", url="https://roadmap.sh/cyber-security", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="CompTIA Security+ Study Guide — Udemy", url="https://www.udemy.com/course/comptia-security-sy0-601/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Certified Ethical Hacker (CEH) — EC-Council", url="https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/", resource_type="paid", platform="EC-Council"),
    ]),
    (["monitoring", "observability", "prometheus", "grafana", "slo", "sla", "alerting"], [
        ResourceSpec(title="Prometheus Getting Started (official)", url="https://prometheus.io/docs/introduction/overview/", resource_type="free", platform="Prometheus"),
        ResourceSpec(title="Grafana Fundamentals (free interactive)", url="https://grafana.com/tutorials/grafana-fundamentals/", resource_type="free", platform="Grafana"),
        ResourceSpec(title="Google SRE Book (free online)", url="https://sre.google/sre-book/table-of-contents/", resource_type="free", platform="Google"),
        ResourceSpec(title="roadmap.sh DevOps Roadmap — Monitoring section", url="https://roadmap.sh/devops", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Observability & Monitoring Masterclass — Udemy", url="https://www.udemy.com/course/mastering-prometheus-and-grafana/", resource_type="paid", platform="Udemy"),
        ResourceSpec(title="Site Reliability Engineering — Coursera", url="https://www.coursera.org/learn/site-reliability-engineering-slos", resource_type="paid", platform="Coursera"),
    ]),
    (["distributed systems", "incident response", "chaos engineering", "reliability", "on-call"], [
        ResourceSpec(title="Google SRE Book (free online)", url="https://sre.google/sre-book/table-of-contents/", resource_type="free", platform="Google"),
        ResourceSpec(title="Designing Data-Intensive Applications (free preview)", url="https://dataintensive.net/", resource_type="free", platform="O'Reilly"),
        ResourceSpec(title="roadmap.sh System Design", url="https://roadmap.sh/system-design", resource_type="free", platform="roadmap.sh"),
    ], [
        ResourceSpec(title="Distributed Systems — MIT 6.824 (free lectures, paid cert)", url="https://pdos.csail.mit.edu/6.824/", resource_type="paid", platform="MIT"),
        ResourceSpec(title="Cloud DevOps Engineer Nanodegree — Udacity", url="https://www.udacity.com/course/cloud-dev-ops-nanodegree--nd9991", resource_type="paid", platform="Udacity"),
    ]),
    (["git", "version control", "github", "gitlab"], [
        ResourceSpec(title="Pro Git Book (free)", url="https://git-scm.com/book/en/v2", resource_type="free", platform="git-scm.com"),
        ResourceSpec(title="GitHub Skills (free interactive courses)", url="https://skills.github.com/", resource_type="free", platform="GitHub"),
        ResourceSpec(title="Learn Git Branching (interactive)", url="https://learngitbranching.js.org/", resource_type="free", platform="learngitbranching.js.org"),
    ], [
        ResourceSpec(title="Git Complete: The Definitive Guide — Udemy", url="https://www.udemy.com/course/git-complete/", resource_type="paid", platform="Udemy"),
    ]),
]

_DEFAULT_FREE = [
    ResourceSpec(title="freeCodeCamp", url="https://www.freecodecamp.org/", resource_type="free", platform="freeCodeCamp"),
    ResourceSpec(title="roadmap.sh", url="https://roadmap.sh/", resource_type="free", platform="roadmap.sh"),
    ResourceSpec(title="MDN Web Docs", url="https://developer.mozilla.org/", resource_type="free", platform="MDN"),
]
_DEFAULT_PAID = [
    ResourceSpec(title="Udemy — search for this skill", url="https://www.udemy.com/", resource_type="paid", platform="Udemy"),
    ResourceSpec(title="Coursera — search for this skill", url="https://www.coursera.org/", resource_type="paid", platform="Coursera"),
]


def _get_resources(skill_name: str, category: str) -> list[ResourceSpec]:
    lookup = (skill_name + " " + category).lower()
    for keywords, free_list, paid_list in _RESOURCE_TEMPLATES:
        if any(kw in lookup for kw in keywords):
            return free_list + paid_list
    return _DEFAULT_FREE + _DEFAULT_PAID


def _fallback_roadmap_generator(gap_analysis: GapAnalysis, job_title: str) -> GeneratedRoadmap:
    """Build a flat roadmap from ALL LACK skills when LLM is unavailable."""
    lack_skills = [sg for sg in gap_analysis.skill_gaps if sg.mastery_level == "LACK"]
    nodes = [
        RoadmapNode(
            skill_name=sg.skill_name,
            category=sg.category,
            mastery_level="LACK",
            reasoning=f"AI unavailable — rule-based fallback for {job_title} role.",
            description=f"Learn {sg.skill_name} to meet {job_title} requirements.",
            estimated_hours=20,
            parent_skill=None,
            resources=_get_resources(sg.skill_name, sg.category),
        )
        for sg in lack_skills
    ]
    return GeneratedRoadmap(nodes=nodes)

SCHEMA_HINT = json.dumps(
    {
        "nodes": [
            {
                "skill_name": "Linux Fundamentals",
                "category": "Core Infrastructure",
                "mastery_level": "LACK",
                "reasoning": "No Linux experience found in the resume or GitHub profile.",
                "description": "Understanding of Linux filesystem, processes, networking, and shell scripting.",
                "estimated_hours": 20,
                "parent_skill": None,
                "resources": [
                    {"title": "The Linux Command Line (free book)", "url": "https://linuxcommand.org/tlcl.php", "resource_type": "free", "platform": "linuxcommand.org"},
                    {"title": "OverTheWire: Bandit (Linux wargame)", "url": "https://overthewire.org/wargames/bandit/", "resource_type": "free", "platform": "OverTheWire"},
                    {"title": "freeCodeCamp: Linux for Beginners", "url": "https://www.freecodecamp.org/news/introduction-to-linux/", "resource_type": "free", "platform": "freeCodeCamp"},
                    {"title": "Linux for Beginners — Udemy", "url": "https://www.udemy.com/course/linux-for-beginners/", "resource_type": "paid", "platform": "Udemy"},
                    {"title": "Linux Foundation SysAdmin — edX", "url": "https://www.edx.org/professional-certificate/linuxfoundationx-linux-system-administration", "resource_type": "paid", "platform": "edX"},
                ],
            },
            {
                "skill_name": "Docker",
                "category": "Containerization",
                "mastery_level": "LACK",
                "reasoning": "Docker not mentioned anywhere in the resume or GitHub projects.",
                "description": "Building, running, and managing Docker containers and images.",
                "estimated_hours": 15,
                "parent_skill": "Linux Fundamentals",
                "resources": [
                    {"title": "Docker Official Get Started Guide", "url": "https://docs.docker.com/get-started/", "resource_type": "free", "platform": "Docker Docs"},
                    {"title": "Play with Docker (free online labs)", "url": "https://labs.play-with-docker.com/", "resource_type": "free", "platform": "Docker"},
                    {"title": "Docker and Kubernetes: The Complete Guide — Udemy", "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/", "resource_type": "paid", "platform": "Udemy"},
                    {"title": "KodeKloud Docker Course", "url": "https://kodekloud.com/courses/docker-for-the-absolute-beginner/", "resource_type": "paid", "platform": "KodeKloud"},
                ],
            },
        ]
    },
    indent=2,
)


def _validate_and_repair_roadmap(
    roadmap: GeneratedRoadmap,
    gap_analysis: GapAnalysis,
    job_title: str,
) -> GeneratedRoadmap:
    """
    Enforce all roadmap constraints post-LLM:
    1. LACK-only nodes (discard DONE nodes — those are subtracted via the resume).
    2. Deduplicate nodes by skill_name (case-insensitive, first wins).
    3. Ensure each node has at least 2 free + 1 paid resource; inject from templates if missing.
    4. Nullify dangling parent_skill references.
    5. Clamp estimated_hours to [1, 200].
    6. Anchor to gap analysis: inject ALL remaining LACK skills the LLM dropped or renamed,
       so the roadmap is exhaustive — every skill gap from the job that is not on the resume appears.
    """
    # 1+2. Filter LACK and deduplicate — no hard cap; show all skill gaps
    seen: set[str] = set()
    filtered: list[RoadmapNode] = []
    for node in roadmap.nodes:
        key = node.skill_name.strip().lower()
        if node.mastery_level != "LACK" or not key or key in seen:
            continue
        seen.add(key)
        filtered.append(node)

    # 3. Repair resources per node — ensure ≥2 free + ≥1 paid
    repaired: list[RoadmapNode] = []
    for node in filtered:
        free_res = [r for r in node.resources if r.resource_type == "free"]
        paid_res = [r for r in node.resources if r.resource_type == "paid"]

        template = _get_resources(node.skill_name, node.category or "")
        template_free = [r for r in template if r.resource_type == "free"]
        template_paid = [r for r in template if r.resource_type == "paid"]

        # Fill in missing free resources (want at least 2)
        while len(free_res) < 2:
            candidate = template_free[len(free_res)] if len(free_res) < len(template_free) else _DEFAULT_FREE[0]
            free_res.append(candidate)

        # Fill in missing paid resources (want at least 1)
        if not paid_res:
            paid_res = template_paid[:2] if template_paid else _DEFAULT_PAID[:1]

        node.resources = free_res + paid_res
        node.estimated_hours = max(1, min(200, node.estimated_hours))
        repaired.append(node)

    # 4. Nullify dangling parent_skill references
    skill_names = {n.skill_name for n in repaired}
    for node in repaired:
        if node.parent_skill and node.parent_skill not in skill_names:
            node.parent_skill = None

    # 6. Anchor: inject ALL LACK skills from the gap analysis the LLM dropped or renamed.
    # This ensures the roadmap = full job skill list − resume skills (DONE), exhaustively.
    # Sort: required first, then preferred.
    repaired_lower = {n.skill_name.lower() for n in repaired}
    lack_gaps = [
        sg for sg in gap_analysis.skill_gaps
        if sg.mastery_level == "LACK"
        and sg.skill_name.lower() not in repaired_lower
    ]
    lack_gaps.sort(key=lambda sg: 0 if sg.importance == "required" else 1)

    for sg in lack_gaps:
        resources = _get_resources(sg.skill_name, sg.category or "")
        repaired.append(RoadmapNode(
            skill_name=sg.skill_name,
            category=sg.category,
            mastery_level="LACK",
            reasoning=sg.reasoning or f"Required for {job_title} role per gap analysis.",
            description=f"Develop proficiency in {sg.skill_name} as needed for the {job_title} role.",
            estimated_hours=20,
            parent_skill=None,
            resources=resources,
        ))

    # Rebuild skill_names after injection and re-nullify any new dangling refs
    skill_names = {n.skill_name for n in repaired}
    for node in repaired:
        if node.parent_skill and node.parent_skill not in skill_names:
            node.parent_skill = None

    return GeneratedRoadmap(nodes=repaired)


def run_roadmap_generator(gap_analysis: GapAnalysis, job_title: str) -> GeneratedRoadmap:
    llm = get_llm(max_tokens=6000)

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
    lack_gaps = [sg for sg in gap_analysis.skill_gaps if sg.mastery_level == "LACK"]
    lack_skills_str = "\n".join(f"  - {sg.skill_name} ({sg.category}, {sg.importance})" for sg in lack_gaps)

    task = Task(
        description=f"""
You are designing a comprehensive, dependency-aware learning roadmap for a candidate
targeting a **{job_title}** role.

The candidate's gap analysis identified these {len(lack_gaps)} skills as MISSING (LACK) —
these are the job requirements NOT already covered by the candidate's resume:
{lack_skills_str}

Full gap analysis JSON (for reasoning context):
{gap_json}

YOUR JOB: Convert EVERY LACK skill above into an ordered, dependency-aware learning roadmap.
The roadmap = (full {job_title} skill list) − (skills already on the resume).
Include ALL skills from the LACK list — do not drop any.

STRICT RULES — violation will cause the output to be rejected:
1. skill_name MUST be taken verbatim from the LACK skill list above — do NOT rename, merge,
   or invent new skills. Every node's skill_name must exactly match one of the names above.
2. mastery_level: always "LACK" — never "DONE"
3. Include ALL {len(lack_gaps)} LACK skills — output all of them, ordered by importance/dependency.
4. parent_skill: prerequisite skill_name (must exactly match another node's skill_name), or null.
5. resources: AT LEAST 2 free AND 2 paid resources per node with real, working URLs.
   - Free: official docs, freeCodeCamp, roadmap.sh, YouTube, Kaggle, interactive platforms
   - Paid: Udemy, Coursera, Pluralsight, Frontend Masters, A Cloud Guru, Linux Foundation
6. estimated_hours: integer 1–200
7. description: one sentence specific to what the skill covers in a {job_title} context.

Return ONLY a single valid JSON object — no markdown fences, no explanation.
Use this exact shape:
{SCHEMA_HINT}
""",
        expected_output=(
            "A JSON object with a 'nodes' array containing ALL LACK skills. Each node has: "
            "skill_name, category, mastery_level (LACK only), reasoning, description, "
            "estimated_hours (int 1-200), parent_skill (str|null), resources (list with "
            "at least 2 free and 2 paid entries)."
        ),
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False)

    def _parse_and_validate(raw: str) -> GeneratedRoadmap:
        roadmap = GeneratedRoadmap.model_validate_json(extract_json(raw))
        roadmap = _validate_and_repair_roadmap(roadmap, gap_analysis, job_title)
        if not roadmap.nodes:
            raise ValueError("Roadmap has no valid LACK nodes after validation")
        return roadmap

    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)

    try:
        return _parse_and_validate(raw)
    except Exception as first_exc:
        print(f"[RETRY] roadmap_generator: first attempt failed ({first_exc!r}), retrying")
        try:
            result = crew.kickoff()
            raw = result.raw if hasattr(result, "raw") else str(result)
            return _parse_and_validate(raw)
        except Exception as retry_exc:
            print(f"[FALLBACK] roadmap_generator: AI failed after retry ({retry_exc!r}), using rule-based fallback")
            return _fallback_roadmap_generator(gap_analysis, job_title)
