"""
Smoke-test the LLM connection.

Usage:
    cd backend
    python scripts/test_llm.py

Tests whichever provider is set in .env (LLM_PROVIDER=openai|ollama).
Expects the LLM to respond with valid JSON containing {"ok": true}.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.services.llm_factory import get_llm

PROMPT = (
    "Respond with exactly this JSON and nothing else — no markdown, no explanation:\n"
    '{"ok": true}'
)


def main() -> None:
    print(f"Provider : {settings.LLM_PROVIDER}")
    if settings.LLM_PROVIDER == "openai":
        print(f"Model    : gpt-4o-mini")
    else:
        print(f"Model    : {settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL}")

    print("Sending test prompt...")
    llm = get_llm()
    response = llm.invoke(PROMPT)
    raw = response.content if hasattr(response, "content") else str(response)
    print(f"Raw response: {raw!r}")

    # Strip possible markdown fences
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1].lstrip("json").strip() if len(parts) >= 3 else text

    data = json.loads(text)
    assert data.get("ok") is True, f"Expected {{\"ok\": true}}, got: {data}"
    print("LLM smoke test PASSED")


if __name__ == "__main__":
    main()
