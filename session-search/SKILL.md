---
name: session-search
description: This skill should be used when searching Claude Code session transcripts with semantic understanding. Triggers on queries like "find sessions about X", "when did I work on Y", "search previous conversations". Supports natural language queries with synonym matching.
---

# Session Search

Search Claude Code session transcripts by combining keyword pre-filtering with semantic evaluation. Finds previous sessions about specific topics, debugging conversations, research tasks, or any past work.

## Workflow

### Step 1: Run the search script

Execute `scripts/search.py` with the user's query:

```bash
python3 scripts/search.py "<query>" [max_results] [max_age_days]
```

- `query` (required): Natural language search query
- `max_results` (optional, default 10): Maximum results to return
- `max_age_days` (optional, default 90): How far back to search

The script performs keyword pre-filtering across all sessions, then extracts meaningful excerpts from top candidates. Output contains a `SESSIONS_DATA` JSON block.

### Step 2: Evaluate results semantically

After receiving the script output, evaluate each session's relevance to the query. Consider:

- **Synonym matching**: "bug" matches "error", "issue", "problem", "fix"
- **Related concepts**: "debugging" matches sessions with test failures or error messages
- **Tool patterns**: "refactoring" matches Edit-heavy sessions
- **Domain context**: "obsidian" matches vault-related work

Assign a relevance score (0-10) to each session based on excerpt content and query intent.

### Step 3: Present results

Display the top results (up to `max_results`) sorted by relevance, formatted as:

```
### [Relevance: N/10] Project — Date
Summary of what the session was about (1-2 sentences based on excerpts)
`claude --resume <session-id>`
```

If no relevant results are found, report that and suggest alternative queries.

## Session Storage

Sessions are stored as JSONL files in `~/.claude/projects/`. Each file contains events with user/assistant messages and tool calls. The search script handles file discovery and text extraction automatically.

## Customization

To search older sessions or get more results:

```
/session-search "query" 20 180
```
(20 results, 180 days lookback)
