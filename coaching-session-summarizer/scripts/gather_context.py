#!/usr/bin/env python3
"""
Gather context for agent-driven session analysis (no API calls).

Prints everything the agent needs to analyze a coaching/therapy session:
  - the transcript text (summary + transcript, summaries excluded)
  - up to 3 previous sessions with the same participant (paths)
  - the list of available trails (for linking)

The agent (Claude Code) reads this output, performs the analysis itself, and
appends the result to the transcript file with Edit. This keeps the whole
workflow on the subscription — no Anthropic API key, no billing.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def load_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[1], parts[2]
    return "", content


def extract_transcript_only(body):
    """Transcript + Summary sections, but drop any prior AI-Generated Summary."""
    body = re.split(r"\n## AI-Generated Summary", body, maxsplit=1)[0]
    return body.strip()


def get_previous_sessions(vault_path, current_session, participant_name):
    vault = Path(vault_path)
    pattern = f"*{participant_name.lower().replace(' ', '-')}*.md"
    sessions = []
    for f in vault.glob(pattern):
        stem = f.stem
        if f.name != current_session and (
            "coaching" in stem or "therapy" in stem or "session" in stem
        ):
            sessions.append(f)
    sessions.sort(key=lambda x: x.stem[:8] if x.stem[:8].isdigit() else "0")
    return sessions[-3:]


def find_trails(vault_path):
    trails_dir = Path(vault_path) / "Trails"
    if not trails_dir.exists():
        return []
    return sorted(
        t.stem.replace("Trail - ", "") for t in trails_dir.glob("Trail*.md")
    )


def main():
    ap = argparse.ArgumentParser(description="Gather context for agent-driven analysis")
    ap.add_argument("transcript_file")
    ap.add_argument("--vault", default=os.path.expanduser("~/Brains/brain"))
    ap.add_argument(
        "--participant",
        default="",
        help="Participant name for previous-session lookup (e.g. 'gleb-kalinin'). "
        "Falls back to the filename's name segment.",
    )
    args = ap.parse_args()

    path = Path(args.transcript_file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    frontmatter, body = load_transcript(path)
    transcript = extract_transcript_only(body)

    participant = args.participant
    if not participant:
        # Heuristic: strip leading YYYYMMDD- and trailing -<sessiontype> from stem.
        stem = re.sub(r"^\d{8}-", "", path.stem)
        stem = re.sub(r"-(coaching|therapy|session|call|meeting|workshop)$", "", stem)
        participant = stem

    prev = get_previous_sessions(args.vault, path.name, participant)
    trails = find_trails(args.vault)

    print("=" * 70)
    print("PREVIOUS SESSIONS (read these for cross-session pattern detection):")
    if prev:
        for p in prev:
            print(f"  - {p}")
    else:
        print("  (none found)")
    print()
    print("AVAILABLE TRAILS (link 2-4 most relevant):")
    print("  " + ", ".join(trails) if trails else "  (none found)")
    print("=" * 70)
    print()
    print("SESSION CONTENT TO ANALYZE:")
    print()
    print(transcript)


if __name__ == "__main__":
    main()
