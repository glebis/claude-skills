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
- **grep (`-m grep`)** — literal fixed-string ripgrep over the .md files. The audit path for
  proper nouns, transliterations, exact phrases, Russian stems/inflections, and absence checks.
  Bypasses the index; matches only the exact script/spelling you type.

## Bilingual / proper-name rule (do not skip)

This vault is bilingual (English/Russian). The embedding model is decent for **concepts** but weak
for **proper nouns / specific entities**, and BM25 only matches the script you type. So:

**Never conclude "it's not in the vault" after one English semantic query.** For names, people,
pets, places, foreign terms, or bilingual topics:
1. Search semantically first (`query` / `vsearch`).
2. Generate likely **native-script** spellings/stems and try them, e.g.
   `Ziggy → Зигги/Зиги`, `dog/pet → собак, пёс, щенок, питомц, животн`. Use **stems** (`собак`
   catches `собака/собаку/собаки`), not just the nominative.
3. Run a **literal pass** before concluding absence: `qmd-search.sh -m grep -n 20 "Зигги"`.
4. Use literal hits to **disambiguate** close names (e.g. `Зигги` the pet vs. `Зигмунд` Freud).
5. If everything fails, say "I didn't find it with these queries: …" and list the terms tried —
   not "it's not in the vault." Raise `-n` to ~20 for absence checks.

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
qmd-search.sh -m grep -n 20 "Зигги"                     # literal native-spelling / absence check
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

## MCP (native tools) vs. the CLI wrapper

qmd ships an MCP server (`qmd mcp`, stdio) exposing tools `query`, `get`, `multi_get`, `status`.
If it's registered in the host (e.g. `.mcp.json`), **prefer the native `query` tool** for hybrid
search — it returns structured results with no spinner/JSON-parsing/exit-code quirks. Register with:

```json
{ "mcpServers": { "qmd": { "command": "qmd", "args": ["mcp"] } } }
```

Use the **wrapper** (`scripts/qmd-search.sh`) when you need what MCP doesn't cover: BM25-only
(`search`), vector-only (`vsearch`), the literal/native-script **`grep`** pass, the fused **`find`**
mode, `--snippet`, or `--min-score`. The bilingual/proper-name rule above applies to both paths.

## Quality / evals

`evals/fixture.example.json` + `scripts/run-evals.sh` run `qmd bench` to score search quality
(precision/recall/MRR per backend). Baseline and interpretation: `evals/BASELINE.md`. Re-run after
changing the wrapper, the index, or the embedding model; a drop vs. baseline is a regression.

## Reference

Full command surface, query grammar (`lex:`/`vec:`/`hyde:`), output formats, models, and recovery
steps are in `references/cli-reference.md`.
