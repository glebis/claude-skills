# qmd CLI reference

Full command surface for [`qmd`](https://github.com/tobi/qmd) (Quick Markdown Search) v2.5.x — a
local-first search engine combining BM25 full-text, vector similarity, and LLM reranking. All
models run on-device (node-llama-cpp); nothing leaves the machine.

## Search commands

| Command | Mode | Notes |
|---|---|---|
| `qmd query <q>` | Hybrid | Query expansion → lex+vec+hyde → LLM rerank. Best quality, slowest. |
| `qmd search <q>` | BM25 | Tokenized full-text. Instant, no model. Best for exact keywords/filenames. |
| `qmd vsearch <q>` | Vector | Cosine similarity over embeddings. Fast semantic/concept lookup. |
| `qmd get <file>[:line] [-l N]` | — | Show one document, optional line slice. |
| `qmd multi-get <pattern>` | — | Batch fetch via glob or comma list. |

### Common search flags
- `-n N` — number of results (default 5)
- `-c <collection>` — restrict to one collection
- `--min-score <0..1>` — drop low-scoring hits
- Output: `--json`, `--files` (docid,score,path,context), `--md`, `--csv`, `--xml`
- `--full` — include full document content
- `--line-numbers`, `--explain` (scoring trace), `--all` (export all matches)

### Output stream note (important for scripting)
The animated spinner and the query-expansion trace (`lex:`/`vec:`/`hyde:` lines) are written to
**stderr**. Redirect `2>/dev/null` to get clean stdout. `--json` and `--files` then parse reliably.

## Query syntax (`qmd query`)
A query is either a single implicit-expand line, or a multi-line typed document:
```
qmd query "how does auth work"                      # implicit expand
qmd query $'lex: CAP theorem\nvec: consistency'     # typed: lexical + vector lines
qmd query $'lex: "exact phrase" sports -baseball'   # phrase + negation in lex
qmd query $'hyde: Hypothetical ideal answer text'   # hyde-only (embeds a fake answer)
```
- `lex:` BM25 term(s); supports `"phrases"` and `-negation`.
- `vec:` text to embed for vector search.
- `hyde:` hypothetical-answer text (HyDE) to embed.
- `intent:` optional first line describing intent.
- Standalone expand queries cannot mix with typed lines.

## Collections & context
```bash
qmd collection add <dir> --name <name>     # index a folder (**/*.md)
qmd collection list|show|rename|remove
qmd context add qmd://<name> "summary"     # human summary; improves relevance
qmd context list|rm
qmd ls [collection[/path]]                 # inspect indexed files
```

## Maintenance
```bash
qmd status                 # index health: files, vectors, pending, models
qmd update [--pull]        # re-index collections (optionally git pull first)
qmd embed [-f] [-c name]   # generate/refresh vectors; -f forces re-embed
  --max-docs-per-batch N   # cap docs per batch (lower if memory-constrained)
  --max-batch-mb N         # cap UTF-8 MB per batch
qmd cleanup                # clear caches + VACUUM the SQLite index
qmd init                   # create a project-local .qmd index
qmd mcp                    # MCP server (stdio) for AI agents
```

## Models (auto-downloaded to `~/.cache/qmd/models`, ~318 MB total)
- Embedding: `embeddinggemma-300M-Q8_0` (multilingual — enables cross-lingual search)
- Reranker: `Qwen3-Reranker-0.6B-Q8_0` (hybrid mode)
- Query expansion: `qmd-query-expansion-1.7B` (hybrid mode)

## Operational gotchas (learned the hard way)
1. **Never run two `qmd embed` at once** — concurrent processes contend on the SQLite index and
   corrupt progress counts. Run embeds sequentially.
2. **Don't search while embedding** — `qmd vsearch`/`query` during an active `qmd embed` competes
   for the GPU/model and returns EMPTY results. Wait for embed to finish. The wrapper script
   refuses to run in this case unless `--force` is passed.
3. **Disk space** — a near-full disk makes embed writes and `qmd cleanup`'s VACUUM fail silently
   with `SQLITE_FULL` (looks like a stall). If embedding won't converge, check `df -h`. Recover a
   bloated write-ahead log with: `sqlite3 ~/.cache/qmd/index.sqlite "PRAGMA wal_checkpoint(TRUNCATE);"`
4. **Embedding is incremental** — large vaults may need `qmd embed` to be re-run until
   `qmd status` shows no "Pending". Re-run after big edits, then `qmd cleanup` to compact.
5. **Vector scores are modest** (~0.4–0.6) with the 300M model — ranking matters, not the absolute number.
6. **`qmd query --json` may exit 134 (SIGABRT)** during model teardown *after* writing complete, valid
   JSON. Treat the output as authoritative, not the exit code. The wrapper script judges success by
   output validity for this reason; raw `qmd query --json` in scripts should do the same (or use `--files`,
   which exits cleanly).

## Prerequisites
- Node ≥ 22 or Bun ≥ 1.0; macOS: `brew install sqlite`.
- Install: `bun install -g @tobilu/qmd` (or `npm install -g @tobilu/qmd`), then trust postinstalls
  (node-llama-cpp builds the local inference binary).
