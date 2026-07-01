#!/usr/bin/env python3
"""Deterministic autonomy-ladder decision tree: yes/no facts -> a rung (composite).

The LLM gathers the facts about the constraint-relieving automation; this script
picks the rung, so recommendations are consistent. It separates two questions —
WHAT KIND of automation (work shape) and HOW IT IS TRIGGERED / hardened — and
composes them, so "unattended timing" or "must never fail" are honored as
modifiers instead of silently dropped.

Usage (booleans; omit = false):
  recommend_rung.py --bounded-outcome
  recommend_rung.py --recurring --fixed-steps --unattended-timing
  recommend_rung.py --streaming-input --fixed-steps
  recommend_rung.py --embedded --reliability-critical
  recommend_rung.py --json '{"recurring": true, "fixed_steps": true}'

Outputs JSON: {rung, base, modifiers, rationale, also_consider, facts}.
"""
import argparse
import json

FACTS = [
    "bounded_outcome",      # can describe + verify the end-state
    "recurring",            # the same task repeats
    "streaming_input",      # new work arrives over time
    "fixed_steps",          # steps are deterministic/repeatable
    "unattended_timing",    # must run at set times, no one watching
    "embedded",             # must live inside an app / be always-on
    "reliability_critical", # must never silently fail
]


def base_rung(f):
    """WHAT KIND of automation — the work shape."""
    if f["embedded"]:
        return ("Agent SDK",
                "Needs embedded/always-on capacity inside an app or pipeline — a real service.")
    if f["fixed_steps"] and (f["recurring"] or f["streaming_input"]):
        return ("Workflow (agent authors deterministic steps)",
                "Repeatable process with fixed steps — have an agent solve it once and emit deterministic, "
                "auditable, re-runnable steps instead of paying for an LLM every run.")
    if f["streaming_input"]:
        return ("Loop",
                "New work keeps arriving and must be handled as it lands, and the steps aren't fixed yet.")
    if f["recurring"]:
        return ("Skill",
                "A repeated task you keep re-explaining — package it as a reusable skill.")
    if f["bounded_outcome"]:
        return ("Goal",
                "A bounded outcome you can describe and verify — one autonomous Goal run. The default first build.")
    return ("Goal (default)",
            "No higher-commitment trigger met — start with a single Goal aimed at the constraint and climb only if it proves insufficient.")


def compose(f):
    base, rationale = base_rung(f)
    modifiers = []
    also = []

    # Trigger: unattended timing is a hard requirement, not a footnote.
    if f["unattended_timing"]:
        if base == "Loop":
            # a continuous loop and a clock-trigger are alternatives; prefer the schedule.
            base = "Scheduled runs (/schedule)"
            rationale = ("Must run unattended at set times — schedule discrete runs rather than hold a "
                         "continuous loop open. Skills run via /schedule, not via loop.")
            if f["fixed_steps"]:
                also.append("If steps are fixed, have the scheduled job run a deterministic workflow.")
        elif base.startswith("Agent SDK"):
            also.append("An always-on SDK service may not need /schedule; add it only for periodic jobs inside the service.")
        else:
            modifiers.append("triggered by /schedule (-> cron / launchd)")

    # Hardening: reliability is the substrate, applied on top of whatever runs.
    if f["reliability_critical"]:
        modifiers.append("under durable execution (Temporal)")
        rationale += " Must never silently fail, so run it on durable, retrying, stateful execution."

    rung = base + ((" " + ", ".join(modifiers)) if modifiers else "")

    # Cross-checks / nudges
    if base.startswith("Loop") and f["fixed_steps"]:
        also.append("Steps look fixed: prefer a deterministic workflow over a token-hungry LLM loop.")
    if base.startswith("Agent SDK") and not (f["embedded"]):
        also.append("Confirm a lighter rung can't relieve the constraint before committing to a service.")
    if base == "Skill":
        also.append("Build the underlying action as a Goal first, then extract the skill.")
    if base == "Goal (default)":
        also.append("If you can't state a verifiable end-state yet, the constraint isn't ready to automate — exploit/subordinate first.")

    return {"rung": rung, "base": base, "modifiers": modifiers,
            "rationale": rationale, "also_consider": also, "facts": f}


def main():
    ap = argparse.ArgumentParser(description="Pick a composite autonomy-ladder rung.")
    for fact in FACTS:
        ap.add_argument("--" + fact.replace("_", "-"), action="store_true")
    ap.add_argument("--json", help="JSON object of facts (overrides flags)")
    args = ap.parse_args()
    if args.json:
        try:
            data = json.loads(args.json)
            if not isinstance(data, dict):
                raise TypeError("--json must be a JSON object of facts")
        except Exception as e:
            print(json.dumps({"error": f"bad --json: {e}"})); return
        f = {k: bool(data.get(k, False)) for k in FACTS}
    else:
        f = {k: getattr(args, k) for k in FACTS}
    print(json.dumps(compose(f), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
