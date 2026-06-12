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
    python3 wispr_dictionary.py propose [--days 30] [--min-freq 3] [--format text]
    python3 wispr_dictionary.py check
"""

import sqlite3
import json
import argparse
import os
import re
import sys
import subprocess
import uuid
import difflib
from collections import Counter
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

    if not args.dry_run and added > 0:
        restart_wispr()


def restart_wispr():
    print("Starting Wispr Flow...")
    try:
        subprocess.Popen(["open", "-a", "Wispr Flow"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Wispr Flow restarted.")
    except Exception:
        print("Warning: Could not restart Wispr Flow. Start it manually.", file=sys.stderr)


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


def get_existing_phrases(conn):
    """Return set of lowercased existing dictionary phrases (and replacements)."""
    existing = set()
    for row in conn.execute(
        "SELECT phrase, replacement FROM Dictionary WHERE isDeleted = 0"
    ).fetchall():
        if row[0]:
            existing.add(row[0].strip().lower())
        if row[1]:
            existing.add(row[1].strip().lower())
    return existing


def find_mishears(conn, cutoff, existing):
    """Find recurring ASR mishears (asrText vs formattedText diffs).

    Returns a list of (asr, fmt, freq) tuples sorted by frequency desc.
    Shared by both `suggest` and `propose`.
    """
    rows = conn.execute(
        "SELECT asrText, formattedText FROM History "
        "WHERE timestamp > ? AND asrText IS NOT NULL AND formattedText IS NOT NULL "
        "AND asrText != formattedText",
        (cutoff,),
    ).fetchall()

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

        ratio = difflib.SequenceMatcher(None, asr.lower(), fmt.lower()).ratio()
        if ratio > 0.6 and ratio < 1.0:
            key = (asr, fmt)
            corrections[key] = corrections.get(key, 0) + 1

    return sorted(
        ((asr, fmt, freq) for (asr, fmt), freq in corrections.items()),
        key=lambda x: -x[2],
    )


def cmd_suggest(args):
    """Analyze dictation history for potential dictionary additions (mishears only)."""
    conn = get_db(readonly=True)

    days = args.days or 30
    min_freq = args.min_freq or 3
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    existing = get_existing_phrases(conn)
    mishears = find_mishears(conn, cutoff, existing)
    conn.close()

    print(f"Suggested dictionary additions (last {days} days, min {min_freq} occurrences):\n")

    count = 0
    for asr, fmt, freq in mishears:
        if freq >= min_freq:
            print(f"  {asr} → {fmt}  ({freq}x)")
            count += 1

    if count == 0:
        print("  No suggestions found. Try lowering --min-freq or increasing --days.")
    else:
        print(f"\n{count} suggestions. Add with: python3 wispr_dictionary.py add \"phrase\" \"replacement\"")


# ---------------------------------------------------------------------------
# propose: human-style review that proposes snippets, replacement rules, vocab
# ---------------------------------------------------------------------------

URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)")
# Capitalized / technical tokens (incl. CamelCase, ALLCAPS acronyms). Latin only
# to avoid splitting Cyrillic sentence-initial words.
TECH_RE = re.compile(r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+|[A-Z]{2,}[a-z]*|[A-Z][a-z]+\.[a-z]+)\b")


_TRIGGER_SKIP = {
    "https", "http", "www", "com", "org", "net", "io", "co", "in", "of",
    "the", "me", "my", "a", "an", "to", "is", "it", "do", "we",
}


def _slug_trigger(text):
    """Build a short, memorable `My X` trigger phrase for a snippet expansion.

    For URLs/emails the service/domain name is the distinctive part; for
    boilerplate sentences use the first couple of content words.
    """
    tokens = re.findall(r"[A-Za-z0-9]+", text)
    content = [t for t in tokens if t.lower() not in _TRIGGER_SKIP and len(t) > 1]
    if not content:
        content = tokens[:2]
    if not content:
        return "My snippet"
    return "My " + " ".join(content[:2]).lower()


def _normalize_boiler(text):
    """Normalize text for boilerplate frequency counting (whitespace/case)."""
    return re.sub(r"\s+", " ", text.strip()).lower()


def find_snippet_candidates(rows, existing, min_freq):
    """Detect recurring URLs/emails/phones and repeated boilerplate sentences."""
    contacts = Counter()       # URL/email/phone -> count (dedup per dictation)
    boiler = Counter()         # normalized full short dictation -> count
    boiler_display = {}        # normalized -> first-seen original text

    for r in rows:
        fmt = (r["formattedText"] or "").strip()
        if not fmt:
            continue

        seen = set()
        for rx in (URL_RE, EMAIL_RE, PHONE_RE):
            for m in rx.findall(fmt):
                m = m.strip().rstrip(".,);:")
                if len(m) < 6:
                    continue
                if m.lower() in existing or m in seen:
                    continue
                seen.add(m)
                contacts[m] += 1

        # Boilerplate: whole dictations repeated verbatim (intros, sign-offs,
        # bios, standard prompts). Require >= 8 words so trivial fillers like
        # "Okay let's do it." don't surface; cap length to avoid huge one-offs.
        words = fmt.split()
        if 8 <= len(words) <= 60:
            norm = _normalize_boiler(fmt)
            if norm in existing:
                continue
            boiler[norm] += 1
            boiler_display.setdefault(norm, fmt)

    candidates = []
    for value, freq in contacts.most_common():
        if freq >= min_freq:
            candidates.append({
                "kind": "contact",
                "trigger": _slug_trigger(value),
                "expansion": value,
                "freq": freq,
            })
    for norm, freq in boiler.most_common():
        if freq >= max(min_freq, 2):
            text = boiler_display[norm]
            candidates.append({
                "kind": "boilerplate",
                "trigger": _slug_trigger(text),
                "expansion": text,
                "freq": freq,
            })
    return candidates


def find_vocab_candidates(rows, existing, min_freq):
    """Frequent capitalized/technical terms that may be mis-recognized."""
    counts = Counter()
    STOP = {
        "I", "The", "This", "That", "And", "But", "For", "You", "We", "It",
        "So", "If", "Or", "My", "No", "Yes", "OK", "Okay", "Also", "Then",
    }
    for r in rows:
        fmt = (r["formattedText"] or "")
        for tok in TECH_RE.findall(fmt):
            if tok in STOP or len(tok) < 3:
                continue
            if tok.lower() in existing:
                continue
            counts[tok] += 1

    return [
        {"term": term, "freq": freq}
        for term, freq in counts.most_common(40)
        if freq >= min_freq
    ]


def _add_cmd(phrase, replacement=None):
    """Render a ready-to-run add command line for a proposal."""
    p = phrase.replace('"', '\\"')
    if replacement is None:
        return f'python3 wispr_dictionary.py add "{p}"'
    r = replacement.replace('"', '\\"')
    return f'python3 wispr_dictionary.py add "{p}" "{r}"'


def cmd_propose(args):
    """Review recent dictation logs and propose dictionary additions.

    Three categories (read-only, safe while Wispr runs):
      1. Snippet candidates    -- recurring URLs/emails/phones + boilerplate
      2. Replacement-rule cand -- recurring ASR mishears (shared with suggest)
      3. Vocab candidates      -- frequent capitalized/technical terms
    """
    conn = get_db(readonly=True)

    days = args.days or 30
    min_freq = args.min_freq or 3
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    existing = get_existing_phrases(conn)

    rows = conn.execute(
        "SELECT formattedText FROM History "
        "WHERE timestamp > ? AND formattedText IS NOT NULL AND formattedText != ''",
        (cutoff,),
    ).fetchall()

    snippets = find_snippet_candidates(rows, existing, min_freq)
    mishears = [
        {"asr": asr, "fmt": fmt, "freq": freq}
        for asr, fmt, freq in find_mishears(conn, cutoff, existing)
        if freq >= min_freq
    ]
    vocab = find_vocab_candidates(rows, existing, min_freq)
    conn.close()

    if args.format == "json":
        out = {
            "days": days,
            "min_freq": min_freq,
            "snippet_candidates": snippets,
            "replacement_candidates": mishears,
            "vocab_candidates": vocab,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    total = len(snippets) + len(mishears) + len(vocab)
    print(f"Dictionary proposals from the last {days} days (min {min_freq} occurrences)")
    print(f"Analyzed {len(rows)} dictations. {total} proposals.\n")

    # --- Snippets (highest leverage) ---
    print("=" * 70)
    print("SNIPPET CANDIDATES  (text expansion -- the highest-leverage lever)")
    print("=" * 70)
    if not snippets:
        print("  none found.\n")
    else:
        for c in snippets:
            tag = "URL/contact" if c["kind"] == "contact" else "boilerplate"
            exp = c["expansion"]
            preview = exp if len(exp) <= 80 else exp[:77] + "..."
            print(f"  [{tag}] used {c['freq']}x")
            print(f"    trigger:   {c['trigger']}")
            print(f"    expansion: {preview}")
            print(f"    add:       {_add_cmd(c['trigger'], exp)}")
            print()

    # --- Replacement rules ---
    print("=" * 70)
    print("REPLACEMENT-RULE CANDIDATES  (recurring ASR mishears)")
    print("=" * 70)
    if not mishears:
        print("  none found.\n")
    else:
        for m in mishears:
            print(f"  {m['asr']} → {m['fmt']}  ({m['freq']}x)")
            print(f"    add: {_add_cmd(m['asr'], m['fmt'])}")
            print()

    # --- Vocab ---
    print("=" * 70)
    print("VOCAB CANDIDATES  (frequent technical terms -- teach recognition)")
    print("=" * 70)
    if not vocab:
        print("  none found.\n")
    else:
        for v in vocab:
            print(f"  {v['term']}  ({v['freq']}x)")
            print(f"    add: {_add_cmd(v['term'])}")
            print()

    if total == 0:
        print("No proposals. Try lowering --min-freq or increasing --days.")
    else:
        print("Review, then (after quitting Wispr Flow) run the `add` lines you approve,")
        print("followed by `python3 wispr_dictionary.py check` and restart Wispr.")


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

    p_propose = sub.add_parser(
        "propose",
        help="Propose snippets, replacement rules, and vocab from dictation logs",
    )
    p_propose.add_argument("--days", type=int, default=30, help="Days of history to analyze")
    p_propose.add_argument("--min-freq", type=int, default=3, help="Minimum occurrence frequency")
    p_propose.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    p_check = sub.add_parser("check", help="Check database health")

    args = parser.parse_args()

    commands = {
        "export": cmd_export,
        "import": cmd_import,
        "add": cmd_add,
        "remove": cmd_remove,
        "list": cmd_list,
        "suggest": cmd_suggest,
        "propose": cmd_propose,
        "check": cmd_check,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
