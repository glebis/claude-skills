#!/usr/bin/env python3
"""Convert an authored session JSON into a target transcript format.

Reads a session JSON (the scaffold with its `turns` array filled in by the model) and renders it to
`fathom`, `plain`, `markdown`, or `json` (pass-through). The synthetic watermark is re-emitted in
every target so it can never be dropped during conversion.

Usage:
    python3 convert_format.py --in /tmp/session.json --to markdown --auto-timestamps
    python3 convert_format.py --in /tmp/session.json --to fathom --out /tmp/session.txt
"""
import argparse
import json
import sys

from _common import (WATERMARK, validate_session, emulate_timestamps, frontmatter,
                     positive_int, SessionError, write_text, run_cli)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise SessionError(f"file not found: {path}")
    except (OSError, ValueError) as e:  # ValueError: JSON decode / bad UTF-8 / oversized ints
        raise SessionError(f"could not parse JSON ({e})")
    spec, turns = validate_session(data)  # raises SessionError on bad shape
    if not turns:
        print("WARNING: 'turns' is empty — rendering a watermark-only document.", file=sys.stderr)
    return data


def _label(turn, spec):
    sp = (turn.get("speaker") or "").strip()
    low = sp.lower()
    if low in ("practitioner", "coach", "therapist"):
        return spec.get("practitioner_label", "Practitioner")
    if low == "client":
        return spec.get("client_label", "Client")
    return sp or "Speaker"


def to_fathom(data):
    spec = data["spec"]
    lines = [f"# {WATERMARK}", ""]
    for t in data["turns"]:
        ts = t.get("timestamp") or "00:00"
        lines.append(f"[{ts}] {_label(t, spec)}: {t.get('text','')}")
    return "\n".join(lines) + "\n"


def to_plain(data):
    spec = data["spec"]
    lines = [f"<!-- {WATERMARK} -->", ""]
    for t in data["turns"]:
        lines.append(f"{_label(t, spec)}: {t.get('text','')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def to_markdown(data):
    spec = data["spec"]
    out = [
        frontmatter([
            ("persona", spec.get("persona", "")),
            ("modality", spec.get("modality", "")),
            ("session_position", spec.get("session_position", "")),
            ("language", spec.get("language", "")),
            ("synthetic", True),
            ("not_clinical_advice", True),
        ]),
        "",
        f"> {WATERMARK}",
        "",
        f"# Session — {spec.get('persona','')} ({spec.get('modality','')})",
        "",
    ]
    for t in data["turns"]:
        ts = t.get("timestamp")
        prefix = f"`{ts}` " if ts else ""
        out.append(f"**{_label(t, spec)}:** {prefix}{t.get('text','')}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def to_json(data):
    # Pass-through: emit the (validated, possibly re-timestamped) session JSON.
    # Enforce the mandatory watermark/flags so the JSON target can never lose provenance.
    data["watermark"] = WATERMARK
    data["synthetic"] = True
    data["not_clinical_advice"] = True
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


RENDERERS = {"fathom": to_fathom, "plain": to_plain, "markdown": to_markdown, "json": to_json}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--in", dest="inp", required=True, help="authored session JSON")
    p.add_argument("--to", required=True, choices=sorted(RENDERERS), help="target format")
    p.add_argument("--out", help="output path (default: stdout)")
    p.add_argument("--auto-timestamps", action="store_true",
                   help="recompute timestamps from turn length instead of using authored ones")
    p.add_argument("--wpm", type=positive_int, default=150, help="speaking rate for --auto-timestamps")
    args = p.parse_args()

    try:
        data = load(args.inp)
    except SessionError as e:
        print(f"ERROR: invalid session JSON — {e}", file=sys.stderr)
        sys.exit(2)

    if args.auto_timestamps:
        emulate_timestamps(data["turns"], wpm=args.wpm)
    rendered = RENDERERS[args.to](data)

    if args.out:
        write_text(args.out, rendered)
        print(f"Wrote {args.to}: {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)


if __name__ == "__main__":
    run_cli(main)
