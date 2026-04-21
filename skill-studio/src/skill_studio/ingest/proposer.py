"""Turn an ingest Bundle into a proposed DesignJSON patch (single LLM call).

Flow: Bundle (deterministic) -> proposer (one LLM call) -> partial JSON patch.
The patch is NOT applied; the caller must present it to the user for approval.
"""
from __future__ import annotations
import json
from typing import Protocol

from .transcript import Bundle


class LLMProvider(Protocol):
    def ask(self, history: list[dict], max_tokens: int = ...) -> str: ...


PROPOSE_PROMPT = """You are helping seed a JTBD interview from a compact bundle of signals \
extracted from a prior session. Propose initial values for the DesignJSON schema below, \
using ONLY what the signals support. When uncertain, leave the field empty — do not \
hallucinate. The user will review and approve/edit before anything is applied.

Schema (propose only fields the signals justify):
  hook (str), problem.what_hurts (str), problem.cost_today (str),
  jtbd.situation (str), jtbd.motivation (str), jtbd.outcome (str),
  scenarios (list of {title, vignette}),
  capabilities (list), inputs (list)

Rules:
- Every proposed value must cite which signal it came from (models_tried, pain_snippets, iterations, total_cost_usd, etc.) in the "rationale" map.
- If the bundle is empty/thin, propose {} — do not invent.
- cost_today: only fill if total_cost_usd > 0 or the transcript clearly complains about cost.
- scenarios: derive from prompt_change / iterations patterns, not from a single turn.

Output format (valid JSON only, no prose):
{
  "patch": { <partial DesignJSON> },
  "rationale": { "<field.path>": "<which signal(s) justified this>" }
}
"""


def propose(bundle: Bundle, llm: LLMProvider, max_tokens: int = 1200) -> tuple[dict, dict]:
    """Run the LLM once over the compact bundle. Returns (patch, rationale).

    On any failure (bad JSON, LLM error), returns ({}, {}) — caller falls back
    to starting the interview without a seed.
    """
    body = json.dumps(bundle.to_dict(), indent=2)
    try:
        raw = llm.ask(
            history=[
                {"role": "user", "content": f"{PROPOSE_PROMPT}\n\nBundle:\n{body}"},
            ],
            max_tokens=max_tokens,
        )
    except Exception:
        return {}, {}

    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {}, {}
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return {}, {}

    patch = parsed.get("patch") if isinstance(parsed, dict) else None
    rationale = parsed.get("rationale") if isinstance(parsed, dict) else None
    return (patch or {}), (rationale or {})
