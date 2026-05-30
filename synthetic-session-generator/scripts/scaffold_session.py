#!/usr/bin/env python3
"""Scaffold a synthetic coaching/therapy session skeleton.

Turns a generation spec (modality, persona, session position, length/duration, language, format)
into a structured JSON skeleton with phases, a beat list, a turn budget, an empty turn array for the
model to fill, and the mandatory synthetic watermark. The model authors the actual dialogue into the
`turns` array; this script only builds the guardrails.

Defaults for modality / language / duration come from setup_config.py (config.json). Precedence:
explicit CLI flag > config value > built-in default.

Usage:
    python3 scaffold_session.py --modality cbt --persona maya --position mid-arc \
        --length standard --format json --out /tmp/session_skeleton.json
"""
import argparse
import json
import sys

from _common import (WATERMARK, LANGUAGES, MODALITIES, load_config, duration_to_length,
                     allocate_turns, positive_int, write_text, run_cli)

MODALITY_META = {
    "icf-grow": {"practitioner": "Coach",
                 "phases": ["check-in", "goal", "reality", "options", "will", "close"]},
    "cbt": {"practitioner": "Therapist",
            "phases": ["check-in", "agenda", "homework-review", "main-work", "new-homework", "summary"]},
    "ifs": {"practitioner": "Therapist",
            "phases": ["check-in", "find-target-part", "unblend", "befriend-part", "integration", "close"]},
    "act-mi": {"practitioner": "Practitioner",
               "phases": ["check-in", "evoke-values", "explore-ambivalence", "defusion", "commit", "summary"]},
}

POSITIONS = {"intake", "early", "mid-arc", "breakthrough", "rupture-and-repair", "closing"}
LENGTHS = {"short": 15, "standard": 30, "long": 50}
FORMATS = {"fathom", "plain", "json", "markdown"}


def resolve_turn_budget(length, duration, config):
    """Apply precedence: explicit --duration > explicit --length > config duration > default length."""
    if duration is not None:
        turns, bucket = duration_to_length(duration)
        return turns, bucket, duration
    if length is not None:
        return LENGTHS[length], length, None
    cfg_duration = config.get("duration_minutes")
    if isinstance(cfg_duration, int) and cfg_duration > 0:
        turns, bucket = duration_to_length(cfg_duration)
        return turns, bucket, cfg_duration
    return LENGTHS["standard"], "standard", None


def build_skeleton(modality, persona, position, length, duration, fmt, language, config):
    m = MODALITY_META[modality]
    phases = m["phases"]
    turn_budget, bucket, duration_used = resolve_turn_budget(length, duration, config)

    weights = [1] * len(phases)
    for i in range(1, len(phases) - 1):
        weights[i] = 2
    targets = allocate_turns(weights, turn_budget)
    beats = [{"phase": p, "target_turns": tt, "notes": ""} for p, tt in zip(phases, targets)]

    return {
        "watermark": WATERMARK,
        "synthetic": True,
        "not_clinical_advice": True,
        "spec": {
            "modality": modality,
            "practitioner_label": m["practitioner"],
            "client_label": "Client",
            "persona": persona,
            "session_position": position,
            "length": bucket,
            "format": fmt,
            "turn_budget": turn_budget,
            "language": language,
            "language_name": LANGUAGES.get(language, language),
            "duration_minutes": duration_used,
        },
        "beats": beats,
        "turns": [],  # model fills: [{speaker, timestamp, text, technique, emotion, phase}, ...]
        "ground_truth": {
            "themes": [],
            "action_items": [],
            "techniques_used": [],
            "emotional_arc": "",
        },
    }


def main():
    cfg = load_config()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modality", default=cfg["modality"], choices=sorted(MODALITIES),
                   help="default from setup config")
    p.add_argument("--persona", required=True, help="persona id from references/personas.md")
    p.add_argument("--position", required=True, choices=sorted(POSITIONS))
    # length/duration default to None so we can detect whether the user passed them explicitly.
    p.add_argument("--length", default=None, choices=sorted(LENGTHS),
                   help="coarse length; overridden by --duration")
    p.add_argument("--duration", type=positive_int, default=None,
                   help="session minutes; overrides --length and config (e.g. 25/50/80)")
    p.add_argument("--language", default=cfg["language"], choices=sorted(LANGUAGES),
                   help="output language (default from setup config)")
    p.add_argument("--format", dest="fmt", default="json", choices=sorted(FORMATS))
    p.add_argument("--out", help="output path (default: stdout)")
    args = p.parse_args()

    skeleton = build_skeleton(args.modality, args.persona, args.position, args.length,
                              args.duration, args.fmt, args.language, cfg)
    payload = json.dumps(skeleton, ensure_ascii=False, indent=2)
    sp = skeleton["spec"]
    if args.out:
        write_text(args.out, payload + "\n")
        print(f"Wrote skeleton: {args.out}", file=sys.stderr)
        print(f"  modality={sp['modality']} persona={sp['persona']} position={sp['session_position']} "
              f"language={sp['language_name']} length={sp['length']} (~{sp['turn_budget']} turns) "
              f"format={args.fmt}", file=sys.stderr)
        print(f"Author the dialogue in {sp['language_name']} into 'turns', then run convert_format.py.",
              file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    run_cli(main)
