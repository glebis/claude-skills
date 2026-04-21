from __future__ import annotations
from typing import Any
from skill_studio.schema import DesignJSON
from skill_studio.presets import Preset


def _get(obj: Any, path: str) -> Any:
    """Walk dotted path on a pydantic model or dict."""
    cur: Any = obj
    for part in path.split("."):
        if hasattr(cur, part):
            cur = getattr(cur, part)
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def _flatten_weights(weights: dict[str, Any], prefix: str = "") -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in weights.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten_weights(v, full))
        else:
            out[full] = float(v)
    return out


def score_coverage(design: DesignJSON) -> dict[str, float]:
    """Return per-field confidence 0..1. Simple v1 heuristic."""
    scores: dict[str, float] = {}
    checkable = [
        "hook", "problem.what_hurts", "problem.cost_today",
        "jtbd.situation", "jtbd.motivation", "jtbd.outcome",
        "before_after.before_external", "before_after.before_internal",
        "before_after.after_external",  "before_after.after_internal",
        "cta",
        "trigger.detail",
    ]
    for path in checkable:
        val = _get(design, path)
        scores[path] = 1.0 if (isinstance(val, str) and val.strip()) else 0.0
    list_targets = {
        "needs.functional": 2, "needs.emotional": 1, "needs.social": 1,
        "inputs": 2, "capabilities": 2, "outputs": 1, "guardrails": 1,
        "scenarios": 1,
    }
    for path, target in list_targets.items():
        val = _get(design, path) or []
        scores[path] = min(1.0, len(val) / target)
    scores["concept_imagery.metaphor"] = 1.0 if (design.concept_imagery.metaphor or "").strip() else 0.0

    # Aggregate top-level scores so presets that weight a whole submodel (e.g.
    # `before_after: 0.7`) get credited once its nested fields are filled.
    def _group_mean(prefix: str) -> float:
        sub = [v for k, v in scores.items() if k.startswith(f"{prefix}.")]
        return sum(sub) / len(sub) if sub else 0.0

    for group in ("before_after", "problem", "jtbd", "trigger", "concept_imagery"):
        scores.setdefault(group, _group_mean(group))
    return scores


def overall_coverage(design: DesignJSON, preset: Preset) -> float:
    scores = score_coverage(design)
    weights = _flatten_weights(preset.field_weights)
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    weighted = sum(scores.get(k, 0.0) * w for k, w in weights.items())
    return weighted / total_weight


def next_uncovered_field(design: DesignJSON, preset: Preset) -> str | None:
    scores = score_coverage(design)
    weights = _flatten_weights(preset.field_weights)
    candidates = [(k, w * (1.0 - scores.get(k, 0.0))) for k, w in weights.items()]
    candidates.sort(key=lambda kv: kv[1], reverse=True)
    for k, gain in candidates:
        if gain > 0.01:
            return k
    return None
