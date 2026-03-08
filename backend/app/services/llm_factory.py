"""
LLM factory — returns the configured chat model (CrewAI LLM).

Switch provider via LLM_PROVIDER env var:
  LLM_PROVIDER=openai   → uses OpenAI gpt-4o-mini (requires OPENAI_API_KEY)
  LLM_PROVIDER=ollama   → uses local Ollama (requires OLLAMA_BASE_URL + OLLAMA_MODEL)

Always call get_llm() at runtime inside a function, never at module level.
"""

from crewai import LLM

from app.core.config import settings


def get_llm(max_tokens: int = 4096) -> LLM:
    if settings.LLM_PROVIDER == "ollama":
        return LLM(
            model=f"ollama/{settings.OLLAMA_MODEL}",
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
            max_tokens=min(max_tokens, 8192),
        )

    # Default: OpenAI
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file, or set LLM_PROVIDER=ollama to use a local model."
        )
    return LLM(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.1,
        max_tokens=max_tokens,
    )
