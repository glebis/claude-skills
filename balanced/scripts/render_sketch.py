#!/usr/bin/env python3
"""Render a balanced sketch (JSON) into a self-contained HTML page.

Usage:
    render_sketch.py <sketch.json> [-o <out.html>]

Input schema:
    {
      "statement": "the user's original words",           (optional)
      "claim":     "the statement, restated precisely",
      "holds":     ["supporting point", ...],             (0-3 lines each)
      "breaks":    ["assumption or counter-evidence", ...],
      "reframe":   ["sharper version of the claim", ...],
      "unknown":   ["uncertainty that decides it", ...],
      "net":       {"summary": "...", "confidence": 75, "action": "..."},
      "refs":      ["Author, Year, Title, Source, DOI", ...]  (optional)
    }

Any line may carry [n] tags that link to refs[n-1].
"""
import argparse
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "sketch-template.html"
PLACEHOLDER = "/*__SKETCH_DATA__*/null"
BRANCHES = ("holds", "breaks", "reframe", "unknown")
MAX_LINES = 3


def is_str_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate(data):
    errors = []
    if not isinstance(data.get("claim"), str) or not data["claim"].strip():
        errors.append("claim: required, non-empty string")
    for key in BRANCHES:
        lines = data.setdefault(key, [])
        if not is_str_list(lines):
            errors.append(f"{key}: must be a list of strings")
        elif len(lines) > MAX_LINES:
            errors.append(f"{key}: at most {MAX_LINES} lines, got {len(lines)}")
    net = data.get("net")
    if not isinstance(net, dict) or not isinstance(net.get("summary"), str):
        errors.append("net.summary: required string")
    else:
        conf = net.get("confidence")
        if conf is not None and not (isinstance(conf, (int, float)) and 0 <= conf <= 100):
            errors.append("net.confidence: number from 0 to 100")
    if not is_str_list(data.setdefault("refs", [])):
        errors.append("refs: must be a list of strings")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data", type=Path, help="sketch JSON file")
    parser.add_argument("-o", "--out", type=Path, help="output HTML (default: <data>.html)")
    args = parser.parse_args()

    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read {args.data}: {exc}")
    if not isinstance(data, dict):
        sys.exit("sketch data must be a JSON object")
    errors = validate(data)
    if errors:
        sys.exit("invalid sketch data:\n  " + "\n  ".join(errors))

    # "</" would let a value close the <script> tag early.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace(PLACEHOLDER, payload)

    out = args.out or args.data.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()
