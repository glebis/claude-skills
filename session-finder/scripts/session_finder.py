#!/usr/bin/env python3
"""
Session Finder — index and search Claude Code sessions using semantic embeddings.

Usage:
    python3 session_finder.py index [--max-age-days 90]
    python3 session_finder.py search "query" [--top 5]
    python3 session_finder.py stats
"""

import sys
import json
import sqlite3
import struct
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import math

DB_PATH = Path.home() / ".claude" / "session-finder.db"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
EMBED_MODEL = "gemini-embedding-001"


def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            parent_session_id TEXT,
            project TEXT,
            cwd TEXT,
            first_timestamp TEXT,
            last_timestamp TEXT,
            file_path TEXT,
            file_mtime REAL,
            message_count INTEGER,
            tools_used TEXT,
            has_away_summary INTEGER,
            document TEXT,
            embedding BLOB
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_mtime ON sessions(file_mtime)")
    conn.commit()


def _detect_parent_session(jsonl_path: Path) -> Optional[str]:
    """If this JSONL lives inside a subagents/ dir, return the parent session ID."""
    parts = jsonl_path.parts
    for i, p in enumerate(parts):
        if p == "subagents" and i > 0:
            return parts[i - 1]
    return None


def extract_document(jsonl_path: Path) -> Optional[dict]:
    """Deterministically extract a searchable document from a session JSONL."""
    user_messages = []
    assistant_texts = []
    tools_used = set()
    away_summaries = []
    timestamps = []
    session_id = None
    cwd = None
    project = extract_project_name(jsonl_path)
    parent_session_id = _detect_parent_session(jsonl_path)

    try:
        with open(jsonl_path, "r", errors="ignore") as f:
            for line in f:
                try:
                    ev = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue

                ts = ev.get("timestamp")
                if ts:
                    timestamps.append(ts)

                if not session_id:
                    session_id = ev.get("sessionId")
                if not cwd:
                    cwd = ev.get("cwd")

                ev_type = ev.get("type")
                subtype = ev.get("subtype", "")

                if subtype == "away_summary":
                    content = ev.get("content", "")
                    if content:
                        away_summaries.append(content)
                    continue

                if ev_type == "user":
                    msg = ev.get("message", {})
                    content = msg.get("content")
                    text = _extract_text(content)
                    if text and not _is_noise(text):
                        user_messages.append(text)

                elif ev_type == "assistant":
                    msg = ev.get("message", {})
                    content = msg.get("content")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    t = block.get("text", "").strip()
                                    if t and len(t) > 20:
                                        assistant_texts.append(t)
                                elif block.get("type") == "tool_use":
                                    tools_used.add(block.get("name", ""))

    except Exception:
        return None

    if not user_messages:
        return None

    session_id = session_id or jsonl_path.stem

    # Build document deterministically
    parts = []

    # Away summaries are the best signal — use them first
    if away_summaries:
        parts.append("Session summaries: " + " | ".join(away_summaries))

    # First user message = task description
    parts.append("Task: " + _truncate(user_messages[0], 500))

    # All user messages (condensed) for topic coverage
    if len(user_messages) > 1:
        condensed = " ".join(_truncate(m, 150) for m in user_messages[1:])
        parts.append("Follow-up: " + _truncate(condensed, 1000))

    # First substantive assistant response (often contains the approach)
    if assistant_texts:
        parts.append("Response: " + _truncate(assistant_texts[0], 300))

    # Tool fingerprint
    real_tools = sorted(t for t in tools_used if t)
    if real_tools:
        parts.append("Tools: " + ", ".join(real_tools))

    # Project context
    parts.append(f"Project: {project}")

    document = "\n".join(parts)

    return {
        "session_id": session_id,
        "parent_session_id": parent_session_id,
        "project": project,
        "cwd": cwd or "",
        "first_timestamp": min(timestamps) if timestamps else "",
        "last_timestamp": max(timestamps) if timestamps else "",
        "file_path": str(jsonl_path),
        "file_mtime": jsonl_path.stat().st_mtime,
        "message_count": len(user_messages),
        "tools_used": json.dumps(real_tools),
        "has_away_summary": 1 if away_summaries else 0,
        "document": document,
    }


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()
    return ""


def _is_noise(text: str) -> bool:
    if "<system-reminder>" in text:
        return True
    if text.startswith("Base directory for this skill"):
        return True
    if len(text) < 5:
        return True
    return False


def _truncate(text: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def extract_project_name(path: Path) -> str:
    parent = path.parent.name
    cleaned = parent.lstrip("-")
    parts = cleaned.split("-")
    skip = {"Users", "home", "ai_projects", "projects", "src", "code", "private", "var", "folders", "tmp"}
    meaningful = []
    for part in parts:
        if re.match(r"^\d{8}$", part):
            continue
        if part in skip or len(part) <= 2:
            continue
        meaningful.append(part)
    if meaningful:
        return "/".join(meaningful[-2:]) if len(meaningful) > 1 else meaningful[-1]
    return parent


def embed_text(text: str) -> Optional[bytes]:
    """Embed text using llm CLI and return packed floats."""
    try:
        result = subprocess.run(
            ["llm", "embed", "-m", EMBED_MODEL, "-c", text],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"  embed error: {result.stderr.strip()}", file=sys.stderr)
            return None
        values = json.loads(result.stdout)
        return struct.pack(f"{len(values)}f", *values)
    except Exception as e:
        print(f"  embed exception: {e}", file=sys.stderr)
        return None


def embed_batch(texts: list[str]) -> list[Optional[bytes]]:
    """Embed multiple texts via llm embed-multi, falling back to one-by-one."""
    # llm embed-multi reads from stdin as JSON lines
    # For simplicity and reliability, do one-by-one
    return [embed_text(t) for t in texts]


def cosine_similarity(a: bytes, b: bytes) -> float:
    n = len(a) // 4
    va = struct.unpack(f"{n}f", a)
    vb = struct.unpack(f"{n}f", b)
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(x * x for x in vb))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── Commands ──


def cmd_index(max_age_days: int = 90):
    """Index sessions: extract documents and compute embeddings."""
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    cutoff = datetime.now() - timedelta(days=max_age_days)
    all_jsonl = []
    for f in PROJECTS_DIR.rglob("*.jsonl"):
        try:
            stat = f.stat()
            if stat.st_size > 100 and datetime.fromtimestamp(stat.st_mtime) > cutoff:
                all_jsonl.append(f)
        except OSError:
            continue

    print(f"Found {len(all_jsonl)} session files (last {max_age_days} days)")

    # Check which are already indexed with current mtime
    existing = {}
    for row in conn.execute("SELECT file_path, file_mtime FROM sessions"):
        existing[row[0]] = row[1]

    to_index = []
    for f in all_jsonl:
        fp = str(f)
        if fp in existing and abs(existing[fp] - f.stat().st_mtime) < 1:
            continue
        to_index.append(f)

    print(f"Need to index: {len(to_index)} (skipping {len(all_jsonl) - len(to_index)} already indexed)")

    if not to_index:
        print("Nothing to do.")
        conn.close()
        return

    indexed = 0
    skipped = 0
    for i, f in enumerate(to_index):
        doc = extract_document(f)
        if not doc:
            skipped += 1
            continue

        print(f"  [{i+1}/{len(to_index)}] {doc['project']} — {doc['session_id'][:8]}…", end=" ", flush=True)

        embedding = embed_text(doc["document"])
        if not embedding:
            print("(no embedding)")
            skipped += 1
            continue

        conn.execute("""
            INSERT OR REPLACE INTO sessions
            (session_id, parent_session_id, project, cwd, first_timestamp,
             last_timestamp, file_path, file_mtime, message_count, tools_used,
             has_away_summary, document, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc["session_id"], doc["parent_session_id"],
            doc["project"], doc["cwd"],
            doc["first_timestamp"], doc["last_timestamp"],
            doc["file_path"], doc["file_mtime"], doc["message_count"],
            doc["tools_used"], doc["has_away_summary"],
            doc["document"], embedding
        ))
        indexed += 1
        print("✓")

        if indexed % 20 == 0:
            conn.commit()

    conn.commit()
    conn.close()
    print(f"\nDone. Indexed: {indexed}, Skipped: {skipped}")


def cmd_search(query: str, top_n: int = 5):
    """Search sessions by semantic similarity."""
    if not DB_PATH.exists():
        print("No index found. Run: python3 session_finder.py index")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    total = conn.execute("SELECT COUNT(*) FROM sessions WHERE embedding IS NOT NULL").fetchone()[0]
    if total == 0:
        print("Index is empty. Run: python3 session_finder.py index")
        conn.close()
        sys.exit(1)

    print(f"Searching {total} sessions for: \"{query}\"")

    query_emb = embed_text(query)
    if not query_emb:
        print("Failed to embed query.")
        conn.close()
        sys.exit(1)

    rows = conn.execute("""
        SELECT session_id, parent_session_id, project, cwd, first_timestamp,
               last_timestamp, message_count, has_away_summary, document, embedding
        FROM sessions WHERE embedding IS NOT NULL
    """).fetchall()

    scored = []
    for row in rows:
        emb = row[9]
        sim = cosine_similarity(query_emb, emb)
        scored.append((sim, row))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\nTop {min(top_n, len(scored))} results:\n")

    for rank, (sim, row) in enumerate(scored[:top_n], 1):
        sid, parent_sid, project, cwd, first_ts, last_ts, msg_count, has_summary, doc, _ = row
        resume_id = parent_sid or sid

        # Parse timestamp for display
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = first_ts[:16] if first_ts else "?"

        # Extract first line of document as summary
        lines = doc.split("\n")
        summary_line = lines[0] if lines else ""
        if summary_line.startswith("Session summaries: "):
            summary_line = summary_line[len("Session summaries: "):]
        elif summary_line.startswith("Task: "):
            summary_line = summary_line[len("Task: "):]
        summary_line = _truncate(summary_line, 120)

        confidence = sim * 100
        is_subagent = " (subagent)" if parent_sid else ""
        print(f"  {rank}. [{confidence:.0f}%] {project} — {date_str}{is_subagent}")
        print(f"     {summary_line}")
        print(f"     claude --resume {resume_id}")
        if rank == 1:
            print(f"     ↑ DEFAULT — run with: sfo {query}")
        print()

    conn.close()

    # Output machine-readable best match (resolved to parent)
    if scored:
        best_row = scored[0][1]
        best_sid = best_row[1] or best_row[0]
        print(f"BEST_SESSION_ID={best_sid}")


def cmd_open(query: str):
    """Search and immediately open the top match."""
    if not DB_PATH.exists():
        print("No index found. Run: python3 session_finder.py index")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))
    query_emb = embed_text(query)
    if not query_emb:
        print("Failed to embed query.")
        conn.close()
        sys.exit(1)

    rows = conn.execute(
        "SELECT session_id, parent_session_id, project, document, embedding FROM sessions WHERE embedding IS NOT NULL"
    ).fetchall()

    best_sim = -1
    best_sid = None
    best_parent = None
    best_doc = None
    for row in rows:
        sim = cosine_similarity(query_emb, row[4])
        if sim > best_sim:
            best_sim = sim
            best_sid = row[0]
            best_parent = row[1]
            best_doc = row[3]

    conn.close()

    if not best_sid:
        print("No sessions in index.")
        sys.exit(1)

    resume_id = best_parent or best_sid
    lines = (best_doc or "").split("\n")
    summary = lines[0][:120] if lines else ""
    print(f"Opening: {summary}")
    print(f"Confidence: {best_sim*100:.0f}%")
    if best_parent:
        print(f"Matched subagent: {best_sid}")
        print(f"Resuming parent: {resume_id}")
    else:
        print(f"Session: {resume_id}")
    print(f"Launching: claude --resume {resume_id}")

    import os
    os.execvp("claude", ["claude", "--resume", resume_id])


def cmd_stats():
    """Show index statistics."""
    if not DB_PATH.exists():
        print("No index. Run: python3 session_finder.py index")
        return

    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    total = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    with_emb = conn.execute("SELECT COUNT(*) FROM sessions WHERE embedding IS NOT NULL").fetchone()[0]
    with_summary = conn.execute("SELECT COUNT(*) FROM sessions WHERE has_away_summary = 1").fetchone()[0]

    projects = conn.execute("SELECT project, COUNT(*) FROM sessions GROUP BY project ORDER BY COUNT(*) DESC LIMIT 10").fetchall()

    print(f"Total sessions indexed: {total}")
    print(f"With embeddings: {with_emb}")
    print(f"With away_summary: {with_summary}")
    print(f"DB size: {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\nTop projects:")
    for p, c in projects:
        print(f"  {p}: {c}")

    conn.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "index":
        max_age = 90
        if "--max-age-days" in sys.argv:
            idx = sys.argv.index("--max-age-days")
            max_age = int(sys.argv[idx + 1])
        cmd_index(max_age)

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: session_finder.py search \"query\" [--top 5]")
            sys.exit(1)
        query = sys.argv[2]
        top_n = 5
        if "--top" in sys.argv:
            idx = sys.argv.index("--top")
            top_n = int(sys.argv[idx + 1])
        cmd_search(query, top_n)

    elif cmd == "open":
        if len(sys.argv) < 3:
            print("Usage: session_finder.py open \"query\"")
            sys.exit(1)
        cmd_open(sys.argv[2])

    elif cmd == "stats":
        cmd_stats()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
