---
name: qmd-search
description: This skill should be used to search the local Obsidian vault / markdown knowledge base by meaning, not just keywords, using the on-device qmd engine (BM25 + vector + LLM rerank). Trigger when the user asks to "search my vault/notes", "find notes about X", "what do my notes say about Y", "do I have anything on Z", "semantic search my knowledge base", or wants concept/cross-lingual retrieval over markdown. Fully local — nothing leaves the machine.
---

# qmd Search

Search a local markdown knowledge base semantically with [`qmd`](https://github.com/tobi/qmd). Three
modes — BM25 keywords, vector similarity, and hybrid (expansion + rerank) — all running on-device.
The key advantage over Obsidian's built-in search: it matches **meaning**, finds notes that share no
words with the query, and works **across languages** (e.g. a Russian query retrieves English notes).

## When to use which mode

- **hybrid (`query`)** — default. A real question or fuzzy intent ("how do I stop overengineering").
  Best quality; first run downloads reranker/expansion models (~one-time slow).
- **vector (`vsearch`)** — fast concept lookup ("notes about embodied computing").
- **BM25 (`search`)** — an exact keyword, name, or filename. Instant, no model.

## Primary usage — the wrapper

Use the bundled wrapper; it suppresses qmd's stderr spinner, formats results as `score  path`
(parsing qmd's JSON, so commas in filenames are safe), and makes a best-effort refusal to run
during an active `qmd embed` (which would return empty results — override with `--force`):

```bash
~/.claude/skills/qmd-search/scripts/qmd-search.sh [-m query|search|vsearch] [-n N] [-c COLLECTION] [--json] [--full] <query...>
```

Examples:
```bash
qmd-search.sh "what helps with anxiety"                 # hybrid (default)
qmd-search.sh -m vsearch -n 8 "behavioral health from photos"
qmd-search.sh -m search sensorium                       # BM25 keyword
qmd-search.sh --json "agent orchestration"              # structured output for further processing
qmd-search.sh --full "quarterly planning"               # include document content
```

After getting hits, read the top files directly (they are normal vault paths) or fetch slices with
`qmd get "<path>:<line>" -l <N>`.

## Setup / indexing (only if `qmd status` shows the vault is not indexed)

```bash
qmd collection add ~/Brains/brain --name brain        # index the vault
qmd context add qmd://brain "short description of the vault"
qmd embed                                              # build vectors; re-run until status shows 0 pending
qmd cleanup                                            # compact the index
```

Refresh after large edits: `qmd update && qmd embed`. Check health any time with `qmd status`.

## Operational rules (do not skip)

- **One embed at a time**, and **never search while embedding** — both cause empty/garbage results.
  The wrapper guards searches; for manual `qmd` calls, check `qmd status` first.
- If embedding never reaches 0 pending, **check disk space** (`df -h`) — a full disk fails writes
  silently. See `references/cli-reference.md` → "Operational gotchas".
- Vector scores are modest (~0.4–0.6); judge by **ranking**, not the absolute number.

## Reference

Full command surface, query grammar (`lex:`/`vec:`/`hyde:`), output formats, models, and recovery
steps are in `references/cli-reference.md`. The qmd MCP server (`qmd mcp`, stdio) is available for
agent integrations.
