"""
Crew service — JSON extraction utility and agent pipeline orchestration.
Full pipeline + background task + DB persistence are added in Step 10.
"""

import json
import re


def extract_json(raw_output: object) -> str:
    """
    Strip markdown code fences and extraneous text from an LLM response,
    returning a clean JSON string.

    Handles patterns like:
      ```json\n{...}\n```
      ```\n{...}\n```
      plain {...} or [...]
    """
    text = str(raw_output).strip()

    # Try to pull out a fenced block first
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
        return text

    # No fence — try to find the first {...} or [...] span
    obj_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if obj_match:
        return obj_match.group(1).strip()

    return text


def parse_with_retry(model_class, raw: str, agent_fn, *args, **kwargs):
    """
    Attempt to parse raw LLM output as model_class.
    On failure, re-run agent_fn(*args, **kwargs) once more.
    Raises ValueError on second failure.
    """
    try:
        return model_class.model_validate_json(extract_json(raw))
    except Exception as first_err:
        # Retry
        try:
            raw2 = agent_fn(*args, **kwargs)
            return model_class.model_validate_json(extract_json(raw2))
        except Exception:
            raise ValueError(
                f"Agent returned invalid JSON after 2 attempts. "
                f"First error: {first_err}"
            ) from first_err
