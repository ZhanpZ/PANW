"""
Generate synthetic resume + GitHub summary fixtures for testing.

Usage:
    python scripts/generate_synthetic_data.py --count 5 --output fixtures/

Outputs per profile:
  fixtures/fixture_N_resume.json  →  { "resume_text": str, "job_title": str }
  fixtures/fixture_N_github.json  →  { "github_summaries": str }
"""

import argparse
import json
import os
import random

# ──────────────────────────────────────────────────────────────────────────────
# Profile templates
# Each entry: (label, job_title, resume_fn, github_fn)
# ──────────────────────────────────────────────────────────────────────────────

FIRST_NAMES = ["Alex", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Drew", "Avery"]
LAST_NAMES  = ["Kim", "Patel", "Rivera", "Chen", "Okonkwo", "Müller", "Nguyen", "Santos"]
UNIVERSITIES = [
    "State University", "City College", "Tech Institute",
    "Northern University", "Pacific College", "Midwest Tech",
]
COMPANIES = [
    "DataCorp", "WebWorks LLC", "BioSoft Inc", "RetailPlus",
    "FinEdge", "HealthBytes", "StartupIO", "MediaGroup",
]

rng = random.Random(42)  # deterministic output


def fake_name() -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def fake_univ() -> str:
    return rng.choice(UNIVERSITIES)


def fake_company() -> str:
    return rng.choice(COMPANIES)


# ──────────────────────────────────────────────────────────────────────────────
# Profile 0 — CS grad → Cloud Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_cs_to_cloud() -> dict:
    name = fake_name()
    univ = fake_univ()
    company = fake_company()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com | LinkedIn: linkedin.com/in/{name.lower().replace(' ', '-')}

EDUCATION
B.S. Computer Science — {univ}, May 2023
GPA: 3.6/4.0 | Relevant coursework: Data Structures, Algorithms, Operating Systems, Computer Networks

EXPERIENCE
Software Engineering Intern — {company} (Jun 2022 – Aug 2022)
• Built REST APIs in Python/Django handling 10,000+ daily requests
• Wrote unit tests with pytest achieving 85% code coverage
• Contributed to internal tooling using PostgreSQL and Redis

Teaching Assistant — {univ} CS Department (Sep 2021 – May 2023)
• Held weekly office hours for 60 students in intro programming courses
• Graded assignments and provided feedback on Python projects

SKILLS
Languages: Python, Java, JavaScript, SQL
Frameworks: Django, Flask, React (basic)
Tools: Git, GitHub, VS Code, Linux (Ubuntu), PostgreSQL
Concepts: REST APIs, OOP, basic networking (TCP/IP), relational databases

PROJECTS
Movie Recommendation System: Built a collaborative filtering recommender using Python/pandas,
deployed on a local Flask server. Achieved 78% accuracy on test set.

Campus Event Scheduler: Django web app for managing university events with user authentication,
SQLite database, and Bootstrap frontend.
"""

    github = """\
Repository: movie-recommender
Description: Collaborative filtering movie recommendation engine
Tech: Python, pandas, scikit-learn, Flask
• Implemented user-based and item-based collaborative filtering algorithms
• REST API serving recommendations as JSON with Flask
• Achieved 78% hit rate on MovieLens 1M dataset

Repository: campus-scheduler
Description: University event management web application
Tech: Python, Django, SQLite, Bootstrap
• User authentication, role-based access (admin/student)
• CRUD operations for events with calendar view
• Deployed locally with Django development server
"""
    return (
        {"resume_text": resume.strip(), "job_title": "Cloud Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Profile 1 — Data Analyst → Data Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_analyst_to_dataeng() -> dict:
    name = fake_name()
    univ = fake_univ()
    company = fake_company()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com

EDUCATION
B.S. Statistics — {univ}, May 2021

EXPERIENCE
Data Analyst — {company} (Aug 2021 – Present)
• Created dashboards in Tableau and Power BI for executive reporting
• Wrote complex SQL queries against Oracle and MySQL databases (10+ table joins)
• Automated weekly Excel reports using Python (openpyxl, pandas)
• Collaborated with data science team to clean datasets for ML models

SKILLS
Languages: SQL, Python (pandas, numpy, openpyxl), R (basic)
Visualization: Tableau, Power BI, Excel
Databases: MySQL, Oracle, basic PostgreSQL
Other: Git, JIRA, Confluence

PROJECTS
Sales Trend Analysis: Built automated ETL pipeline in Python pulling from MySQL,
transforming data with pandas, outputting to Excel dashboards.

Customer Churn Study: R/ggplot2 analysis on 50K customer records identifying
top 5 predictors of churn for marketing team.
"""

    github = """\
Repository: sales-etl
Description: Automated ETL pipeline for sales trend analysis
Tech: Python, pandas, MySQL, openpyxl
• Extracts data from MySQL via SQLAlchemy connection
• Applies cleaning and aggregation transformations with pandas
• Outputs formatted Excel reports on a weekly schedule

Repository: churn-analysis
Description: Statistical churn analysis and visualization
Tech: R, ggplot2, dplyr
• Logistic regression model predicting customer churn (AUC 0.81)
• Visual reports generated with R Markdown
"""
    return (
        {"resume_text": resume.strip(), "job_title": "Data Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Profile 2 — Frontend Dev → Full Stack Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_frontend_to_fullstack() -> dict:
    name = fake_name()
    univ = fake_univ()
    company = fake_company()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com | Portfolio: {name.lower().replace(' ', '')}.dev

EDUCATION
B.A. Web Design & Interactive Media — {univ}, Dec 2020

EXPERIENCE
Frontend Developer — {company} (Jan 2021 – Present)
• Built responsive UIs with React 17/18, TypeScript, and Tailwind CSS
• Integrated REST APIs via Axios; managed state with Redux Toolkit
• Worked with designers to implement pixel-perfect Figma mockups
• Set up CI/CD pipelines for the frontend with GitHub Actions

SKILLS
Languages: JavaScript (ES2022), TypeScript, HTML5, CSS3
Frameworks: React, Vue.js (basic)
Tools: Vite, Webpack, ESLint, Prettier, Figma, Git
APIs: REST (consumer), basic GraphQL queries
Testing: Jest, React Testing Library

PROJECTS
Portfolio Site: Personal site built with React + Vite + Tailwind,
deployed on Vercel. 95 Lighthouse performance score.

Component Library: Storybook-based internal component library with 30+
reusable React components and full accessibility support.
"""

    github = """\
Repository: portfolio-site
Description: Personal portfolio built with React + Vite + Tailwind
Tech: React, TypeScript, Tailwind CSS, Vite
• Responsive layout with mobile-first design
• Dark/light mode toggle using CSS variables
• Deployed on Vercel with automatic preview deployments

Repository: component-lib
Description: Internal UI component library
Tech: React, TypeScript, Storybook
• 30+ reusable components (Button, Modal, Table, Form inputs)
• Accessibility-first (ARIA, keyboard navigation)
• Jest + RTL unit tests for all components
"""
    return (
        {"resume_text": resume.strip(), "job_title": "Full Stack Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Profile 3 — Bootcamp Grad → Backend Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_bootcamp_to_backend() -> dict:
    name = fake_name()
    company = fake_company()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com

EDUCATION
Full-Stack Web Development Bootcamp — Code Academy Online, Aug 2023 (16 weeks)
Prior: B.A. English Literature — Liberal Arts College, May 2020

EXPERIENCE
Junior Web Developer (Contract) — {company} (Oct 2023 – Present)
• Built CRUD features in Node.js/Express with MongoDB
• Created React frontends consuming internal REST APIs
• Wrote basic unit tests with Jest
• Fixed bugs and added features under senior developer mentorship

SKILLS
Languages: JavaScript, HTML, CSS, some Python
Backend: Node.js, Express.js
Frontend: React (hooks, functional components), basic Redux
Databases: MongoDB, basic SQL (SQLite)
Tools: Git, Postman, VS Code, basic Linux commands

PROJECTS
Todo API: RESTful API built with Express.js and MongoDB Atlas,
deployed on Heroku with basic JWT authentication.

Blog Platform: Full-stack app with React frontend, Node/Express backend,
MongoDB database. Users can register, post, and comment.
"""

    github = """\
Repository: todo-api
Description: RESTful todo API with authentication
Tech: Node.js, Express, MongoDB, JWT
• CRUD endpoints for tasks with user authentication
• JWT-based auth with bcrypt password hashing
• Deployed to Heroku with MongoDB Atlas cloud DB

Repository: blog-platform
Description: Full-stack blog application
Tech: React, Node.js, Express, MongoDB
• User registration and login (JWT)
• Rich text post creation and commenting system
• Basic CI with GitHub Actions
"""
    return (
        {"resume_text": resume.strip(), "job_title": "Backend Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Profile 4 — Biology Grad → ML Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_biology_to_ml() -> dict:
    name = fake_name()
    univ = fake_univ()
    company = fake_company()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com

EDUCATION
M.S. Computational Biology — {univ}, May 2023
B.S. Biology — {univ}, May 2021
Thesis: "Predicting protein-ligand binding affinity using gradient boosted trees"

EXPERIENCE
Research Analyst — {company} Bioinformatics Lab (Jun 2023 – Present)
• Processed genomic datasets using Python (pandas, NumPy, BioPython)
• Built classification models with scikit-learn (Random Forest, XGBoost) for phenotype prediction
• Performed statistical analysis with R and SciPy; visualized results with Matplotlib/seaborn
• Managed lab computing on a shared Linux cluster (SLURM job scheduler)

SKILLS
Languages: Python, R, SQL (basic), bash scripting
Libraries: pandas, NumPy, scikit-learn, XGBoost, Matplotlib, seaborn, BioPython
Tools: Jupyter Notebooks, Git, Linux/bash, SLURM
ML: Supervised learning (classification, regression), cross-validation, feature engineering
Databases: PostgreSQL (basic reads), SQLite

PROJECTS
Protein Binding Predictor: XGBoost model achieving 0.89 AUC predicting drug-target binding.
Feature engineering from molecular descriptors with RDKit.

Gene Expression Clustering: Unsupervised K-means + hierarchical clustering on RNA-seq data
from 500 samples; visualized with PCA and t-SNE.
"""

    github = """\
Repository: protein-binding-predictor
Description: ML model for drug-target binding affinity prediction
Tech: Python, XGBoost, scikit-learn, RDKit, pandas
• Feature engineering from SMILES molecular strings using RDKit
• XGBoost classifier with Bayesian hyperparameter tuning (Optuna)
• Cross-validation achieving 0.89 AUC on held-out test set
• Jupyter notebooks with full experiment tracking

Repository: rna-seq-clustering
Description: Unsupervised clustering of gene expression data
Tech: Python, scikit-learn, matplotlib, seaborn
• K-means and hierarchical agglomerative clustering on RNA-seq counts
• PCA + t-SNE dimensionality reduction for visualization
• Differential expression analysis comparing cluster centroids
"""
    return (
        {"resume_text": resume.strip(), "job_title": "ML Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Profile 5 — New Grad (CS) → Software Engineer
# ──────────────────────────────────────────────────────────────────────────────

def profile_new_grad_to_swe() -> dict:
    name = fake_name()
    univ = fake_univ()
    resume = f"""\
{name}
Email: {name.lower().replace(' ', '.')}@email.com | GitHub: github.com/{name.lower().replace(' ', '')}

EDUCATION
B.S. Computer Science — {univ}, May 2026 (Expected)
GPA: 3.4/4.0 | Relevant coursework: Data Structures, Algorithms, Computer Organization,
Software Engineering, Database Systems, Discrete Math

EXPERIENCE
No full-time industry experience.

Class Project — E-Commerce Web App (Jan 2026 – Apr 2026)
• Team of 4; built a shopping cart app using React and a Node.js/Express backend
• Integrated a SQLite database for product and order storage
• Deployed on a free-tier Render instance for demo day

Hackathon — HackState 2025 (48 hours)
• Built a real-time chat app with WebSockets (Socket.io) and a Vue.js frontend
• Won "Best First-Time Hacker" award among 120 participants

SKILLS
Languages: Python, Java, C (intro-level), JavaScript, HTML, CSS
Frameworks: React (basic), Express.js (basic)
Tools: Git, VS Code, Linux terminal (basic), IntelliJ IDEA
Concepts: OOP, basic sorting/searching algorithms, relational schemas, REST APIs (consumer)

PROJECTS
Personal Portfolio: Static site built with HTML/CSS/JavaScript hosted on GitHub Pages.

Sorting Visualizer: React app animating bubble, merge, and quicksort algorithms
with adjustable speed control.
"""

    github = """\
Repository: sorting-visualizer
Description: Visual demo of sorting algorithms in React
Tech: React, JavaScript, CSS
• Animates bubble sort, merge sort, and quicksort step-by-step
• Adjustable speed slider and array size controls
• Deployed via GitHub Pages

Repository: ecommerce-project
Description: Full-stack e-commerce class project
Tech: React, Node.js, Express, SQLite
• Product listing, cart, and checkout flow
• Simple admin panel to add/remove products
• Deployed on Render (free tier)
"""
    return (
        {"resume_text": resume.strip(), "job_title": "Software Engineer"},
        {"github_summaries": github.strip()},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

PROFILES = [
    profile_cs_to_cloud,
    profile_analyst_to_dataeng,
    profile_frontend_to_fullstack,
    profile_bootcamp_to_backend,
    profile_biology_to_ml,
    profile_new_grad_to_swe,
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic fixture data")
    parser.add_argument("--count", type=int, default=6, help="Number of fixtures (max 6)")
    parser.add_argument("--output", type=str, default="fixtures/", help="Output directory")
    args = parser.parse_args()

    count = min(args.count, len(PROFILES))
    os.makedirs(args.output, exist_ok=True)

    for i in range(count):
        resume_data, github_data = PROFILES[i]()

        resume_path = os.path.join(args.output, f"fixture_{i}_resume.json")
        github_path = os.path.join(args.output, f"fixture_{i}_github.json")

        with open(resume_path, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)
        with open(github_path, "w", encoding="utf-8") as f:
            json.dump(github_data, f, indent=2, ensure_ascii=False)

        print(f"  [OK] {resume_path}  ({resume_data['job_title']})")
        print(f"  [OK] {github_path}")

    print(f"\nGenerated {count} fixture pair(s) in '{args.output}'")


if __name__ == "__main__":
    main()
