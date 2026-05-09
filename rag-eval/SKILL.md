---
name: rag-eval
description: Iterate on RAG systems with structured evals instead of eyeballing. This skill should be used when the user is tuning a RAG pipeline — changing retrieval prompts, swapping models, adjusting chunking, or debugging poor answers — and wants a cheap, ranked set of experiments with cost tracking and structured feedback on the stack. Also use when the user asks "how do I know if my RAG is working?", "this RAG eval is burning money", or "what should I try next on retrieval?".
---

# rag-eval

## Purpose

Replace the "tweak → squint → swap model → burn credits" loop with a single command that runs a grid of eval variants on the user's gold-set, ranks them by a cost-aware score, and returns structured feedback on architecture, stack, and likely-issues. Draws on evidence-based RAG practices and learns from the user's past runs.

## When to use

Trigger on: "help me test a RAG", "tune my RAG", "my RAG is bad", "compare retrieval prompts", "how do I eval this", "what's the best embedding model for X", "my RAG eval is expensive". Also trigger when the user reports burning OpenRouter / OpenAI credits with no clear signal of improvement.

## Prerequisites — gather before running

Collect these from the user before the first sweep. Many are optional with sensible defaults; always confirm the ones that gate cost.

1. **RAG codebase root** — path to the repo/module under test.
2. **Gold-set** — at least 10 Q&A pairs. If missing, offer to generate a starter gold-set from the user's dataset (LLM-synthesized, human-reviewed). See `references/best-practices.md`.
3. **Dataset** — the corpus the RAG retrieves over.
4. **Budget cap** — hard dollar limit per run (default: $2 if user doesn't specify). **Always confirm before any sweep.**
5. **Provider keys** — `OPENROUTER_API_KEY` or `OPENAI_API_KEY` (read from env).
6. **Vector-store config** — collection name, embedding model, chunk size (read from repo; confirm if ambiguous).
7. **Eval history path** (optional) — defaults to `.rag-eval/history.jsonl` in the repo root.

## Workflow

Follow this order. Refer to `references/best-practices.md` for the canonical checklist and `references/evidence-base.md` for the research-backed defaults.

### Step 0 — (Optional) Ingest a prior iteration session

When the user provides a session ID (Claude Code transcript, skill-studio session, or a Fathom meeting), run the **deterministic ingest** *first* — no LLM calls. This extracts only the useful signals (models tried, prompt variants, cost events, eval results) as compact JSON, so the rest of the skill works off a tiny structured bundle instead of a long raw transcript.

```bash
python scripts/session_ingest.py <session_id> > /tmp/rag-eval-bundle.json
# or with a direct path:
python scripts/session_ingest.py --path /path/to/transcript.jsonl > /tmp/rag-eval-bundle.json
```

The bundle includes: `models_tried`, `prompts_tried` (hashes only), `iterations`, `total_cost_usd`, `summary_stats`. Feed this into Step 1 — do not paste the raw transcript.

**Why this matters:** transcripts can be 100k+ tokens of noise. The ingest script does regex extraction only, keeping the LLM budget for the actual audit + sweep planning. This is a hard requirement, not an optimization.

### Step 1 — Audit the stack

Read `references/best-practices.md` and inspect the user's repo + vector-store config. Produce a structured report covering:
- Architecture (retrieval type: dense / hybrid / rerank; chunking strategy; prompt structure)
- Tech stack (embedding model, LLM, vector store)
- Resources (dataset size, gold-set size, prior eval runs)
- Risks (known anti-patterns, missing pieces)

Present the report to the user and ask which issues to address first.

### Step 2 — Propose a sweep plan

Based on the audit, propose 3–8 variants to test. Keep the grid small on the first run (default: 2 prompts × 2 models × 1 retrieval variant = 4 cells). Estimate cost using gold-set size × variants × avg tokens × provider pricing. **Present the cost estimate and wait for user confirmation before running.**

### Step 3 — Run the sweep

Use `scripts/eval_sweep.py` (see the script header for invocation). It reads a config YAML, runs each variant against the gold-set, records per-variant cost and answer quality, and appends to `history.jsonl`.

**Guardrails:**
- Never exceed the budget cap — halt mid-sweep if reached.
- Never mutate the user's repo. Write all artifacts under `.rag-eval/` (gitignore it).
- Confirm before any sweep estimated to exceed the user's cap.

### Step 4 — Rank and report

After the sweep, rank variants by a cost-aware score: `quality × (1 / log(1 + cost))`. Present:
- Top 3 variants with quality metrics and cost
- What changed vs the previous best
- Concrete next experiment to try

Write the full report to `.rag-eval/reports/<timestamp>.md`.

### Step 5 — Self-improve

Before each subsequent run, read `history.jsonl` and factor in what the user has already tried. Avoid re-testing rejected variants. Surface patterns ("models A, B, C all underperformed on multi-hop queries — next try a reranker").

## Reusable resources

- `scripts/eval_sweep.py` — grid-search runner. Reads `eval_config.yaml`, writes results to `history.jsonl`.
- `references/best-practices.md` — evidence-based RAG checklist the agent uses as an anchor.
- `references/evidence-base.md` — pointers to recent RAG research and when each technique helps.
- `assets/eval_config.template.yaml` — starter config to copy into the user's repo.
- `assets/gold_set.template.jsonl` — 3 example Q&A pairs to show the gold-set format.

## Notes

- **Cost is the main failure mode.** Never run without a confirmed budget. Err on the side of smaller sweeps; users can always run again.
- **No repo mutation.** All outputs go under `.rag-eval/` in the target repo.
- **When uncertain about best practices, do web research.** Use `tavily-search` or `firecrawl-research` to pull current evidence, then synthesize into the audit report.
- **Defer to the user.** Before changing any file in the target repo, always confirm.
