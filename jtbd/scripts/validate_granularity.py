"""Granularity Gate validator — pattern-based heuristic scorer.

Scores a draft JTBD JSON on five dimensions (0-2 each).
Any dimension at 0 blocks save until rewrite.
See references/granularity_fixes.md for rewrite prompts.
"""

import json
import re
import sys


GENERIC_ACTORS = {
    "user", "users", "people", "person", "someone", "everyone",
    "customer", "customers", "anybody", "they", "them",
}

ALWAYS_WORDS = {
    "always", "in general", "whenever", "all the time", "every time",
    "usually", "often", "sometimes",
}

VAGUE_WORKAROUNDS = {
    "nothing", "none", "they don't", "various tools", "various",
    "whatever they have", "different things", "a few things",
}

VAGUE_OUTCOMES = {
    "better", "improved", "more efficient", "good", "great",
    "faster", "easier", "smoother", "nicer", "enhanced",
}


def score_actor(text):
    if not text:
        return 0
    tokens = text.lower().strip().split()
    non_filler = [t for t in tokens if t not in {"the", "a", "an", "some", "all", "any"}]
    if not non_filler:
        return 0
    if len(non_filler) <= 2 and non_filler[0] in GENERIC_ACTORS:
        return 0
    if any(t in GENERIC_ACTORS for t in non_filler) and len(non_filler) <= 3:
        return 1
    if len(non_filler) >= 4:
        return 2
    return 1


def score_context(text):
    if not text:
        return 0
    lower = text.lower().strip()
    if any(w in lower for w in ALWAYS_WORDS):
        return 0
    if re.search(r"when\s+\w+", lower) or re.search(r"after\s+\w+", lower):
        if len(lower.split()) >= 8:
            return 2
        return 1
    if len(lower.split()) < 5:
        return 0
    return 1


def score_workaround(text):
    if not text:
        return 0
    lower = text.lower().strip()
    for phrase in VAGUE_WORKAROUNDS:
        if lower == phrase or lower.startswith(phrase):
            return 0
    if any(char in text for char in ["→", "->", "then", "paste", "copy", "manually"]):
        return 2
    if len(text.split()) >= 6:
        return 1
    return 0


def score_outcome(text):
    if not text:
        return 0
    lower = text.lower().strip()
    for phrase in VAGUE_OUTCOMES:
        if lower == phrase or (lower.startswith(phrase) and len(lower.split()) <= 3):
            return 0
    if re.search(r"\d+", text):
        return 2
    if any(w in lower for w in ["half", "double", "reduce", "cut", "increase", "decrease", "from", "under"]):
        return 1
    if len(text.split()) >= 6:
        return 1
    return 0


def score_evidence(quotes):
    if not quotes:
        return 0
    if isinstance(quotes, list) and len(quotes) == 0:
        return 0
    if isinstance(quotes, list):
        has_attribution = any("—" in q or " - " in q or "said" in q.lower() for q in quotes)
        has_verbatim = any(q.startswith('"') or q.startswith("'") or q.startswith("“") for q in quotes)
        if has_attribution and has_verbatim:
            return 2
        return 1
    return 0


def validate(data):
    situation = data.get("jtbd", {}).get("situation", "")
    outcome = data.get("jtbd", {}).get("outcome", "")
    workaround = data.get("problem", {}).get("what_hurts", "")
    quotes = data.get("evidence", {}).get("quotes", [])
    actor = situation.split(",")[0] if situation else ""

    scores = {
        "actor_specificity": score_actor(actor),
        "context_trigger": score_context(situation),
        "current_workaround": score_workaround(workaround),
        "measurable_outcome": score_outcome(outcome),
        "evidence_quote": score_evidence(quotes),
    }

    total = sum(scores.values())
    blocking = [k for k, v in scores.items() if v == 0]

    return {
        "scores": scores,
        "total": total,
        "max": 10,
        "blocking": blocking,
        "passes": len(blocking) == 0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_granularity.py <path-to-jtbd.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    result = validate(data)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passes"] else 1)
