from __future__ import annotations
import json
from skill_studio.schema import DesignJSON
from skill_studio.interview.merge import deep_merge


EXTRACTION_PROMPT = """Given recent interview exchanges, extract any fields from the DesignJSON schema that they fill. Output ONLY valid JSON with fields the transcript actually addresses, no others. Don't hallucinate."""


def extract_and_apply(design: DesignJSON, transcript_tail: list[dict], llm) -> dict:
    """After each user turn, run extraction from transcript tail and merge into design.

    Returns the patch applied (empty dict if extraction produced nothing).
    """
    context = "\n".join(f"{t['role']}: {t['text']}" for t in transcript_tail[-6:])
    user_msg = (
        f"{EXTRACTION_PROMPT}\n\n"
        f"Recent exchanges:\n{context}\n\n"
        f"Partial JSON:"
    )
    try:
        raw = llm.ask(history=[{"role": "user", "content": user_msg}], max_tokens=800)
    except Exception:
        return {}
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        patch = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return {}
    deep_merge(design, patch)
    return patch


# Backward-compatible alias — existing tests import _deep_merge from extractor.
_deep_merge = deep_merge
