#!/usr/bin/env python3
"""
Wispr Flow Dictionary Manager.

Manages dictionary entries (recognition terms and replacement rules)
in the Wispr Flow SQLite database. Supports export/import via JSON
for version control and cross-machine sync.

IMPORTANT: Wispr Flow must be quit before any write operations.
Read operations (export, list, suggest) are safe while running.

Usage:
    python3 wispr_dictionary.py export [--output PATH]
    python3 wispr_dictionary.py import [--input PATH] [--dry-run]
    python3 wispr_dictionary.py add "phrase" ["replacement"]
    python3 wispr_dictionary.py remove "phrase"
    python3 wispr_dictionary.py list [--filter PATTERN]
    python3 wispr_dictionary.py suggest [--days 30] [--min-freq 3]
    python3 wispr_dictionary.py check
"""

import sqlite3
import json
import argparse
import os
import sys
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = os.path.expanduser("~/Library/Application Support/Wispr Flow/flow.sqlite")
DEFAULT_DICT_PATH = os.path.expanduser("~/ai_projects/claude-skills/wispr-analytics/data/dictionary.json")


def get_db(readonly=True):
    if not os.path.exists(DB_PATH):
        print("Error: Wispr Flow database not found", file=sys.stderr)
        sys.exit(1)
    uri = f"file:{DB_PATH}?mode=ro" if readonly else DB_PATH
    if readonly:
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def is_wispr_running():
    try:
        result = subprocess.run(["pgrep", "-f", "Wispr Flow"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def require_wispr_stopped():
    if is_wispr_running():
        print("Error: Wispr Flow is running. Quit it first (Cmd+Q) to avoid database corruption.", file=sys.stderr)
        sys.exit(1)


def cmd_export(args):
    conn = get_db(readonly=True)
    rows = conn.execute(
        "SELECT id, phrase, replacement, manualEntry, frequencyUsed, "
        "createdAt, modifiedAt, isDeleted, isSnippet, isStarred "
        "FROM Dictionary WHERE isDeleted = 0 ORDER BY phrase"
    ).fetchall()
    conn.close()

    entries = []
    for r in rows:
        entry = {
            "phrase": r["phrase"],
            "replacement": r["replacement"],
            "is_snippet": bool(r["isSnippet"]),
            "is_starred": bool(r["isStarred"]),
            "manual": bool(r["manualEntry"]),
            "frequency": r["frequencyUsed"],
        }
        if entry["replacement"] is None:
            del entry["replacement"]
        if not entry["is_snippet"]:
            del entry["is_snippet"]
        if not entry["is_starred"]:
            del entry["is_starred"]
        if not entry["manual"]:
            del entry["manual"]
        if entry["frequency"] == 0:
            del entry["frequency"]
        entries.append(entry)

    output = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat() + "Z",
        "count": len(entries),
        "entries": entries,
    }

    out_path = args.output or DEFAULT_DICT_PATH
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(entries)} entries to {out_path}")


def cmd_import(args):
    require_wispr_stopped()

    in_path = args.input or DEFAULT_DICT_PATH
    if not os.path.exists(in_path):
        print(f"Error: {in_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    conn = get_db(readonly=False)

    existing = {
        row[0]
        for row in conn.execute(
            "SELECT phrase FROM Dictionary WHERE isDeleted = 0"
        ).fetchall()
    }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    added = 0
    skipped = 0

    for entry in entries:
        phrase = entry["phrase"]
        if phrase in existing:
            skipped += 1
            continue

        if args.dry_run:
            replacement = entry.get("replacement", "")
            label = f"{phrase} → {replacement}" if replacement else phrase
            print(f"  Would add: {label}")
            added += 1
            continue

        entry_id = str(uuid.uuid4())
        replacement = entry.get("replacement") or phrase
        is_snippet = 1 if entry.get("is_snippet") else 0
        is_starred = 1 if entry.get("is_starred") else 0
        manual = 1 if entry.get("manual", True) else 0

        conn.execute(
            "INSERT INTO Dictionary (id, phrase, replacement, teamDictionaryId, "
            "lastUsed, frequencyUsed, remoteFrequencyUsed, manualEntry, "
            "createdAt, modifiedAt, isDeleted, source, isSnippet, observedSource, isStarred) "
            "VALUES (?, ?, ?, '00000000-0000-0000-0000-000000000000', "
            "NULL, 0, 0, ?, ?, ?, 0, 'manual', ?, NULL, ?)",
            (entry_id, phrase, replacement, manual, now, now, is_snippet, is_starred),
        )
        added += 1

    if not args.dry_run:
        conn.commit()

    conn.close()

    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"{prefix}Added: {added}, Skipped (existing): {skipped}")


def cmd_add(args):
    require_wispr_stopped()
    conn = get_db(readonly=False)

    existing = conn.execute(
        "SELECT COUNT(*) FROM Dictionary WHERE phrase = ? AND isDeleted = 0",
        (args.phrase,),
    ).fetchone()[0]

    if existing > 0:
        print(f"'{args.phrase}' already exists in dictionary")
        conn.close()
        return

    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    replacement = args.replacement if args.replacement else args.phrase

    conn.execute(
        "INSERT INTO Dictionary (id, phrase, replacement, teamDictionaryId, "
        "lastUsed, frequencyUsed, remoteFrequencyUsed, manualEntry, "
        "createdAt, modifiedAt, isDeleted, source, isSnippet, observedSource, isStarred) "
        "VALUES (?, ?, ?, '00000000-0000-0000-0000-000000000000', "
        "NULL, 0, 0, 1, ?, ?, 0, 'manual', 0, NULL, 0)",
        (entry_id, args.phrase, replacement, now, now),
    )
    conn.commit()
    conn.close()

    label = f"'{args.phrase}' → '{replacement}'" if replacement else f"'{args.phrase}'"
    print(f"Added: {label}")


def cmd_remove(args):
    require_wispr_stopped()
    conn = get_db(readonly=False)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    result = conn.execute(
        "UPDATE Dictionary SET isDeleted = 1, modifiedAt = ? WHERE phrase = ? AND isDeleted = 0",
        (now, args.phrase),
    )
    conn.commit()

    if result.rowcount > 0:
        print(f"Removed: '{args.phrase}'")
    else:
        print(f"Not found: '{args.phrase}'")
    conn.close()


def cmd_list(args):
    conn = get_db(readonly=True)

    query = "SELECT phrase, replacement, frequencyUsed, isSnippet FROM Dictionary WHERE isDeleted = 0"
    params = []
    if args.filter:
        query += " AND (phrase LIKE ? OR replacement LIKE ?)"
        params = [f"%{args.filter}%", f"%{args.filter}%"]
    query += " ORDER BY phrase"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    for r in rows:
        phrase = r["phrase"]
        replacement = r["replacement"] or ""
        freq = r["frequencyUsed"]
        snippet = " [snippet]" if r["isSnippet"] else ""
        freq_str = f" (used {freq}x)" if freq > 0 else ""

        if replacement and replacement != phrase:
            print(f"  {phrase} → {replacement}{freq_str}{snippet}")
        else:
            print(f"  {phrase} [vocab]{freq_str}{snippet}")

    print(f"\n{len(rows)} entries")


def cmd_suggest(args):
    """Analyze dictation history for potential dictionary additions."""
    conn = get_db(readonly=True)

    days = args.days or 30
    min_freq = args.min_freq or 3
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    existing = {
        row[0].lower()
        for row in conn.execute(
            "SELECT phrase FROM Dictionary WHERE isDeleted = 0"
        ).fetchall()
    }

    rows = conn.execute(
        "SELECT asrText, formattedText FROM History "
        "WHERE timestamp > ? AND asrText IS NOT NULL AND formattedText IS NOT NULL "
        "AND asrText != formattedText",
        (cutoff,),
    ).fetchall()
    conn.close()

    corrections = {}
    for r in rows:
        asr = r["asrText"].strip()
        fmt = r["formattedText"].strip()

        if len(asr) > 100 or len(fmt) > 100:
            continue
        if asr.lower() == fmt.lower():
            continue
        if asr.lower() in existing:
            continue

        import difflib
        ratio = difflib.SequenceMatcher(None, asr.lower(), fmt.lower()).ratio()
        if ratio > 0.6 and ratio < 1.0:
            key = (asr, fmt)
            corrections[key] = corrections.get(key, 0) + 1

    suggestions = sorted(corrections.items(), key=lambda x: -x[1])

    print(f"Suggested dictionary additions (last {days} days, min {min_freq} occurrences):\n")

    count = 0
    for (asr, fmt), freq in suggestions:
        if freq >= min_freq:
            print(f"  {asr} → {fmt}  ({freq}x)")
            count += 1

    if count == 0:
        print("  No suggestions found. Try lowering --min-freq or increasing --days.")
    else:
        print(f"\n{count} suggestions. Add with: python3 wispr_dictionary.py add \"phrase\" \"replacement\"")


def cmd_check(args):
    """Check database health and dictionary stats."""
    conn = get_db(readonly=True)

    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]

    total = conn.execute("SELECT COUNT(*) FROM Dictionary").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM Dictionary WHERE isDeleted = 0").fetchone()[0]
    manual = conn.execute("SELECT COUNT(*) FROM Dictionary WHERE isDeleted = 0 AND manualEntry = 1").fetchone()[0]
    snippets = conn.execute("SELECT COUNT(*) FROM Dictionary WHERE isDeleted = 0 AND isSnippet = 1").fetchone()[0]
    with_replacement = conn.execute(
        "SELECT COUNT(*) FROM Dictionary WHERE isDeleted = 0 AND replacement IS NOT NULL AND replacement != ''"
    ).fetchone()[0]

    conn.close()

    running = "YES ⚠️  (quit before writing)" if is_wispr_running() else "no"

    print(f"Database: {DB_PATH}")
    print(f"Integrity: {integrity}")
    print(f"Wispr running: {running}")
    print(f"Dictionary: {active} active / {total} total")
    print(f"  Manual entries: {manual}")
    print(f"  With replacements: {with_replacement}")
    print(f"  Snippets: {snippets}")
    print(f"  Auto-learned: {active - manual}")


def main():
    parser = argparse.ArgumentParser(description="Wispr Flow Dictionary Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export", help="Export dictionary to JSON")
    p_export.add_argument("--output", "-o", help=f"Output path (default: {DEFAULT_DICT_PATH})")

    p_import = sub.add_parser("import", help="Import dictionary from JSON")
    p_import.add_argument("--input", "-i", help=f"Input path (default: {DEFAULT_DICT_PATH})")
    p_import.add_argument("--dry-run", action="store_true", help="Show what would be added")

    p_add = sub.add_parser("add", help="Add a single entry")
    p_add.add_argument("phrase", help="The phrase to recognize")
    p_add.add_argument("replacement", nargs="?", help="Optional replacement text")

    p_remove = sub.add_parser("remove", help="Remove an entry (soft delete)")
    p_remove.add_argument("phrase", help="The phrase to remove")

    p_list = sub.add_parser("list", help="List dictionary entries")
    p_list.add_argument("--filter", "-f", help="Filter by phrase or replacement")

    p_suggest = sub.add_parser("suggest", help="Suggest new entries from dictation history")
    p_suggest.add_argument("--days", type=int, default=30, help="Days of history to analyze")
    p_suggest.add_argument("--min-freq", type=int, default=3, help="Minimum correction frequency")

    p_check = sub.add_parser("check", help="Check database health")

    args = parser.parse_args()

    commands = {
        "export": cmd_export,
        "import": cmd_import,
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "suggest": cmd_suggest,
        "check": cmd_check,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
