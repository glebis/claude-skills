#!/usr/bin/env python3
"""Granola meeting notes CLI — Personal API, export to Obsidian."""

import json
import sys
import os
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

PUBLIC_API_BASE = "https://public-api.granola.ai/v1"
SOPS_ENV_PATH = os.path.expanduser("~/Brains/brain/.env.granola")


def _get_api_key():
    """Decrypt Personal API Key from sops-encrypted .env.granola."""
    try:
        result = subprocess.run(
            ["sops", "-d", SOPS_ENV_PATH],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                if line.startswith("GRANOLA_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("ERROR: Cannot decrypt Granola API key from", SOPS_ENV_PATH, file=sys.stderr)
    sys.exit(1)


def api_get(path, params=None):
    """GET request to Granola Personal API."""
    key = _get_api_key()
    url = f"{PUBLIC_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def format_time(iso_str):
    if not iso_str:
        return "?"
    try:
        return datetime.fromisoformat(iso_str).strftime("%H:%M")
    except (ValueError, TypeError):
        return "?"


def cmd_list(args):
    """List meetings via Personal API."""
    all_notes = []
    cursor = None

    while True:
        params = {}
        if cursor:
            params["cursor"] = cursor
        if args.after:
            params["created_after"] = args.after

        data = api_get("/notes", params if params else None)
        notes = data.get("notes", [])
        all_notes.extend(notes)

        if not args.all or not data.get("hasMore"):
            break
        cursor = data.get("cursor")
        if not cursor:
            break

    if args.format == "json":
        print(json.dumps({"notes": all_notes, "count": len(all_notes)}, ensure_ascii=False, indent=2))
    else:
        print(f"Found {len(all_notes)} notes:\n")
        for n in all_notes:
            date = n.get("created_at", "")[:10]
            title = n.get("title") or "(Untitled)"
            owner = n.get("owner", {}).get("name", "")
            nid = n.get("id", "")
            attendees = n.get("attendees", [])
            names = ", ".join(a.get("name", a.get("email", "")) for a in attendees[:4])
            att_str = f" with {names}" if names else ""
            print(f"  {date}  {title}{att_str}")
            print(f"    id: {nid}")


def cmd_show(args):
    """Show a single note with summary."""
    params = {"include": "transcript"} if args.transcript else None
    note = api_get(f"/notes/{args.note_id}", params)

    if args.format == "json":
        print(json.dumps(note, ensure_ascii=False, indent=2))
        return

    title = note.get("title") or "(Untitled)"
    date = note.get("created_at", "")[:10]
    owner = note.get("owner", {}).get("name", "")
    attendees = [a.get("name", a.get("email", "")) for a in note.get("attendees", [])]
    cal = note.get("calendar_event", {})

    print(f"# {title}")
    print(f"Date: {date}  Owner: {owner}")
    if cal:
        start = format_time(cal.get("start_time"))
        end = format_time(cal.get("end_time"))
        print(f"Time: {start}–{end}")
    if attendees:
        print(f"Attendees: {', '.join(attendees)}")
    print()

    summary = note.get("summary_markdown") or note.get("summary_text") or ""
    if summary:
        print("## Summary\n")
        print(summary)
        print()

    transcript = note.get("transcript")
    if transcript:
        print("## Transcript\n")
        for u in transcript:
            ts = format_time(u.get("start_time", ""))
            text = u.get("text", "").strip()
            speaker = u.get("speaker", {})
            source = speaker.get("source", "") if isinstance(speaker, dict) else ""
            label = speaker.get("diarization_label", "") if isinstance(speaker, dict) else ""
            tag = label or source or ""
            tag_str = f" [{tag}]" if tag else ""
            print(f"[{ts}]{tag_str} {text}")


def cmd_export(args):
    """Export note to Obsidian markdown (Fathom-compatible format)."""
    note = api_get(f"/notes/{args.note_id}", {"include": "transcript"})

    title = note.get("title") or "(Untitled)"
    note_id = note.get("id", "")
    created_at = note.get("created_at", "")
    date_short = created_at[:10].replace("-", "")
    date_dash = created_at[:10]
    owner = note.get("owner", {}).get("name", "")
    attendees = note.get("attendees", [])
    participant_names = []
    if owner:
        participant_names.append(owner)
    for a in attendees:
        name = a.get("name", a.get("email", ""))
        if name and name not in participant_names:
            participant_names.append(name)

    cal = note.get("calendar_event", {})
    start_time = cal.get("start_time") if cal else None
    end_time = cal.get("end_time") if cal else None

    duration = None
    if start_time and end_time:
        try:
            t0 = datetime.fromisoformat(start_time)
            t1 = datetime.fromisoformat(end_time)
            mins = int((t1 - t0).total_seconds() / 60)
            duration = f"{mins // 60:02d}:{mins % 60:02d}"
        except (ValueError, TypeError):
            pass

    summary = note.get("summary_markdown") or note.get("summary_text") or ""
    transcript = note.get("transcript") or []

    slug = title.lower().strip()
    for ch in ".,!?:;'\"()[]{}":
        slug = slug.replace(ch, "")
    slug = slug.replace(" ", "-").replace("--", "-")[:60].rstrip("-")
    filename = f"{date_short}-{slug}.md"

    lines = ["---"]
    lines.append(f"granola_id: {note_id}")
    lines.append(f'title: "{title}"')
    lines.append(f"date: {date_dash}")
    if participant_names:
        lines.append(f"participants: {json.dumps(participant_names)}")
    if duration:
        lines.append(f"duration: {duration}")
    lines.append("source: granola")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")

    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    if transcript:
        lines.append("## Transcript")
        lines.append("")
        for u in transcript:
            text = u.get("text", "").strip()
            if not text:
                continue
            speaker = u.get("speaker", {})
            source = speaker.get("source", "") if isinstance(speaker, dict) else ""
            label = speaker.get("diarization_label", "") if isinstance(speaker, dict) else ""
            if label:
                speaker_name = label
            elif source == "microphone":
                speaker_name = participant_names[0] if participant_names else "Speaker"
            elif source == "speaker":
                speaker_name = "Other"
            else:
                speaker_name = "Speaker"
            lines.append(f"**{speaker_name}**: {text}")
            lines.append("")

    content = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(args.vault) / "Sessions" / filename

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(json.dumps({
        "exported": str(out_path),
        "title": title,
        "date": date_short,
        "participants": participant_names,
        "duration": duration,
        "utterances": len(transcript),
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Granola meeting notes CLI (Personal API)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List notes")
    p_list.add_argument("--format", choices=["text", "json"], default="text")
    p_list.add_argument("--after", help="ISO 8601 date filter (created_after)")
    p_list.add_argument("--all", action="store_true", help="Paginate through all results")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show note details")
    p_show.add_argument("note_id", help="Note ID (not_xxxx)")
    p_show.add_argument("--format", choices=["text", "json"], default="text")
    p_show.add_argument("--transcript", action="store_true", help="Include transcript")
    p_show.set_defaults(func=cmd_show)

    p_export = sub.add_parser("export", help="Export note to Obsidian")
    p_export.add_argument("note_id", help="Note ID (not_xxxx)")
    p_export.add_argument("--vault", default=os.path.expanduser("~/Brains/brain"))
    p_export.add_argument("--output", help="Custom output path")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
