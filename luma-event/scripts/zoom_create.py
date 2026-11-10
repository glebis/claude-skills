#!/usr/bin/env python3
"""Create the Zoom meeting and store its join URL without printing the passcode.

  zoom_create.py "Title" 2026-11-11 18:00 [--duration 90] [--out FILE]

The join URL carries the passcode (?pwd=...). It goes to --out (default:
$TMPDIR/luma-zoom-join.txt) and is printed masked, so it never lands in a
transcript. Paste it into Lu.ma with `agent-browser keyboard type "$(cat FILE)"`.
Prints: meeting id, masked join URL, the file path.
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

ZOOM = Path.home() / ".claude/skills/zoom/scripts/zoom_meetings.py"


def run(*args):
    r = subprocess.run([sys.executable, str(ZOOM), *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"zoom script failed: {r.stderr.strip()[:300]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("time", help="HH:MM, Europe/Berlin")
    ap.add_argument("--duration", type=int, default=90)
    ap.add_argument("--out", type=Path, default=Path(os.environ.get("TMPDIR", "/tmp")) / "luma-zoom-join.txt")
    a = ap.parse_args()

    created = run("create", a.title, "--start", f"{a.date}T{a.time}:00",
                  "--duration", str(a.duration), "--timezone", "Europe/Berlin")
    m = re.search(r"\*\*ID:\*\*\s*(\d+)", created)
    if not m:
        sys.exit("no meeting ID in Zoom output")
    mid = m.group(1)
    # `create` output shows the host start URL; the join URL comes from `get`.
    details = run("get", mid)
    j = re.search(r"https://[a-z0-9.]*zoom\.us/j/[^\s)*]+", details)
    if not j:
        sys.exit(f"meeting {mid} created but no join URL found; run: zoom_meetings.py get {mid}")
    a.out.write_text(j.group(0))
    a.out.chmod(0o600)
    print(f"meeting_id={mid}")
    print("join_url=" + re.sub(r"pwd=.*", "pwd=…", j.group(0)))
    print(f"join_url_file={a.out}")


if __name__ == "__main__":
    main()
