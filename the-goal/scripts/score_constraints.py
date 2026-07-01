#!/usr/bin/env python3
"""Deterministically rank candidate steps to find the binding constraint (Herbie).

The LLM elicits the qualitative picture and maps it to ordinal scores (0..3);
THIS script ranks, so the core diagnosis is repeatable rather than vibes. It
refuses to fake precision (too many unknowns -> "insufficient data") and it
enforces the TOC rule that throughput-sensitivity is *decisive*, not just heavy:
a step that wouldn't raise throughput if sped up cannot be the constraint.

Input: JSON (via --input FILE or stdin) — a list of candidate steps:
  [
    {
      "name": "Finish the sales offer",
      "throughput_sensitivity": 3,   # if 2x faster, would T rise? 0 no .. 3 strongly. DECISIVE.
      "wait_before": 2,              # work queued BEFORE this step (0..3)
      "downstream_starvation": 3,    # how much downstream starves on it (0..3)
      "capacity_gap": 2,             # demand vs capacity here (0..3)
      "policy_gate": false,          # a rule/approval gate rather than a work step
      "annoyance": 3                 # how annoying it FEELS (0..3) — only flags the annoying-but-non-binding trap
    }, ...
  ]
Any numeric field may be null/omitted = unknown. Out-of-range values are clamped.

Output: JSON ranking with verdict, winner, confidence and warnings. Exit 0 always.
"""
import argparse
import json
import sys

CORROBORATING = {           # evidence that the step caps the line
    "downstream_starvation": 2.0,
    "wait_before": 1.5,
    "capacity_gap": 1.5,
}
MAX_PER = 3
POLICY_BONUS = 1.0


def _ordinal(v):
    """Return a clamped 0..3 int, or None if not a usable number (bools rejected)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return max(0, min(MAX_PER, int(round(v))))


def score_step(step):
    sens = _ordinal(step.get("throughput_sensitivity"))
    present = 0
    total = 0.0
    max_total = 0.0
    for field, w in CORROBORATING.items():
        v = _ordinal(step.get(field))
        if v is not None:
            present += 1
            total += w * v
            max_total += w * MAX_PER
    if bool(step.get("policy_gate")):
        total += POLICY_BONUS * MAX_PER
        max_total += POLICY_BONUS * MAX_PER
        present += 1
    corroboration = (total / max_total) if max_total else 0.0
    # sensitivity gates the score: unknown -> 0.5 (can't confirm), 0 -> 0 (disqualified)
    gate = (sens / MAX_PER) if sens is not None else 0.5
    fields_known = present + (1 if sens is not None else 0)
    completeness = fields_known / (len(CORROBORATING) + 1)
    ann = _ordinal(step.get("annoyance"))
    nc = bool(step.get("necessary_condition"))
    # a necessary condition (must be adequate to function) is never a "trap"
    trap = (ann is not None and ann >= 2 and sens is not None and sens <= 1 and not nc)
    return {
        "name": str(step.get("name", "(unnamed)")),
        "score": round(gate * corroboration, 3),
        "sensitivity_known": sens is not None,
        "disqualified_zero_sensitivity": sens == 0,
        "necessary_condition": nc,
        "data_completeness": round(completeness, 2),
        "annoying_non_binding": trap,
    }


def rank(steps):
    valid = [s for s in steps if isinstance(s, dict)]
    skipped = len(steps) - len(valid)
    scored = sorted((score_step(s) for s in valid), key=lambda x: x["score"], reverse=True)
    warnings = []
    if skipped:
        warnings.append(f"{skipped} item(s) were not objects and were skipped.")
    if not scored:
        return {"verdict": "insufficient_data", "constraint": None, "ranking": [],
                "warnings": warnings + ["No valid candidate steps provided."]}

    avg_complete = sum(s["data_completeness"] for s in scored) / len(scored)
    top = scored[0]
    margin = top["score"] - scored[1]["score"] if len(scored) > 1 else top["score"]

    if avg_complete < 0.5:
        warnings.append("INSUFFICIENT DATA: over half the evidence is unknown. "
                        "Gather sensitivity/wait/starvation before trusting the ranking.")
    for s in scored:
        if s["data_completeness"] < 0.5:
            warnings.append(f"THIN EVIDENCE: '{s['name']}' is under-specified ({s['data_completeness']}); "
                            "its rank may be artificially low.")
    if not top["sensitivity_known"]:
        warnings.append(f"CONFIRM: throughput-sensitivity of the leader '{top['name']}' is unknown — "
                        "verify a 2x speed-up would actually raise throughput before committing.")
    if top["annoying_non_binding"]:
        warnings.append(f"TRAP: the leader '{top['name']}' looks annoying-but-non-binding (low sensitivity). "
                        "Re-check; do not automate a non-constraint.")
    for s in scored[1:]:
        if s["annoying_non_binding"]:
            warnings.append(f"TRAP: '{s['name']}' feels annoying but is not throughput-binding — do not automate it.")
    if top["disqualified_zero_sensitivity"]:
        warnings.append("All candidates have zero/low throughput-sensitivity: none is the constraint as scoped. "
                        "Widen scope or re-examine the goal.")

    if avg_complete < 0.5 or top["score"] == 0:
        verdict = "insufficient_data"
    elif (len(scored) > 1 and margin < 0.1) or not top["sensitivity_known"] or top["annoying_non_binding"]:
        verdict = "ambiguous"
    else:
        verdict = "constraint_found"
    # classify each step into a role with concrete advice
    for i, s in enumerate(scored):
        if i == 0 and verdict == "constraint_found":
            s["role"], s["advice"] = "constraint", "Add capacity here — this is Herbie."
        elif s["necessary_condition"]:
            s["role"] = "prerequisite"
            s["advice"] = "Bring to adequate, then subordinate; do not over-invest past 'done + works'."
            warnings.append(f"PREREQUISITE: '{s['name']}' must be adequate to function but is not the constraint — "
                            "finish it to adequate, then stop investing.")
        elif s["annoying_non_binding"]:
            s["role"], s["advice"] = "trap", "Leave alone — feels heavy but non-binding."
        else:
            s["role"], s["advice"] = "non_constraint", "Subordinate to the constraint."

    return {
        "verdict": verdict,
        "constraint": top["name"] if verdict == "constraint_found" else None,
        "margin": round(margin, 3),
        "ranking": scored,
        "warnings": warnings,
    }


def main():
    ap = argparse.ArgumentParser(description="Rank candidate steps to find the binding constraint.")
    ap.add_argument("--input", help="JSON file of candidate steps (default: stdin)")
    args = ap.parse_args()
    try:
        if args.input:
            with open(args.input, encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
        steps = json.loads(raw)
        assert isinstance(steps, list), "input must be a JSON list of steps"
    except Exception as e:
        print(json.dumps({"verdict": "error", "error": str(e)}))
        return
    print(json.dumps(rank(steps), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
