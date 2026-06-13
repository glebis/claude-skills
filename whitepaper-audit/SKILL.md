---
name: whitepaper-audit
description: Audit a white paper or long-form technical document against a research-grounded best-practices checklist. Two lanes — deterministic script checks (readability, undefined acronyms, structure blocks, broken links) plus an LLM-judge review (overclaims, inconsistent numbers, buried lede, limitations honesty, audience fit). Produces a prioritized P0–P2 findings report by default; applies fixes on explicit request (TDD for any code changes). Use when the user says "audit this white paper", "review my paper against best practices", "check this doc for overclaims", "whitepaper QA", "is this paper ready to publish", or wants prioritized recommendations on a technical document.
---

# whitepaper-audit

Audit a markdown white paper in two lanes and produce one merged, prioritized report.

## Inputs

- **Document path** (required) — markdown source, not PDF.
- **Stated audience** (ask if not given) — severity of `audience-fit`/`jargon-undefined`
  depends on it. Default: "technical practitioners, non-academic".
- **Mode** — `recommend` (default) or `fix` (only on explicit request).

## Workflow

### 1. Lane 1 — deterministic

```bash
python3 scripts/check_doc.py <doc.md> --offline [--target-grade N] [--allow ACRO]
```

Drop `--offline` to also check http(s) links (HEAD→GET, timeouts; only *broken* is a
finding). Output: JSON findings, schema in DESIGN.md.

### 2. Lane 2 — LLM judge

Dispatch a **subagent** (fresh context — never judge a document you wrote in the same
context) with `references/audit-prompt.md`, filling {PATH} and {AUDIENCE}, plus the
`[judge]` criteria from `references/checklist.md`. The judge returns JSON findings.

Judge calibration rules are binding: verbatim quotes required; no P0 at low confidence;
"needs verification", never "factually wrong".

### 3. Merge

Dedupe by (location, issue type) keeping both lane attributions; sort P0 → P1 → P2, then
confidence. Cross-reference: a lane-1 broken link that supports a claim (judge decides
materiality) is P1; decorative → P2.

### 4. Report (default mode)

Write a markdown report: summary verdict, findings table (id, severity, confidence,
location, fix), then details. Recommend; do not edit.

### 5. Fix mode (only when explicitly requested)

Apply fixes **P0-first**. Any change to code goes through superpowers
test-driven-development (test first, watch it fail). Prose fixes: edit, then **re-run the
full audit** and report cleared vs remaining findings.

## Evals

Before trusting a new/changed judge prompt, run `evals/README.md` procedure (planted
defects + clean control; pass criteria inside). Lane 1 is covered by
`scripts/tests/test_check_doc.py` (pytest).

## Files

- `scripts/check_doc.py` — lane 1 (stdlib-only; `--help` for flags)
- `references/checklist.md` — operational criteria, both lanes
- `references/audit-prompt.md` — judge prompt template
- `evals/` — judge validation cases + pass criteria
- `DESIGN.md` — architecture decisions (v0.2, Codex-audited)
