#!/usr/bin/env python3
"""Granola meeting notes CLI — query local cache and API, export to Obsidian."""

import json
import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

CACHE_PATH = os.path.expanduser(
    "~/Library/Application Support/Granola/cache-v4.json"
)
SUPABASE_PATH = os.path.expanduser(
    "~/Library/Application Support/Granola/supabase.json"
)
API_BASE = "https://api.granola.ai"


def load_cache():
    with open(CACHE_PATH, "r") as f:
        raw = json.load(f)
    state = raw.get("cache", {})
    if isinstance(state.get("state"), str):
        state = json.loads(state["state"])
    else:
        state = state.get("state", {})
    return state


def get_access_token():
    with open(SUPABASE_PATH, "r") as f:
        data = json.load(f)
    tokens = json.loads(data["workos_tokens"])
    obtained = tokens["obtained_at"]
    expires_ms = obtained + tokens["expires_in"] * 1000
    now_ms = int(time.time() * 1000)
    if now_ms >= expires_ms:
        print("ERROR: Access token expired. Open Granola app to refresh.", file=sys.stderr)
        sys.exit(1)
    return tokens["access_token"]


def api_request(endpoint, payload=None):
    """Make authenticated API request to Granola."""
    import urllib.request
    import gzip

    token = get_access_token()
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        body = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
        return json.loads(body.decode("utf-8"))


def extract_people(doc):
    """Extract attendee names/emails from document."""
    people = doc.get("people", {})
    if not isinstance(people, dict):
        return []
    attendees = people.get("attendees", [])
    result = []
    for a in attendees:
        if isinstance(a, dict):
            name = None
            details = a.get("details", {})
            if isinstance(details, dict):
                person = details.get("person", {})
                if isinstance(person, dict):
                    name_obj = person.get("name", {})
                    if isinstance(name_obj, dict):
                        name = name_obj.get("fullName")
            email = a.get("email", "")
            result.append({"name": name or email.split("@")[0], "email": email})
    return result


def extract_calendar_times(doc):
    """Extract start/end times from calendar event."""
    cal = doc.get("google_calendar_event")
    if not cal or not isinstance(cal, dict):
        return None, None
    start = cal.get("start", {}).get("dateTime")
    end = cal.get("end", {}).get("dateTime")
    return start, end


def format_time(iso_str):
    """Format ISO timestamp to HH:MM."""
    if not iso_str:
        return "?"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%H:%M")
    except (ValueError, TypeError):
        return "?"


def cmd_list(args):
    """List all meetings from local cache."""
    state = load_cache()
    docs = state.get("documents", {})
    transcripts = state.get("transcripts", {})

    sorted_docs = sorted(
        docs.values(), key=lambda d: d.get("created_at", ""), reverse=True
    )

    output = {"meetings": []}
    for doc in sorted_docs:
        doc_id = doc.get("id", "")
        title = doc.get("title") or "(Untitled)"
        created = doc.get("created_at", "")[:10]
        people = extract_people(doc)
        start, end = extract_calendar_times(doc)
        has_transcript = doc_id in transcripts
        transcript_count = len(transcripts.get(doc_id, []))

        entry = {
            "id": doc_id,
            "title": title,
            "date": created,
            "start": format_time(start),
            "end": format_time(end),
            "attendees": [p["name"] for p in people],
            "has_local_transcript": has_transcript,
            "transcript_utterances": transcript_count,
        }
        output["meetings"].append(entry)

    if args.format == "json":
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Found {len(output['meetings'])} meetings in Granola:\n")
        for m in output["meetings"]:
            tx = f" [{m['transcript_utterances']} utterances]" if m["has_local_transcript"] else ""
            attendees = f" with {', '.join(m['attendees'])}" if m["attendees"] else ""
            print(f"  {m['date']} {m['start']}-{m['end']}  {m['title']}{attendees}{tx}")
            print(f"    id: {m['id']}")


def find_document(docs, meeting_id):
    """Find a document by ID prefix or title substring."""
    for did, d in docs.items():
        if did.startswith(meeting_id) or (
            meeting_id.lower() in (d.get("title") or "").lower()
        ):
            return d
    return None


def require_document(docs, meeting_id):
    """Find a document or exit with error."""
    doc = find_document(docs, meeting_id)
    if not doc:
        print(f"Meeting not found: {meeting_id}", file=sys.stderr)
        sys.exit(1)
    return doc


def cmd_show(args):
    """Show details of a specific meeting."""
    state = load_cache()
    docs = state.get("documents", {})
    transcripts = state.get("transcripts", {})

    doc = require_document(docs, args.meeting_id)

    doc_id = doc["id"]
    result = {
        "id": doc_id,
        "title": doc.get("title") or "(Untitled)",
        "date": doc.get("created_at", "")[:10],
        "attendees": extract_people(doc),
        "calendar": None,
        "notes_markdown": doc.get("notes_markdown") or "",
        "notes_plain": doc.get("notes_plain") or "",
        "summary": doc.get("summary") or "",
    }

    cal = doc.get("google_calendar_event")
    if cal and isinstance(cal, dict):
        result["calendar"] = {
            "title": cal.get("summary"),
            "start": cal.get("start", {}).get("dateTime"),
            "end": cal.get("end", {}).get("dateTime"),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_transcript(args):
    """Get transcript for a meeting (local cache or API)."""
    state = load_cache()
    docs = state.get("documents", {})
    transcripts = state.get("transcripts", {})

    doc = require_document(docs, args.meeting_id)

    doc_id = doc["id"]
    utterances = transcripts.get(doc_id)

    # Try local cache first, then API
    if not utterances and not args.local_only:
        try:
            utterances = api_request("/v1/get-document-transcript", {"document_id": doc_id})
            if isinstance(utterances, dict) and "message" in utterances:
                utterances = None
        except Exception as e:
            print(f"API fetch failed: {e}", file=sys.stderr)
            utterances = None

    if not utterances:
        print(f"No transcript available for: {doc.get('title')}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(utterances, ensure_ascii=False, indent=2))
    else:
        for u in utterances:
            ts = u.get("start_timestamp", "")
            text = u.get("text", "")
            source = u.get("source", "")
            time_str = format_time(ts) if ts else ""
            src_tag = f" [{source}]" if source else ""
            print(f"[{time_str}]{src_tag} {text}")


def compute_duration(utterances):
    """Compute duration from first to last utterance timestamps."""
    if not utterances:
        return None
    first_ts = utterances[0].get("start_timestamp", "")
    last_ts = utterances[-1].get("end_timestamp", "")
    if not first_ts or not last_ts:
        return None
    try:
        t0 = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        delta = t1 - t0
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    except (ValueError, TypeError):
        return None


def cmd_export(args):
    """Export meeting to Obsidian markdown note (Fathom-compatible format)."""
    state = load_cache()
    docs = state.get("documents", {})
    transcripts = state.get("transcripts", {})
    metadata = state.get("meetingsMetadata", {})

    doc = require_document(docs, args.meeting_id)

    doc_id = doc["id"]
    title = doc.get("title") or "(Untitled)"
    created = doc.get("created_at", "")[:10].replace("-", "")
    created_dash = doc.get("created_at", "")[:10]
    people = extract_people(doc)
    start, end = extract_calendar_times(doc)
    notes_md = doc.get("notes_markdown") or ""
    summary = doc.get("summary") or ""

    # Get transcript
    utterances = transcripts.get(doc_id)
    if not utterances and not args.local_only:
        try:
            utterances = api_request("/v1/get-document-transcript", {"document_id": doc_id})
            if isinstance(utterances, dict):
                utterances = None
        except Exception:
            utterances = None

    # Compute duration
    duration = compute_duration(utterances)
    if not duration and start and end:
        try:
            t0 = datetime.fromisoformat(start)
            t1 = datetime.fromisoformat(end)
            mins = int((t1 - t0).total_seconds() / 60)
            duration = f"{mins // 60:02d}:{mins % 60:02d}"
        except (ValueError, TypeError):
            duration = None

    # Build participant list including creator
    participant_names = []
    people_dict = doc.get("people", {})
    if isinstance(people_dict, dict):
        creator = people_dict.get("creator", {})
        if isinstance(creator, dict) and creator.get("name"):
            participant_names.append(creator["name"])
    for p in people:
        if p["name"] not in participant_names:
            participant_names.append(p["name"])

    # Build slug
    slug = title.lower().strip()
    for ch in ".,!?:;'\"()[]{}":
        slug = slug.replace(ch, "")
    slug = slug.replace(" ", "-").replace("--", "-")[:60].rstrip("-")
    filename = f"{created}-{slug}.md"

    # Build frontmatter (Fathom-compatible)
    lines = ["---"]
    lines.append(f"granola_id: {doc_id}")
    lines.append(f"title: \"{title}\"")
    lines.append(f"date: {created_dash}")
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

    if notes_md:
        lines.append("## Notes")
        lines.append("")
        lines.append(notes_md)
        lines.append("")

    if utterances:
        lines.append("## Transcript")
        lines.append("")
        for u in utterances:
            text = u.get("text", "").strip()
            if not text:
                continue
            source = u.get("source", "")
            # Granola doesn't have per-utterance speaker names.
            # Use source label as speaker stand-in.
            if source == "microphone":
                speaker = participant_names[0] if participant_names else "Speaker"
            elif source == "system":
                speaker = "Other"
            else:
                speaker = "Speaker"
            lines.append(f"**{speaker}**: {text}")
            lines.append("")

    content = "\n".join(lines)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(args.vault) / filename

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(json.dumps({
        "exported": str(out_path),
        "title": title,
        "date": created,
        "participants": participant_names,
        "duration": duration,
        "utterances": len(utterances) if utterances else 0,
    }, ensure_ascii=False, indent=2))


def cmd_api_list(args):
    """List all meetings via Granola API (may have more than local cache)."""
    result = api_request("/v2/get-documents", {
        "limit": args.limit,
        "offset": args.offset,
        "include_content": True,
    })
    docs = result.get("docs", [])
    output = {"meetings": [], "total_returned": len(docs)}
    for doc in docs:
        people = extract_people(doc)
        start, end = extract_calendar_times(doc)
        output["meetings"].append({
            "id": doc.get("id", ""),
            "title": doc.get("title") or "(Untitled)",
            "date": doc.get("created_at", "")[:10],
            "start": format_time(start),
            "end": format_time(end),
            "attendees": [p["name"] for p in people],
            "has_notes": bool(doc.get("notes_markdown")),
            "has_summary": bool(doc.get("summary")),
        })
    print(json.dumps(output, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Granola meeting notes CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List meetings from local cache")
    p_list.add_argument("--format", choices=["text", "json"], default="text")
    p_list.set_defaults(func=cmd_list)

    # show
    p_show = sub.add_parser("show", help="Show meeting details")
    p_show.add_argument("meeting_id", help="Document ID (prefix) or title substring")
    p_show.set_defaults(func=cmd_show)

    # transcript
    p_tx = sub.add_parser("transcript", help="Get meeting transcript")
    p_tx.add_argument("meeting_id", help="Document ID (prefix) or title substring")
    p_tx.add_argument("--format", choices=["text", "json"], default="text")
    p_tx.add_argument("--local-only", action="store_true", help="Only use local cache")
    p_tx.set_defaults(func=cmd_transcript)

    # export
    p_exp = sub.add_parser("export", help="Export meeting to Obsidian note")
    p_exp.add_argument("meeting_id", help="Document ID (prefix) or title substring")
    p_exp.add_argument("--vault", default=os.path.expanduser("~/Brains/brain"),
                       help="Obsidian vault path")
    p_exp.add_argument("--output", help="Custom output path (overrides vault)")
    p_exp.add_argument("--local-only", action="store_true")
    p_exp.set_defaults(func=cmd_export)

    # api-list
    p_api = sub.add_parser("api-list", help="List meetings via Granola API")
    p_api.add_argument("--limit", type=int, default=50)
    p_api.add_argument("--offset", type=int, default=0)
    p_api.set_defaults(func=cmd_api_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
