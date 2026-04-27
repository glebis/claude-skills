---
name: session-finder
description: Index and search Claude Code sessions using semantic embeddings (Gemini). Find past sessions by topic, relaunch the best match. Triggers on "find session", "which session did I", "relaunch the session where", "session about X".
---

# Session Finder

Semantic search across Claude Code sessions using Gemini embeddings.

## Commands

### Index sessions
```bash
python3 ~/.claude/skills/session-finder/scripts/session_finder.py index [--max-age-days 90]
```

### Search
```bash
python3 ~/.claude/skills/session-finder/scripts/session_finder.py search "query" [--top 5]
```

### Open best match directly
```bash
python3 ~/.claude/skills/session-finder/scripts/session_finder.py open "query"
```

### Stats
```bash
python3 ~/.claude/skills/session-finder/scripts/session_finder.py stats
```

## How it works

1. **Document extraction** — deterministic, no LLM. Each session JSONL is parsed into a structured document:
   - `away_summary` events (pre-existing Claude recaps) if available
   - First user message (task description)
   - Follow-up user messages (condensed)
   - First assistant response
   - Tools used
   - Project name
2. **Embedding** — documents are embedded with `gemini-embedding-exp-03-07` via `llm` CLI
3. **Storage** — SQLite at `~/.claude/session-finder.db`
4. **Search** — query is embedded, cosine similarity ranks all sessions, top match is the default to open

## Workflow

When user asks to find a session:
1. Run `search` with their query
2. Present results with confidence scores
3. Offer to resume the top match via `claude --resume <id>`
