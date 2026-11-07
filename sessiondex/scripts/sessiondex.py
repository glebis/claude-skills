#!/usr/bin/env python3
"""sessiondex: one full-text index over local AI agent sessions.

Reads Codex, Claude Code, OpenCode and Pi history (read-only) into a SQLite
FTS5 database. Only human and assistant text is indexed: no tool output, no
reasoning, no injected context. Likely secrets are scrubbed before storage.

    sessiondex.py index [--agent codex] [--full]
    sessiondex.py recent [-n 20] [--agent codex] [--days 7] [--cwd foo]
    sessiondex.py search "query" [-n 10] [--agent ...] [--days ...] [--role user]
    sessiondex.py show <id-prefix> [--tail 20]
    sessiondex.py stats

Add --json to recent/search/show/stats for agent use, and --all to include
subagent sessions. The index lives at ~/.local/share/sessiondex/index.db
(override with SESSIONDEX_DB).
"""
import argparse
import glob
import io
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
DB_PATH = os.environ.get("SESSIONDEX_DB", f"{HOME}/.local/share/sessiondex/index.db")
CODEX_DIR = os.environ.get("SESSIONDEX_CODEX", f"{HOME}/.codex")
CLAUDE_DIR = os.environ.get("SESSIONDEX_CLAUDE", f"{HOME}/.claude/projects")
PI_DIR = os.environ.get("SESSIONDEX_PI", f"{HOME}/.pi/agent/sessions")
OPENCODE_DB = os.environ.get("SESSIONDEX_OPENCODE", f"{HOME}/.local/share/opencode/opencode.db")
MAX_MESSAGE_CHARS = 100_000
AGENTS = ("codex", "claude", "opencode", "pi")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, agent TEXT NOT NULL, native_id TEXT NOT NULL,
  title TEXT, cwd TEXT, kind TEXT NOT NULL, parent TEXT,
  started_at INTEGER, updated_at INTEGER, source TEXT,
  fingerprint TEXT, msg_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, seq INTEGER NOT NULL,
  role TEXT NOT NULL, ts INTEGER, text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, seq);
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  text, content='messages', content_rowid='id',
  tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
"""

# ---------------------------------------------------------------- text hygiene

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)", re.S),
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|passw(?:or)?d)(\"?\s*[:=]\s*[\"']?)[^\s\"',;]{8,}"),
]


def redact(text):
    for pattern in SECRET_PATTERNS:
        if pattern.groups == 2:
            text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}[REDACTED]", text)
        elif pattern.groups == 1:
            text = pattern.sub(lambda m: f"{m.group(1)} [REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text


# Wrappers around real content: keep the inner part, drop the envelope.
# Voice input arrives as <realtime_delegation><input>...</input>, for example.
UNWRAP = [
    (re.compile(r"<(realtime_delegation|codex_delegation)\b[^>]*>.*?<input>(.*?)</input>.*?</\1>", re.S), r"\2"),
    (re.compile(r"<goal_context\b[^>]*>.*?<objective>(.*?)</objective>.*?</goal_context>", re.S), r"\1"),
    (re.compile(r"<bash-input>(.*?)</bash-input>", re.S), r"$ \1"),
    (re.compile(r"<command-name>(.*?)</command-name>", re.S), r"\1"),
    (re.compile(r"<command-args>(.*?)</command-args>", re.S), r"\1"),
]
# Pure machine content: remove entirely.
INJECTED_BLOCKS = re.compile(
    r"<(system-reminder|environment_context|user_instructions|local-command-caveat|"
    r"local-command-stdout|local-command-stderr|turn_aborted|subagent_notification|"
    r"in-app-browser-context|recommended_plugins|heartbeat|task-notification|skill|"
    r"bash-stdout|bash-stderr|command-message)\b[^>]*>.*?</\1>",
    re.S,
)
INJECTED_PREFIXES = ("# AGENTS.md instructions", "<INSTRUCTIONS>", "<permissions instructions>")


def clean(text):
    """Strip harness-injected context, leaving what a person or model wrote."""
    if not isinstance(text, str):
        return ""
    for pattern, replacement in UNWRAP:
        text = pattern.sub(replacement, text)
    text = INJECTED_BLOCKS.sub("", text).strip()
    if text.startswith(INJECTED_PREFIXES):
        return ""
    return text


def block_text(content):
    """Join text from a string or a list of typed content blocks."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") in ("text", "input_text", "output_text"):
            parts.append(block.get("text") or "")
    return "\n".join(p for p in parts if p)


def to_ms(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value if value > 1e11 else value * 1000)
    try:
        return int(datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def one_line(text, limit=80):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def read_ro(path):
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=30)


def read_lines(path):
    """Yield parsed JSON objects from a .jsonl or .jsonl.zst file."""
    if path.endswith(".zst"):
        try:
            import zstandard
            with open(path, "rb") as fh:
                raw = zstandard.ZstdDecompressor().stream_reader(fh).read()
        except ImportError:
            raw = subprocess.run(["zstd", "-dc", path], capture_output=True, check=True).stdout
        stream = io.StringIO(raw.decode("utf-8", "replace"))
    else:
        stream = open(path, encoding="utf-8", errors="replace")
    with stream:
        for line in stream:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield row


def file_fingerprint(path):
    stat = os.stat(path)
    return f"{stat.st_mtime_ns}:{stat.st_size}"


# ---------------------------------------------------------------- readers
# A reader yields (session_dict, load_messages) pairs. load_messages is only
# called for new or changed sessions and returns [(role, ts_ms, text), ...].


def codex_rollout_messages(path):
    """Fallback for threads with no history rows. Rollouts mix injected context
    into the user role, so clean() does the real work here."""
    for candidate in (path, f"{path}.zst"):
        if os.path.isfile(candidate):
            path = candidate
            break
    else:
        return []
    out = []
    for row in read_lines(path):
        payload = row.get("payload")
        if row.get("type") != "response_item" or not isinstance(payload, dict):
            continue
        if payload.get("type") == "message" and payload.get("role") in ("user", "assistant"):
            text = clean(block_text(payload.get("content")))
            if text:
                out.append((payload["role"], to_ms(row.get("timestamp")), text))
    return out


def codex_kind(source):
    if source and source.startswith("{"):
        return "guardian" if '"guardian"' in source else "subagent"
    return "main"


def read_codex():
    state_path = f"{CODEX_DIR}/state_5.sqlite"
    history_path = f"{CODEX_DIR}/thread_history_1.sqlite"
    if not os.path.exists(state_path):
        return
    state = read_ro(state_path)
    history = read_ro(history_path) if os.path.exists(history_path) else None

    def loader(thread_id, rollout_path):
        def load():
            rows = []
            if history is not None:
                rows = history.execute(
                    "SELECT item_type, created_at_ms, item_json FROM thread_items "
                    "WHERE thread_id=? AND item_type IN ('userMessage','agentMessage') "
                    "ORDER BY rollout_ordinal",
                    (thread_id,),
                ).fetchall()
            out = []
            for item_type, ts, item_json in rows:
                item = json.loads(item_json)
                text = clean(block_text(item.get("content")) or item.get("text") or "")
                if text:
                    out.append(("user" if item_type == "userMessage" else "assistant", ts, text))
            return out or codex_rollout_messages(rollout_path)
        return load

    query = (
        "SELECT id, rollout_path, created_at_ms, updated_at_ms, created_at, updated_at, source, cwd, "
        "name, title, first_user_message, preview FROM threads"
    )
    for (tid, rollout, c_ms, u_ms, c_s, u_s, source, cwd, name, title, first, preview) in state.execute(query).fetchall():
        kind = codex_kind(source)
        updated = to_ms(u_ms or u_s)
        session = dict(
            agent="codex", native_id=tid, kind=kind, cwd=cwd, parent=None, source=rollout,
            title=name or title or first or preview, started_at=to_ms(c_ms or c_s), updated_at=updated,
            fingerprint=f"{updated}",
        )
        # Guardian threads are automated reviews: counted, never indexed.
        yield session, (lambda: []) if kind == "guardian" else loader(tid, rollout)


def claude_parse(path):
    """Return (messages, title, cwd) from one Claude Code transcript."""
    messages, seen, title, cwd = [], set(), None, None
    for row in read_lines(path):
        kind = row.get("type")
        cwd = cwd or row.get("cwd")
        if kind == "custom-title":
            title = row.get("customTitle") or title
        elif kind == "ai-title" and not title:
            title = row.get("aiTitle")
        if kind not in ("user", "assistant") or row.get("isMeta"):
            continue
        uuid = row.get("uuid")
        if uuid in seen:
            continue
        seen.add(uuid)
        text = clean(block_text((row.get("message") or {}).get("content")))
        if text:
            messages.append((kind, to_ms(row.get("timestamp")), text))
    return messages, title, cwd


def read_claude():
    # Exact depths only: plugins also drop unrelated .jsonl logs in these folders.
    paths = glob.glob(f"{CLAUDE_DIR}/*/*.jsonl") + glob.glob(f"{CLAUDE_DIR}/*/*/subagents/*.jsonl")
    for path in paths:
        is_sub = "/subagents/" in path
        stem = os.path.basename(path)[: -len(".jsonl")]
        native = f"{os.path.basename(os.path.dirname(os.path.dirname(path)))}/{stem}" if is_sub else stem
        stat = os.stat(path)
        session = dict(
            agent="claude", native_id=native, kind="subagent" if is_sub else "main",
            cwd=None, parent=None, source=path, title=None, started_at=None,
            updated_at=int(stat.st_mtime * 1000), fingerprint=file_fingerprint(path),
        )

        def load(path=path, session=session):
            messages, title, cwd = claude_parse(path)
            session["title"], session["cwd"] = title, cwd
            return messages

        yield session, load


def read_pi():
    for path in glob.glob(f"{PI_DIR}/**/*.jsonl", recursive=True):
        stat = os.stat(path)
        session = dict(
            agent="pi", native_id=os.path.basename(path)[: -len(".jsonl")], kind="main",
            cwd=None, parent=None, source=path, title=None, started_at=None,
            updated_at=int(stat.st_mtime * 1000), fingerprint=file_fingerprint(path),
        )

        def load(path=path, session=session):
            out = []
            for row in read_lines(path):
                if row.get("type") == "session":
                    session["cwd"] = row.get("cwd")
                    session["native_id"] = row.get("id") or session["native_id"]
                message = row.get("message")
                if row.get("type") == "message" and isinstance(message, dict) and message.get("role") in ("user", "assistant"):
                    text = clean(block_text(message.get("content")))
                    if text:
                        out.append((message["role"], to_ms(row.get("timestamp")), text))
            return out

        yield session, load


def read_opencode():
    if not os.path.exists(OPENCODE_DB):
        return
    db = read_ro(OPENCODE_DB)

    def loader(session_id):
        def load():
            roles = {
                mid: json.loads(data).get("role")
                for mid, data in db.execute("SELECT id, data FROM message WHERE session_id=?", (session_id,))
            }
            out = []
            rows = db.execute(
                "SELECT message_id, time_created, data FROM part WHERE session_id=? ORDER BY time_created, id",
                (session_id,),
            )
            for message_id, ts, data in rows:
                part = json.loads(data)
                if part.get("type") != "text" or part.get("synthetic") or part.get("ignored"):
                    continue
                text = clean(part.get("text"))
                role = roles.get(message_id)
                if text and role in ("user", "assistant"):
                    out.append((role, to_ms(ts), text))
            return out
        return load

    rows = db.execute("SELECT id, parent_id, directory, title, time_created, time_updated FROM session").fetchall()
    for sid, parent, directory, title, created, updated in rows:
        session = dict(
            agent="opencode", native_id=sid, kind="subagent" if parent else "main", cwd=directory,
            parent=parent, source=OPENCODE_DB, title=title, started_at=to_ms(created),
            updated_at=to_ms(updated), fingerprint=f"{updated}",
        )
        yield session, loader(sid)


READERS = {"codex": read_codex, "claude": read_claude, "opencode": read_opencode, "pi": read_pi}

# ---------------------------------------------------------------- index


def open_index():
    os.makedirs(os.path.dirname(DB_PATH), mode=0o700, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30)
    os.chmod(DB_PATH, 0o600)  # transcripts stay private even after redaction
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript(SCHEMA)
    return db


def store(db, session, messages):
    sid = f"{session['agent']}:{session['native_id']}"
    db.execute("DELETE FROM messages WHERE session_id=?", (sid,))
    db.execute("DELETE FROM sessions WHERE id=?", (sid,))
    first_user = next((m[2] for m in messages if m[0] == "user"), None)
    title = one_line(redact(clean(session.get("title")) or first_user or ""), 120)
    stamps = [m[1] for m in messages if m[1]]
    started = session.get("started_at") or (min(stamps) if stamps else session.get("updated_at"))
    db.execute(
        "INSERT INTO sessions (id, agent, native_id, title, cwd, kind, parent, started_at, updated_at, "
        "source, fingerprint, msg_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (sid, session["agent"], session["native_id"], title, session.get("cwd"), session["kind"],
         session.get("parent"), started, session.get("updated_at"), session.get("source"),
         session["fingerprint"], len(messages)),
    )
    # The title is stored as seq -1 so title words are searchable too.
    rows = [(sid, -1, "title", started, title)] if title else []
    for seq, (role, ts, text) in enumerate(messages):
        rows.append((sid, seq, role, ts, redact(text[:MAX_MESSAGE_CHARS])))
    db.executemany("INSERT INTO messages (session_id, seq, role, ts, text) VALUES (?,?,?,?,?)", rows)


def cmd_index(args):
    db = open_index()
    agents = [args.agent] if args.agent else list(AGENTS)
    for agent in agents:
        started = time.time()
        known = dict(db.execute("SELECT native_id, fingerprint FROM sessions WHERE agent=?", (agent,)))
        known_sources = {}
        if agent == "pi":  # Pi's native id is only known after reading the file
            known_sources = dict(db.execute("SELECT source, fingerprint FROM sessions WHERE agent='pi'"))
        seen = changed = failed = 0
        for session, load in READERS[agent]():
            seen += 1
            previous = known_sources.get(session["source"]) if agent == "pi" else known.get(session["native_id"])
            if not args.full and previous == session["fingerprint"]:
                continue
            try:
                store(db, session, load())
                changed += 1
            except Exception as error:  # one corrupt session must not stop the run
                failed += 1
                print(f"  skipped {agent}:{session['native_id']}: {error}", file=sys.stderr)
            if changed % 200 == 0:
                db.commit()
        db.commit()
        print(f"{agent:9} {seen:6} sessions, {changed:6} updated, {failed} failed ({time.time() - started:.1f}s)")
    db.execute("INSERT INTO messages_fts(messages_fts) VALUES ('optimize')")
    db.commit()


# ---------------------------------------------------------------- queries


def rank_score(relevance, age_days, role):
    """Order search hits. Higher is better.

    relevance: BM25 strength of the match (positive; roughly 1 to 20)
    age_days:  days since the session was last updated
    role:      'user', 'assistant' or 'title'
    """
    return relevance / (1 + age_days / 90)


def fts_query(text, raw=False):
    if raw:
        return text
    terms = re.findall(r'[^\s"]+', text)
    return " ".join('"' + term + '"' for term in terms)


def filters(args, alias="s"):
    clauses, params = [], []
    if not args.all:
        clauses.append(f"{alias}.kind='main'")
    if args.agent:
        clauses.append(f"{alias}.agent=?")
        params.append(args.agent)
    if args.days:
        clauses.append(f"{alias}.updated_at>=?")
        params.append(int((time.time() - args.days * 86400) * 1000))
    if args.cwd:
        clauses.append(f"{alias}.cwd LIKE ?")
        params.append(f"%{args.cwd}%")
    return clauses, params


def when(ms):
    return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M") if ms else "unknown"


def resume_command(agent, native_id, source, cwd):
    prefix = f"cd {json.dumps(cwd)} && " if cwd else ""
    return {
        "codex": f"codex resume {native_id}",
        "claude": f"{prefix}claude --resume {native_id}",
        "opencode": f"{prefix}opencode --session {native_id}",
        "pi": f"{prefix}pi --session {json.dumps(source)}",
    }[agent]


def short_home(path):
    return (path or "").replace(HOME, "~")


def cmd_recent(args):
    db = open_index()
    clauses, params = filters(args)
    clauses.append("s.msg_count>0")
    rows = db.execute(
        f"SELECT s.id, s.agent, s.title, s.cwd, s.updated_at, s.msg_count FROM sessions s "
        f"WHERE {' AND '.join(clauses)} ORDER BY s.updated_at DESC LIMIT ?",
        params + [args.n],
    ).fetchall()
    if args.json:
        keys = ("id", "agent", "title", "cwd", "updated_at", "msg_count")
        print(json.dumps([dict(zip(keys, row)) for row in rows], ensure_ascii=False, indent=2))
        return
    for sid, agent, title, cwd, updated, count in rows:
        print(f"{when(updated)}  {agent:8} {count:5} msgs  {one_line(title, 64)}")
        print(f"{'':18}{sid}  {short_home(cwd)}")


def cmd_search(args):
    db = open_index()
    clauses, params = filters(args)
    if args.role:
        clauses.append("m.role=?")
        params.append(args.role)
    where = " AND ".join(["messages_fts MATCH ?"] + clauses)
    try:
        rows = db.execute(
            f"SELECT s.id, s.agent, s.title, s.cwd, s.updated_at, m.role, m.ts, -bm25(messages_fts), "
            f"snippet(messages_fts, 0, '[', ']', ' … ', 24) "
            f"FROM messages_fts JOIN messages m ON m.id=messages_fts.rowid "
            f"JOIN sessions s ON s.id=m.session_id WHERE {where} "
            f"ORDER BY bm25(messages_fts) LIMIT 2000",
            [fts_query(args.query, args.raw)] + params,
        ).fetchall()
    except sqlite3.OperationalError as error:
        sys.exit(f"Bad search query: {error}")
    now = time.time() * 1000
    best = {}
    for sid, agent, title, cwd, updated, role, ts, relevance, snippet in rows:
        age_days = max(0.0, (now - (updated or now)) / 86_400_000)
        score = rank_score(relevance, age_days, role)
        hit = best.setdefault(sid, dict(id=sid, agent=agent, title=title, cwd=cwd, updated_at=updated,
                                        score=-math.inf, hits=0))
        hit["hits"] += 1
        if score > hit["score"]:
            hit.update(score=round(score, 3), role=role, snippet=one_line(snippet, 220))
    results = sorted(best.values(), key=lambda hit: hit["score"], reverse=True)[: args.n]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if not results:
        print("No matches.")
    for hit in results:
        print(f"{when(hit['updated_at'])}  {hit['agent']:8} {hit['hits']:3} hits  {one_line(hit['title'], 64)}")
        print(f"{'':18}{hit['id']}  {short_home(hit['cwd'])}")
        print(f"{'':18}{hit['role']}: {hit['snippet']}\n")


def cmd_show(args):
    db = open_index()
    # The prefix may omit the "agent:" part.
    matches = db.execute(
        "SELECT id, agent, native_id, title, cwd, kind, started_at, updated_at, source, msg_count "
        "FROM sessions WHERE id LIKE ? OR native_id LIKE ? LIMIT 6",
        (f"{args.id}%", f"{args.id}%"),
    ).fetchall()
    if not matches:
        sys.exit(f"No session matches {args.id}")
    if len(matches) > 1:
        sys.exit("Ambiguous id, matches:\n" + "\n".join(f"  {row[0]}" for row in matches))
    sid, agent, native, title, cwd, kind, started, updated, source, count = matches[0]
    messages = db.execute(
        "SELECT seq, role, ts, text FROM messages WHERE session_id=? AND seq>=0 ORDER BY seq", (sid,)
    ).fetchall()
    if args.tail:
        messages = messages[-args.tail:]
    resume = resume_command(agent, native, source, cwd)
    if args.json:
        print(json.dumps(dict(id=sid, agent=agent, title=title, cwd=cwd, kind=kind, started_at=started,
                              updated_at=updated, msg_count=count, resume=resume,
                              messages=[dict(seq=m[0], role=m[1], ts=m[2], text=m[3]) for m in messages]),
                         ensure_ascii=False, indent=2))
        return
    print(f"{title}\n{agent} · {kind} · {count} messages · {when(started)} to {when(updated)}")
    print(f"Folder: {short_home(cwd)}\nResume: {resume}\n")
    for _, role, ts, text in messages:
        print(f"--- {role} · {when(ts)}\n{text}\n")


def cmd_stats(args):
    db = open_index()
    rows = db.execute(
        "SELECT agent, kind, COUNT(*), SUM(msg_count), SUM(msg_count=0), MAX(updated_at) "
        "FROM sessions GROUP BY 1, 2 ORDER BY 1, 2"
    ).fetchall()
    size = os.path.getsize(DB_PATH)
    if args.json:
        keys = ("agent", "kind", "sessions", "messages", "empty", "latest")
        print(json.dumps(dict(db_bytes=size, groups=[dict(zip(keys, row)) for row in rows]), indent=2))
        return
    print(f"{'agent':9} {'kind':9} {'sessions':>8} {'messages':>9} {'empty':>6}  latest")
    for agent, kind, sessions, messages, empty, latest in rows:
        print(f"{agent:9} {kind:9} {sessions:8} {messages:9} {empty:6}  {when(latest)}")
    print(f"\nIndex: {short_home(DB_PATH)} ({size / 1_048_576:.0f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Search local AI agent sessions.")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--agent", choices=AGENTS)
        p.add_argument("--days", type=float, help="only sessions updated in the last N days")
        p.add_argument("--cwd", help="only sessions whose folder contains this text")
        p.add_argument("--all", action="store_true", help="include subagent sessions")
        p.add_argument("--json", action="store_true")

    p = sub.add_parser("index")
    p.add_argument("--agent", choices=AGENTS)
    p.add_argument("--full", action="store_true", help="reread every session")
    p.set_defaults(run=cmd_index)

    p = sub.add_parser("recent")
    common(p)
    p.add_argument("-n", type=int, default=20)
    p.set_defaults(run=cmd_recent)

    p = sub.add_parser("search")
    p.add_argument("query")
    common(p)
    p.add_argument("-n", type=int, default=10)
    p.add_argument("--role", choices=("user", "assistant", "title"))
    p.add_argument("--raw", action="store_true", help="pass the query to FTS5 unchanged")
    p.set_defaults(run=cmd_search)

    p = sub.add_parser("show")
    p.add_argument("id")
    p.add_argument("--tail", type=int)
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_show)

    p = sub.add_parser("stats")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_stats)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
