"""Finding 2: Fold extractor + director landing check into a single LLM call.

Each user turn previously made 2 sequential LLM calls:
  1. extract_and_apply  — extract schema fields from transcript tail
  2. _subject_landed    — decide if current subject has been addressed

This module collapses them into one call that returns both signals at once,
cutting per-turn LLM latency in half in voice mode.
"""
from __future__ import annotations
import json
from skill_studio.schema import DesignJSON
from skill_studio.interview.subjects import Subject
from skill_studio.interview.merge import deep_merge


COMBINED_PROMPT = """\
You are an AI interview assistant. Given recent interview exchanges and the \
current landing criterion, perform two tasks at once and return a single JSON \
object with exactly two keys:

1. "landed": true if the user's latest answer satisfies the landing criterion, \
false otherwise.
2. "patch": a partial DesignJSON object containing only fields the transcript \
actually fills — or an empty object {} if nothing concrete was said.

Respond with ONLY valid JSON. No commentary. No markdown fences. Example:
{"landed": true, "patch": {"hook": "Weekly review drafter"}}
"""


def analyze_turn(
    design: DesignJSON,
    subject: Subject | None,
    transcript_tail: list[dict],
    llm,
) -> tuple[bool, dict]:
    """Single LLM call: decide if subject landed AND extract schema patch.

    Returns (landed: bool, patch: dict).
    Falls back to (False, {}) on any parse or network error.
    """
    landing_criterion = subject.landing_criterion if subject else "always true"
    context = "\n".join(f"{t['role']}: {t['text']}" for t in transcript_tail[-6:])
    user_msg = (
        f"{COMBINED_PROMPT}\n\n"
        f"Landing criterion: {landing_criterion}\n\n"
        f"Recent exchanges:\n{context}\n\n"
        f"JSON:"
    )
    try:
        raw = llm.ask(history=[{"role": "user", "content": user_msg}], max_tokens=900)
    except Exception:
        return False, {}

    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return False, {}
    try:
        result = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return False, {}

    landed = bool(result.get("landed", False))
    patch = result.get("patch", {})
    if not isinstance(patch, dict):
        patch = {}

    if patch:
        deep_merge(design, patch)

    return landed, patch
