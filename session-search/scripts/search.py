#!/usr/bin/env python3
"""
Session Search - Search across Claude Code session transcripts.
Pre-filters sessions by keyword matching, then outputs candidates
for Claude to evaluate semantically.
"""

import sys
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple


def find_all_sessions(max_age_days: int = 90) -> List[Tuple[Path, datetime]]:
    """Find all session files modified within max_age_days."""
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return []

    cutoff = datetime.now() - timedelta(days=max_age_days)
    sessions = []

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        try:
            stat = jsonl_file.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            if mtime > cutoff and stat.st_size > 100:
                sessions.append((jsonl_file, mtime))
        except (OSError, ValueError):
            continue

    sessions.sort(key=lambda x: x[1], reverse=True)
    return sessions


def extract_project_name(path: Path) -> str:
    """Extract readable project name from session path.

    Paths look like: ~/.claude/projects/-Users-name-projects-foo/session.jsonl
    or: ~/.claude/projects/-Users-name-projects-foo-20260323/session.jsonl
    """
    parent = path.parent.name

    # Remove leading dash and split
    cleaned = parent.lstrip("-")
    parts = cleaned.split("-")

    # Skip common prefixes (Users, username, common dirs)
    skip = {"Users", "home", "ai_projects", "projects", "src", "code"}

    meaningful = []
    for part in parts:
        # Skip numeric suffixes (dates like 20260323)
        if re.match(r"^\d{8}$", part):
            continue
        if part in skip:
            continue
        # Skip single-char parts and username (heuristic: second segment)
        if len(part) <= 2:
            continue
        meaningful.append(part)

    if meaningful:
        # Return last 2 meaningful parts joined
        return "/".join(meaningful[-2:]) if len(meaningful) > 1 else meaningful[-1]
    return parent


def keyword_match_score(texts: List[str], keywords: List[str]) -> int:
    """Count how many keyword matches exist in session texts."""
    combined = " ".join(texts).lower()
    score = 0
    for kw in keywords:
        score += combined.count(kw.lower())
    return score


def extract_meaningful_excerpts(session_path: Path, keywords: List[str], max_excerpts: int = 8) -> Tuple[List[str], int]:
    """Extract excerpts from session, prioritizing keyword-matching lines.

    Returns (excerpts, total_message_count).
    """
    all_texts = []
    keyword_texts = []
    keywords_lower = [k.lower() for k in keywords]

    try:
        with open(session_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_type = event.get("type")

                    if event_type not in ("user", "assistant"):
                        continue

                    message = event.get("message", {})
                    content = message.get("content")

                    if isinstance(content, str):
                        text = content.strip()
                    elif isinstance(content, list):
                        parts = []
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    parts.append(block.get("text", ""))
                                elif block.get("type") == "tool_use":
                                    parts.append(f"[Tool: {block.get('name', '')}]")
                        text = "\n".join(parts).strip()
                    else:
                        continue

                    if not text or len(text) < 10:
                        continue

                    # Skip system reminders and skill descriptions
                    if "<system-reminder>" in text or "Base directory for this skill" in text:
                        continue

                    all_texts.append(text)

                    # Check keyword match
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in keywords_lower):
                        # Truncate long texts to relevant portion
                        if len(text) > 300:
                            for kw in keywords_lower:
                                idx = text_lower.find(kw)
                                if idx >= 0:
                                    start = max(0, idx - 100)
                                    end = min(len(text), idx + 200)
                                    text = "..." + text[start:end] + "..."
                                    break
                        keyword_texts.append(text)

                except json.JSONDecodeError:
                    continue

    except Exception:
        return [], 0

    # Build excerpts: keyword matches first, then first/last user messages
    excerpts = []

    # Add keyword-matching excerpts (most relevant)
    for t in keyword_texts[:max_excerpts]:
        if len(t) > 300:
            t = t[:300] + "..."
        excerpts.append(t)

    # Fill remaining slots with first user message (usually the task description)
    remaining = max_excerpts - len(excerpts)
    if remaining > 0 and all_texts:
        first_msg = all_texts[0]
        if len(first_msg) > 300:
            first_msg = first_msg[:300] + "..."
        if first_msg not in excerpts:
            excerpts.append(first_msg)

    return excerpts, len(all_texts)


def search_sessions(query: str, max_results: int = 10, max_age_days: int = 90):
    """Search sessions: keyword pre-filter, then output top candidates for semantic eval."""
    sessions = find_all_sessions(max_age_days)

    if not sessions:
        print("No sessions found.")
        return

    # Split query into keywords for pre-filtering
    keywords = [w for w in query.split() if len(w) >= 2]
    if not keywords:
        keywords = [query]

    print(f"Scanning {len(sessions)} sessions...\n")

    # Phase 1: Quick keyword scan to find candidates
    candidates = []
    for session_path, mtime in sessions:
        try:
            # Quick scan: read raw file and check for keyword presence
            raw = session_path.read_text(errors="ignore")
            raw_lower = raw.lower()
            hit_count = sum(raw_lower.count(kw.lower()) for kw in keywords)

            if hit_count > 0:
                candidates.append((session_path, mtime, hit_count))
        except Exception:
            continue

    # Sort by hit count (descending), then by recency
    candidates.sort(key=lambda x: (x[2], x[1].timestamp()), reverse=True)

    if not candidates:
        print(f"No sessions found matching '{query}'.")
        return

    # Phase 2: Extract meaningful excerpts from top candidates
    top_n = min(max_results * 3, len(candidates), 30)  # Over-fetch for semantic filtering
    session_data = []

    for session_path, mtime, hit_count in candidates[:top_n]:
        excerpts, msg_count = extract_meaningful_excerpts(session_path, keywords)
        if excerpts:
            session_data.append({
                "session_id": session_path.stem,
                "mtime": mtime.strftime("%Y-%m-%d %H:%M"),
                "project": extract_project_name(session_path),
                "keyword_hits": hit_count,
                "total_messages": msg_count,
                "excerpts": excerpts,
            })

    print(f"Found {len(candidates)} sessions with keyword matches.")
    print(f"Returning top {len(session_data)} for evaluation.\n")

    print("SESSIONS_DATA:")
    print(json.dumps({
        "query": query,
        "max_results": max_results,
        "sessions": session_data,
    }, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print("Usage: search.py <query> [max_results] [max_age_days]")
        print('Example: search.py "bug fixing" 10 90')
        sys.exit(1)

    query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    max_age_days = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    print(f"Searching for: '{query}'")
    print(f"Max results: {max_results}, Max age: {max_age_days} days\n")

    search_sessions(query, max_results, max_age_days)


if __name__ == "__main__":
    main()
