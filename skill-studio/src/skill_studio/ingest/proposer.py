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

The bundle now includes structured session activity:
- agents: subagent calls with descriptions, types, and prompt snippets
- skills: skill invocations observed during the session
- tool_sequence: ordered list of all tool calls with descriptions
- tool_frequency: how often each tool was used
- workflow_patterns: repeated tool sequences (potential automatable workflows)

Use these signals to infer capabilities, inputs, and scenarios. For example:
- Agent calls reveal delegation patterns and multi-step orchestration
- Skill calls show existing automations the user relies on
- Workflow patterns (repeated tool sequences) suggest automatable workflows
- Tool frequency reveals the user's primary interaction patterns

Rules:
- Every proposed value must cite which signal it came from in the "rationale" map.
- If the bundle is empty/thin, propose {} — do not invent.
- cost_today: only fill if total_cost_usd > 0 or the transcript clearly complains about cost.
- scenarios: derive from agent calls, workflow patterns, or iterations — not a single turn.
- capabilities: derive from agent descriptions, skill calls, and tool sequences.

Output format (valid JSON only, no prose):
{
  "patch": { <partial DesignJSON> },
  "rationale": { "<field.path>": "<which signal(s) justified this>" },
  "skill_proposals": [
    {
      "name": "suggested-skill-name",
      "description": "what this skill would do",
      "trigger": "when to invoke it",
      "workflow": ["tool1", "tool2", "tool3"],
      "source_signals": ["which bundle fields support this proposal"]
    }
  ]
}

skill_proposals: If the session reveals repeatable multi-step workflows (from \
workflow_patterns, agent orchestration, or repeated skill+tool sequences), \
propose them as potential new skills. Only propose when the evidence is strong — \
at least 2 occurrences of a pattern or a clear agent orchestration flow. \
If no strong patterns exist, return an empty list.
"""


def _extract_json(raw: str) -> dict | None:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def _compact_bundle(bundle: Bundle) -> dict:
    """Trim the bundle to fit in a single LLM prompt without losing signal."""
    d = bundle.to_dict()
    if len(d.get("tool_sequence", [])) > 30:
        d["tool_sequence"] = d["tool_sequence"][:15] + [{"tool": "...", "description": f"({len(d['tool_sequence']) - 30} more)"}] + d["tool_sequence"][-15:]
    for agent in d.get("agents", []):
        if len(agent.get("prompt_snippet", "")) > 150:
            agent["prompt_snippet"] = agent["prompt_snippet"][:150] + "..."
    return d


def propose(bundle: Bundle, llm: LLMProvider, max_tokens: int = 1500) -> tuple[dict, dict]:
    """Run the LLM once over the compact bundle. Returns (patch, rationale).

    On any failure (bad JSON, LLM error), returns ({}, {}) — caller falls back
    to starting the interview without a seed.
    """
    body = json.dumps(_compact_bundle(bundle), indent=2)
    try:
        raw = llm.ask(
            history=[
                {"role": "user", "content": f"{PROPOSE_PROMPT}\n\nBundle:\n{body}"},
            ],
            max_tokens=max_tokens,
        )
    except Exception:
        return {}, {}

    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        return {}, {}

    patch = parsed.get("patch") or {}
    rationale = parsed.get("rationale") or {}
    if parsed.get("skill_proposals"):
        rationale["_skill_proposals"] = parsed["skill_proposals"]
    return patch, rationale
