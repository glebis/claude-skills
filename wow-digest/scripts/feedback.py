#!/usr/bin/env python3
"""Collect human feedback on WOW digest items for eval gold set."""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

EVAL_DIR = Path(__file__).parent.parent / ".wow-eval"


def record_feedback(selected_path, verdicts):
    """Append feedback entries to feedback.jsonl.

    verdicts: list of dicts with keys: title, verdict, reason (optional)
    verdict values: "wow", "meh", "noise", "already_knew"
    """
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    feedback_path = EVAL_DIR / "feedback.jsonl"

    with open(selected_path) as f:
        selected = json.load(f)

    with open(feedback_path, "a") as f:
        for item, verdict_info in zip(selected, verdicts):
            entry = {
                "timestamp": datetime.now().isoformat(),
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "source_type": item.get("source_type", ""),
                "wow_score_llm": item.get("wow_score", 0),
                "wow_score_human": verdict_info.get("score"),
                "verdict": verdict_info.get("verdict", ""),
                "reason": verdict_info.get("reason", ""),
                "challenged_assumption": item.get("challenged_assumption", ""),
                "hook": item.get("hook", ""),
            }
            f.write(json.dumps(entry) + "\n")

    count = sum(1 for _ in open(feedback_path))
    print(f"Feedback recorded. Total entries: {count}", file=sys.stderr)
    if count >= 50:
        print("Gold set ready for prompt sweep (50+ entries).", file=sys.stderr)


def show_stats():
    """Print feedback statistics."""
    feedback_path = EVAL_DIR / "feedback.jsonl"
    if not feedback_path.exists():
        print("No feedback collected yet.")
        return

    entries = [json.loads(line) for line in open(feedback_path)]
    verdicts = {}
    for e in entries:
        v = e.get("verdict", "unknown")
        verdicts[v] = verdicts.get(v, 0) + 1

    print(f"Total entries: {len(entries)}")
    for v, count in sorted(verdicts.items()):
        print(f"  {v}: {count}")

    if entries:
        llm_scores = [e["wow_score_llm"] for e in entries if e.get("wow_score_llm")]
        wow_items = [e for e in entries if e["verdict"] == "wow"]
        if llm_scores:
            print(f"  Avg LLM score (all): {sum(llm_scores)/len(llm_scores):.1f}")
        if wow_items:
            wow_llm = [e["wow_score_llm"] for e in wow_items if e.get("wow_score_llm")]
            if wow_llm:
                print(f"  Avg LLM score (wow only): {sum(wow_llm)/len(wow_llm):.1f}")


def main():
    parser = argparse.ArgumentParser(description="WOW digest feedback")
    sub = parser.add_subparsers(dest="command")

    record = sub.add_parser("record", help="Record feedback from JSON")
    record.add_argument("--selected", required=True, help="Path to selected items JSON")
    record.add_argument("--verdicts", required=True, help="Path to verdicts JSON")

    sub.add_parser("stats", help="Show feedback statistics")

    args = parser.parse_args()

    if args.command == "record":
        with open(args.verdicts) as f:
            verdicts = json.load(f)
        record_feedback(args.selected, verdicts)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
