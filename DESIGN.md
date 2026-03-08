# Skill-Bridge Career Navigator — Design Documentation

## 1. Overview

Skill-Bridge is a career navigation platform that transforms a user's resume and GitHub history into a personalized, interactive learning roadmap. Given a target job title, an AI pipeline analyzes the candidate's current skills, compares them against real job requirements, and renders the resulting skill graph as an interactive DAG (Directed Acyclic Graph) in the browser.

**Core idea:** surface exactly what you're missing (LACK) and what you already have (DONE), then point you to curated resources for each gap — all in one session-persistent workspace.

---

## 2. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | Fast HMR, type safety, modern ecosystem |
| Visualization | `@xyflow/react` v12 | Production-grade zoomable DAG, node customization |
| Global State | Zustand | Minimal boilerplate, selector-based re-renders |
| Styling | Tailwind CSS | Utility-first, no CSS file sprawl |
| Backend | FastAPI + Pydantic v2 | Async-ready, auto-docs, strict schema validation |
| AI Orchestration | CrewAI + LangChain | Multi-agent task decomposition, retry logic |
| LLM Primary | OpenAI `gpt-4o-mini` | Cost-efficient, fast, strong instruction-following |
| LLM Fallback | Ollama (local) | Offline operation, no API cost |
| Database | SQLite + SQLAlchemy ORM | Zero-config persistence, portable single file |
| HTTP Client | Axios | Typed request/response, interceptor support |

---

## 3. Architecture

```
Browser                           Backend                          LLM
──────────────────────────────    ─────────────────────────────    ──────────
HomePage                          FastAPI (main.py)
  ├─ SessionSidebar               ├─ /api/v1/sessions
  └─ InputForm (resume/GitHub)    ├─ /api/v1/roadmap/generate ──→  Agent Pipeline
        │                         │     BackgroundTask              │
        │  POST /roadmap/generate │                                 ├─ ResumeParserAgent
        └─────────────────────────┤                                 ├─ JobRequirementsAgent (parallel)
                                  │  poll every 2s                  ├─ GapAnalyzerAgent
RoadmapPage ←─────────────────────┤ /api/v1/roadmap/job/{id}       └─ RoadmapGeneratorAgent
  ├─ RoadmapCanvas                │                                        │
  │   └─ SkillNode (green/red)    │  /api/v1/roadmap/{id}  ←──────────────┘
  └─ NodeDetailPanel              │  /api/v1/roadmap/node/{id}   (PATCH mastery)
      ├─ ResourceList             └─ /api/v1/uploads/{node_id}
      └─ ProofUpload
```

### 3.1 Request Lifecycle

1. User submits resume text, GitHub summaries, and target job title.
2. Backend creates a `Profile` + `Roadmap` record (status: `pending`) and immediately returns a `job_id`.
3. A FastAPI `BackgroundTask` runs the 4-agent pipeline asynchronously.
4. Frontend polls `GET /api/v1/roadmap/job/{job_id}` every 2 seconds.
5. On `complete`, the full roadmap is fetched and rendered as a React Flow canvas.

---

## 4. Database Schema

Six SQLAlchemy ORM models with cascade deletes:

```
sessions       id, name, created_at, updated_at
profiles       id, session_id→sessions, resume_text, github_summaries, job_title
roadmaps       id, session_id→sessions, profile_id→profiles, status(pending|processing|complete|failed), error_message
skill_nodes    id, roadmap_id→roadmaps, skill_name, mastery_level(DONE|LACK), category,
               description, estimated_hours, position_x, position_y,
               parent_id→skill_nodes (self-ref DAG), reasoning
resources      id, skill_node_id→skill_nodes, title, url, resource_type(free|paid), platform
proof_uploads  id, skill_node_id→skill_nodes, filename, filepath, uploaded_at, notes
```

**Key design choices:**
- `MasteryLevel` is a strict two-value enum — no "MAYBE" or "PARTIAL" states.
- `parent_id` is a self-referential FK enabling the skill dependency graph.
- `position_x/y` are computed server-side (topological BFS layout with category-grid fallback) so the client can render immediately without layout computation.

---

## 5. AI Agent Pipeline

All four agents use `get_llm()` at call time (never at module level) to support both OpenAI and Ollama providers without import-time side effects.

```
Input
 │
 ├──[parallel]──────────────────────────────────────┐
 │                                                   │
 ▼                                                   ▼
ResumeParserAgent                         JobRequirementsAgent
Parses resume text + GitHub summaries     Generates 15–25 required skills
into a structured ParsedProfile.          for the target job title.
 │                                                   │
 └───────────────────┬───────────────────────────────┘
                     ▼
             GapAnalyzerAgent
             Classifies every job-requirement skill as
             DONE or LACK against the candidate profile.
             Includes rule-based fallback on LLM failure.
                     │
                     ▼
          RoadmapGeneratorAgent
          Produces ordered skill nodes with parent_skill
          dependencies, estimated hours, and ≥1 free +
          ≥1 paid resource per node.
                     │
                     ▼
              DB Persistence
              Two-pass insert: nodes first (get IDs),
              then resolve parent_id references.
```

### Resilience Strategy

| Layer | Mechanism |
|---|---|
| JSON parsing | `extract_json()` strips markdown fences, falls back to regex extraction |
| Agent output | Retry once on Pydantic validation failure |
| Gap analysis | Rule-based keyword fallback if AI fails after retry |
| Mastery coercion | Invalid values coerced to LACK; missing skills added as LACK |
| Roadmap status | `failed` status + `error_message` stored in DB on unrecoverable error |

---

## 6. Frontend Component Map

```
App.tsx (React Router)
├── HomePage
│   ├── SessionSidebar       — list, create, delete sessions
│   └── InputForm            — resume textarea, GitHub textarea, job title
└── RoadmapPage
    ├── Loading overlay      — cycling status text during polling
    ├── RoadmapCanvas        — @xyflow/react DAG, zoom/pan, MiniMap
    │   ├── SkillNode        — green (DONE) / red (LACK) custom node
    │   ├── OffscreenArrows  — directional nudge buttons when nodes go off-screen
    │   └── DirectionTracker — ReactFlow hook to detect off-screen nodes
    └── NodeDetailPanel      — slide-in drawer on node click
        ├── ResourceList     — free/paid learning links
        └── ProofUpload      — file upload + list, persists to backend
```

### State Management (Zustand)

| Store | Responsibility |
|---|---|
| `sessionStore` | Active session, session list, CRUD actions |
| `roadmapStore` | Current roadmap data, polling loop (2s interval), node mastery patch |
| `uiStore` | Toast queue, panel open/close state |

---

## 7. API Reference

```
GET    /api/v1/health
GET    /api/v1/sessions
POST   /api/v1/sessions                  {name}
DELETE /api/v1/sessions/{id}

POST   /api/v1/roadmap/generate          GenerateRoadmapRequest → {job_id, status}
GET    /api/v1/roadmap/job/{job_id}      → {job_id, status, error_message}
GET    /api/v1/roadmap/session/{sid}     → latest complete Roadmap for session
GET    /api/v1/roadmap/{id}              → full Roadmap + skill_nodes + resources
PATCH  /api/v1/roadmap/node/{id}         {mastery_level} → updates DB + returns new value

POST   /api/v1/uploads/{node_id}         multipart/form-data → ProofUpload
GET    /api/v1/uploads/{node_id}         → ProofUpload[]
DELETE /api/v1/uploads/{upload_id}       → removes file from disk + DB
```

---

## 8. Node Layout Algorithm

The server computes `position_x` / `position_y` using a two-tier strategy:

1. **Topological BFS layout** — nodes are placed by dependency depth (level on Y-axis), siblings spread evenly on X-axis. Used when the DAG has meaningful hierarchy (< 50% of nodes at root level).
2. **Category-grid fallback** — when the graph is flat (most nodes have no parent), nodes are arranged in category columns. Each category gets a column; nodes stack vertically within it.

Constants: `NODE_W=220`, `NODE_H=80`, `H_GAP=60–80`, `V_GAP=40–120`.

---

## 9. Security & Configuration

- CORS origins controlled via `CORS_ORIGINS` env var (comma-separated list).
- All uploads stored under `backend/uploads/` (gitignored), served only via authenticated routes.
- `OPENAI_API_KEY` loaded from `.env` via `pydantic-settings`; never committed.
- `LLM_PROVIDER=ollama` env var switches the entire pipeline to local inference.
- Global exception handler returns generic 500 to clients; full stack trace logged server-side only.

---

## 10. Local Development

### 10.1 OpenAI (default)

**Step 1 — Copy and configure `.env`**
```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and set the following:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...          # ← paste your real OpenAI API key here

# Leave these at their defaults:
DATABASE_URL=sqlite:///./data/skillbridge.db
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
CORS_ORIGINS=http://localhost:5173
```

**Step 2 — Start the backend**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

**Step 3 — Start the frontend**
```bash
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

---

### 10.2 Ollama (local, no API key required)

**Step 1 — Install Ollama**

Download and install from [https://ollama.com/download](https://ollama.com/download) for your OS.
Verify installation:
```bash
ollama --version
```

**Step 2 — Pull a model**

The default model is `llama3.2`. Pull it before starting the app:
```bash
ollama pull llama3.2
```

Other supported options (update `OLLAMA_MODEL` in `.env` to match):
```bash
ollama pull mistral        # faster, lower RAM (~4 GB)
ollama pull llama3.1       # larger context window
ollama pull qwen2.5:7b     # strong at structured JSON output
```

**Step 3 — Start the Ollama server**

Ollama runs as a background server on port `11434`. On macOS/Linux it starts automatically after install. On Windows, launch the Ollama app from the system tray, or run:
```bash
ollama serve
# → listening on http://localhost:11434
```

Verify it is running:
```bash
curl http://localhost:11434/api/tags
# should return a JSON list of your pulled models
```

**Step 4 — Configure `backend/.env` for Ollama**

```bash
cd backend
cp .env.example .env
```

Open `backend/.env` and set:
```env
LLM_PROVIDER=ollama                        # ← switch from openai to ollama
OPENAI_API_KEY=                            # ← leave blank, not needed

OLLAMA_BASE_URL=http://localhost:11434     # ← default Ollama port
OLLAMA_MODEL=llama3.2                      # ← must match the model you pulled

# Leave these at their defaults:
DATABASE_URL=sqlite:///./data/skillbridge.db
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
CORS_ORIGINS=http://localhost:5173
```

> **Note:** If you pulled a different model (e.g. `mistral`), set `OLLAMA_MODEL=mistral` to match exactly.

**Step 5 — Start the backend**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

**Step 6 — Start the frontend**
```bash
cd ../frontend
npm install
npm run dev
# → http://localhost:5173
```

**Step 7 — Verify Ollama is being used**

After submitting a roadmap request, check the backend terminal. You should see CrewAI log lines referencing `ollama/llama3.2` (or whichever model you configured) instead of `gpt-4o-mini`.

> **Performance note:** Local models are slower than OpenAI. A full roadmap generation may take 2–5 minutes depending on your hardware. The 2-second polling loop on the frontend will keep waiting — no timeout.

---

### 10.3 `.env` Quick Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | Yes | `openai` | `openai` or `ollama` |
| `OPENAI_API_KEY` | If `openai` | — | Your OpenAI secret key (`sk-...`) |
| `OLLAMA_BASE_URL` | If `ollama` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | If `ollama` | `llama3.2` | Must match a model you have pulled |
| `DATABASE_URL` | No | `sqlite:///./data/skillbridge.db` | SQLite file path (relative to `backend/`) |
| `UPLOAD_DIR` | No | `./uploads` | Directory for proof-of-work file storage |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Max file size for uploads |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated allowed frontend origins |

---

### 10.4 Test Fixtures

Generate 5 synthetic career profiles for end-to-end testing:
```bash
python scripts/generate_synthetic_data.py --count 5 --output fixtures/
```

---

## 11. Future Enhancements

### Near-Term (Second Iteration)

| Feature | Description |
|---|---|
| **Codebase zip upload** | Accept a `.zip` of source code; infer skills from language/framework usage |
| **Confidence score decay** | Mastery confidence decays over time; DONE skills revert to review-needed state |
| **Spaced repetition reminders** | SM-2 algorithm + `next_review_at` field; daily digest email or in-app badge |
| **Non-CS job abstractions** | Configurable skill taxonomy for non-engineering roles (PM, design, data science) |

### Medium-Term

| Feature | Description |
|---|---|
| **Progress analytics** | Track LACK→DONE transitions over time; visualize learning velocity |
| **Resource ratings** | User-submitted ratings per resource; surface highest-rated first |
| **Collaborative sessions** | Share a read-only roadmap URL with a mentor or recruiter |
| **Export to PDF / Markdown** | Print-friendly roadmap for offline review or portfolio |

### Long-Term

| Feature | Description |
|---|---|
| **Multi-LLM routing** | Route to GPT-4o for complex analysis, Haiku for simple tasks; cost optimization |
| **Real job listing integration** | Pull live requirements from LinkedIn/Indeed APIs instead of LLM-generated job specs |
| **Skill verification badges** | OAuth integration with GitHub, Coursera, LinkedIn Learning to auto-verify DONE status |

---

## 12. Known Limitations & Trade-offs

| Limitation | Context |
|---|---|
| SQLite concurrency | SQLite is suitable for single-user local use; production would require PostgreSQL |
| Blocking background tasks | FastAPI `BackgroundTasks` runs in the same process; heavy LLM calls block worker threads under concurrent load |
| No authentication | Sessions are identified by integer IDs with no auth; all data is local and single-tenant by design |
| LLM non-determinism | Agent outputs vary between runs; the same resume+job may produce different roadmaps |
