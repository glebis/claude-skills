#!/usr/bin/env python3
"""
vision-bench: Evaluate and compare images using vision LLMs as judges.

Usage:
  python bench.py img1.png img2.png --criteria text_to_image --prompt "a cat in space"
  python bench.py img1.png --criteria document_ocr --judge gemini-2.0-flash
  python bench.py img1.png img2.png --judges gpt-4o gemini-2.0-flash claude-opus-4-5-20251022
"""
import argparse
import sys
from pathlib import Path

import yaml

from judge import score_images
from report import generate_report

CRITERIA_DIR = Path(__file__).parent / "criteria"


def list_presets() -> list[str]:
    return [p.stem for p in sorted(CRITERIA_DIR.glob("*.yaml"))]


def load_criteria(name: str) -> dict:
    path = Path(name) if (name.endswith(".yaml") or name.endswith(".yml")) else CRITERIA_DIR / f"{name}.yaml"
    if not path.exists():
        print(f"Criteria not found: {name}")
        print(f"Available presets: {', '.join(list_presets())}")
        sys.exit(1)
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Score images with vision LLM judges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available presets: {', '.join(list_presets())}"
    )
    parser.add_argument("images", nargs="*", help="Image paths to evaluate")
    parser.add_argument("--criteria", "-c", default="text_to_image",
                        help="Preset name or path to .yaml file (default: text_to_image)")
    parser.add_argument("--judge", "-j", default="gemini-2.5-flash",
                        help="Single judge model")
    parser.add_argument("--judges", nargs="+",
                        help="Multiple judge models for consensus scoring (overrides --judge)")
    parser.add_argument("--prompt", "-p", help="Original generation prompt (used for prompt_adherence)")
    parser.add_argument("--output", "-o", choices=["markdown", "json", "table"], default="markdown")
    parser.add_argument("--save", "-s", help="Save report to file")
    parser.add_argument("--list-presets", action="store_true", help="List available presets and exit")
    args = parser.parse_args()

    if args.list_presets:
        for p in list_presets():
            criteria = load_criteria(p)
            print(f"  {p:<25} {criteria.get('description', '')}")
        return

    criteria = load_criteria(args.criteria)
    judges = args.judges or [args.judge]

    print(f"Evaluating {len(args.images)} image(s) with {len(judges)} judge(s)...", file=sys.stderr)

    results = score_images(args.images, criteria, judges, args.prompt)
    report = generate_report(results, criteria, args.output)

    if args.save:
        Path(args.save).write_text(report)
        print(f"Report saved to {args.save}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
