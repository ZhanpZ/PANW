"""
LLM factory — returns the configured chat model.

Switch provider via LLM_PROVIDER env var:
  LLM_PROVIDER=openai   → uses OpenAI gpt-4o-mini (requires OPENAI_API_KEY)
  LLM_PROVIDER=ollama   → uses local Ollama (requires OLLAMA_BASE_URL + OLLAMA_MODEL)

Always call get_llm() at runtime inside a function, never at module level.
"""

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


def get_llm() -> BaseChatModel:
    if settings.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
        )

    # Default: OpenAI
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Add it to your .env file, or set LLM_PROVIDER=ollama to use a local model."
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,  # type: ignore[arg-type]
        temperature=0.1,
    )
