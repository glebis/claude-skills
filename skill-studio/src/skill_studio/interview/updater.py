from __future__ import annotations
import json
from skill_studio.schema import DesignJSON
from skill_studio.interview.merge import deep_merge


EXTRACTION_PROMPT = """Given the user's latest answer, extract any fields from the DesignJSON schema that it fills. Output ONLY valid JSON matching the schema's partial shape (only include fields the answer actually addresses, no others). Don't hallucinate."""


def apply_answer(design: DesignJSON, target: str, answer: str, llm) -> None:
    user_msg = (
        f"{EXTRACTION_PROMPT}\n\n"
        f"Target field we were asking about: {target}\n"
        f"User's answer: \"{answer}\"\n\n"
        f"JSON (partial):"
    )
    raw = llm.ask(history=[{"role": "user", "content": user_msg}], max_tokens=800)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        return
    try:
        patch = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return
    deep_merge(design, patch)


# Backward-compatible alias
_deep_merge = deep_merge
