#!/usr/bin/env python3
"""Setup mode — persist default generation settings for the skill.

Writes a `config.json` next to the skill so later `scaffold_session.py` runs inherit defaults for
language, modality, and session duration without re-specifying them. Run this when the user wants to
configure the skill ("setup", "set my defaults", "always use Russian / CBT / 50-minute sessions").

Usage:
    python3 setup_config.py --language ru --modality cbt --duration 50
    python3 setup_config.py --show          # print current config (no writes)
    python3 setup_config.py --reset         # restore built-in defaults
"""
import argparse
import json
import sys

from _common import (LANGUAGES, MODALITIES, DEFAULTS, load_config, save_config,
                     duration_to_length, positive_int, run_cli)


def describe(cfg):
    turns, bucket = duration_to_length(cfg["duration_minutes"])
    return {
        "language": f"{cfg['language']} ({LANGUAGES.get(cfg['language'], cfg['language'])})",
        "modality": cfg["modality"],
        "duration_minutes": cfg["duration_minutes"],
        "derived_turn_budget": turns,
        "derived_length": bucket,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--language", choices=sorted(LANGUAGES), help="default output language")
    p.add_argument("--modality", choices=MODALITIES, help="default modality")
    p.add_argument("--duration", type=positive_int, help="default session minutes (e.g. 25/50/80)")
    p.add_argument("--show", action="store_true", help="print current config without modifying it")
    p.add_argument("--reset", action="store_true", help="restore built-in defaults")
    args = p.parse_args()

    # --show is read-only: print and exit, no writes (unless combined with changes/reset).
    will_change = bool(args.language or args.modality or args.duration or args.reset)
    if args.show and not will_change:
        print(json.dumps(describe(load_config()), ensure_ascii=False, indent=2))
        return

    cfg = dict(DEFAULTS) if args.reset else load_config()
    if args.language:
        cfg["language"] = args.language
    if args.modality:
        cfg["modality"] = args.modality
    if args.duration:
        cfg["duration_minutes"] = args.duration

    save_config(cfg)
    print(f"Saved config → config.json", file=sys.stderr)
    print(json.dumps(describe(cfg), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_cli(main)
