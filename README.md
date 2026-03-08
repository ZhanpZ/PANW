# Design Document

[https://github.com/ZhanpZ/PANW/blob/main/DESIGN.md]DESIGN.md

# Skill-Bridge Career Navigator

**Candidate Name:** Zhanping Zeng

**Scenario Chosen:** Skill-Bridge Career Navigator

**Estimated Time Spent:** 1–2 hours planning; 2 hours coding; 0.5 hours misc.

---

## Quick Start

### Prerequisites

- Python 3.10+ with `pip`
- Node.js 18+ with `npm`
- **OpenAI** (default): an OpenAI API key (`sk-...`)
- **Ollama** (local, no API key): [install Ollama](https://ollama.com/download), then run `ollama pull llama3.2`

### Run Commands

```bash
# 1. Configure environment
cd backend
cp .env.example .env
# Open backend/.env and set OPENAI_API_KEY (or set LLM_PROVIDER=ollama)

# 2. Start the backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs

# 3. Start the frontend (new terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Test Commands

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Generate synthetic test fixtures
cd backend
python scripts/generate_synthetic_data.py --count 5 --output fixtures/

# Full agent pipeline test
python scripts/test_crew_full.py
```

---

## AI Disclosure

**Did you use an AI assistant (Copilot, ChatGPT, etc.)?**: Yes (Claude Code, Gemini)

**How did you verify the suggestions?**: I verified suggestions by running the actual test commands specified in each build step.

**Give one example of a suggestion you rejected or changed:** Claude initially suggested a "MAYBE" mastery level, but this was too ambiguous for the user and made it harder to set up the fallback. I updated the Pydantic schema to enforce a stricter rule, ensuring skills are only classified as "DONE" or "LACK".

---

## Tradeoffs & Prioritization

**What did you cut to stay within the 4–6 hour limit?**: I dropped several planned features to ensure the core functionality was working. These include: uploading proof of work, letting the agent decide on mastery level based on proof of work, adding spaced repetition, and having a confidence score percentage.

**What would you build next if you had more time?**: I would work on the proof-of-work functionality and the features that depend on it.

**Known limitations**: Currently this is single-user and runs locally. Another limitation is that the agent/LLM produces non-deterministic output across runs — the same person might be recommended JavaScript and its ecosystem in one session, but Python and its ecosystem in another if the previous session was accidentally deleted and they start fresh.
