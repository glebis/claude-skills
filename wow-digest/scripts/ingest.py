#!/usr/bin/env python3
"""Multi-source content ingestion for WOW digest.

Pulls from email (GWS) and Telegram channels, normalizes to candidate JSONL.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import base64
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
EVAL_DIR = Path(__file__).parent.parent / ".wow-eval"


def load_config():
    import yaml
    config_path = CONFIG_DIR / "sources.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def extract_email_body(payload):
    """Extract plain text from Gmail message payload."""
    if "body" in payload and payload["body"].get("data"):
        if payload.get("mimeType", "") == "text/plain":
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and part["body"].get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            result = extract_email_body(part)
            if result:
                return result
    # Fallback to HTML stripped
    if "body" in payload and payload["body"].get("data"):
        html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    return ""


def ingest_email(config, days=1):
    """Pull newsletters from Gmail via GWS CLI."""
    query = config.get("email", {}).get("query", "newer_than:1d")
    max_results = config.get("email", {}).get("max_results", 100)
    query = query.replace("newer_than:1d", f"newer_than:{days}d")

    result = subprocess.run(
        ["gws", "gmail", "users", "messages", "list",
         "--params", json.dumps({"userId": "me", "q": query, "maxResults": max_results}),
         "--format", "json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"GWS error: {result.stderr}", file=sys.stderr)
        return []

    data = json.loads(result.stdout)
    messages = data.get("messages", [])
    candidates = []

    for msg in messages:
        msg_result = subprocess.run(
            ["gws", "gmail", "users", "messages", "get",
             "--params", json.dumps({
                 "userId": "me",
                 "id": msg["id"],
                 "format": "full"
             }),
             "--format", "json"],
            capture_output=True, text=True
        )
        if msg_result.returncode != 0:
            continue

        msg_data = json.loads(msg_result.stdout)
        headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}

        body = extract_email_body(msg_data["payload"])
        snippet = body[:500] if body else msg_data.get("snippet", "")

        candidates.append({
            "source_type": "email",
            "source_name": headers.get("From", "Unknown"),
            "title": headers.get("Subject", "No subject"),
            "snippet": snippet,
            "url": "",
            "timestamp": headers.get("Date", ""),
            "message_id": msg["id"],
        })

    return candidates


def ingest_telegram(config, days=1):
    """Pull channel posts from Telegram via tg.py."""
    tg_config = config.get("telegram", {})
    channels = tg_config.get("channels", [])
    limit = tg_config.get("limit_per_channel", 50)
    candidates = []
    tg_script = Path.home() / ".claude/skills/telegram-telethon/scripts/tg.py"

    for channel in channels:
        result = subprocess.run(
            [sys.executable, str(tg_script), "recent",
             "--chat", channel,
             "--days", str(days),
             "--limit", str(limit),
             "--json"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Telegram error for {channel}: {result.stderr}", file=sys.stderr)
            continue

        # tg.py outputs a JSON array, not NDJSON
        try:
            messages = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Fallback: try line-by-line
            messages = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        if not isinstance(messages, list):
            messages = [messages]

        for msg in messages:
            text = msg.get("text", msg.get("message", ""))
            if not text or len(text) < 20:
                continue
            candidates.append({
                "source_type": "telegram",
                "source_name": channel,
                "title": text[:100] if text else "No text",
                "snippet": text[:500] if text else "",
                "url": msg.get("url", ""),
                "timestamp": msg.get("date", ""),
                "message_id": str(msg.get("id", "")),
            })

    return candidates


def candidate_hash(candidate):
    """Hash title+source for dedup across days."""
    key = f"{candidate.get('title', '').strip().lower()}|{candidate.get('source_name', '').strip().lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def load_recent_hashes(days=7):
    """Load candidate hashes from the last N days of .wow-eval/candidates/."""
    hashes = set()
    candidates_dir = EVAL_DIR / "candidates"
    if not candidates_dir.exists():
        return hashes
    cutoff = datetime.now() - timedelta(days=days)
    for f in candidates_dir.glob("*.jsonl"):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < cutoff:
                continue
        except ValueError:
            continue
        for line in f.read_text().strip().split("\n"):
            if not line:
                continue
            try:
                c = json.loads(line)
                hashes.add(candidate_hash(c))
            except json.JSONDecodeError:
                continue
    return hashes


def dedup_candidates(candidates, recent_hashes):
    """Remove candidates already seen in the last 7 days."""
    unique = []
    seen_this_run = set()
    dupes = 0
    for c in candidates:
        h = candidate_hash(c)
        if h in recent_hashes or h in seen_this_run:
            dupes += 1
            continue
        seen_this_run.add(h)
        unique.append(c)
    if dupes:
        print(f"  Dedup: removed {dupes} already-seen candidates", file=sys.stderr)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Ingest content for WOW digest")
    parser.add_argument("--days", type=int, default=1, help="Look back N days")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL path")
    parser.add_argument("--sources", nargs="+", default=["email", "telegram"],
                        choices=["email", "telegram"], help="Sources to pull from")
    parser.add_argument("--no-dedup", action="store_true", help="Skip dedup check")
    args = parser.parse_args()

    config = load_config()
    all_candidates = []

    if "email" in args.sources:
        print(f"Pulling email (last {args.days}d)...", file=sys.stderr)
        all_candidates.extend(ingest_email(config, args.days))
        print(f"  → {len(all_candidates)} email candidates", file=sys.stderr)

    if "telegram" in args.sources:
        print(f"Pulling Telegram (last {args.days}d)...", file=sys.stderr)
        tg_count_before = len(all_candidates)
        all_candidates.extend(ingest_telegram(config, args.days))
        print(f"  → {len(all_candidates) - tg_count_before} Telegram candidates", file=sys.stderr)

    if not args.no_dedup:
        recent_hashes = load_recent_hashes(days=7)
        all_candidates = dedup_candidates(all_candidates, recent_hashes)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for c in all_candidates:
            f.write(json.dumps(c) + "\n")

    print(f"Total: {len(all_candidates)} candidates → {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
