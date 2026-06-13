# whitepaper-audit — design spec (v0.2, post-Codex-audit)

Date: 2026-06-03 · Author: Gleb Kalinin + Claude · Codex audit: incorporated (v0.1 → v0.2)

## Purpose

A general-purpose skill that audits a technical/scientific white paper (or any long-form
explanatory document) against a research-grounded best-practices checklist, and either
(a) produces a prioritized P0–P2 findings report (default), or (b) applies corrections on
request. First target: `~/ai_projects/confide/docs/WHITEPAPER.md`.

## Architecture

```
whitepaper-audit/
├── SKILL.md                      # triggers, workflow, modes
├── DESIGN.md                     # this file
├── references/
│   ├── checklist.md              # operational rules w/ examples+counterexamples, tagged [script]/[judge]
│   └── audit-prompt.md           # LLM-judge prompt template
├── scripts/
│   ├── check_doc.py              # deterministic checks (stdlib-only)
│   └── tests/test_check_doc.py   # pytest, built TDD
└── evals/
    ├── README.md                 # pass criteria, runner procedure
    └── cases/                    # planted-defect docs + clean + near-clean controls
```

## Finding schema (both lanes — the merge contract)

Every finding, from either lane:

```json
{
  "check_id": "acronym-undefined",      // stable id from checklist.md
  "lane": "script" | "judge",
  "severity": "P0" | "P1" | "P2",
  "confidence": "high" | "medium" | "low",
  "location": "§5.2 / quoted line",
  "evidence_quote": "…verbatim excerpt…",
  "rationale": "why this is a problem",
  "suggested_fix": "concrete edit"
}
```

Merged report: dedupe by (location, issue type), keep both lane attributions when merged,
sort P0→P2 then confidence. **Severity = impact × confidence** — a low-confidence
high-impact issue is reported at the lower severity with a "verify" note, never silently
promoted.

## Two-lane audit

### Lane 1 — deterministic (`check_doc.py`, TDD)

Stdlib-only, Python 3.10+. JSON findings on stdout, exit 0; never crashes on malformed
markdown. **Preprocessing applies to all checks:** strip code blocks, tables, URLs,
headings, footnote markers, and HTML comments before text metrics.

| check_id | Method | Severity gating |
|---|---|---|
| `readability` | Flesch-Kincaid grade per section (heuristic syllable counter — trend-level, documented as such) + **top-5 hardest sentences** | P2 by default; P1 only when an audience-critical section (abstract, intro) exceeds target by >3 grades. Default target ≤ 13. |
| `acronym-undefined` | **Acronyms only** (2–6 capitals), with allowlist (units, common: PDF, URL, USA…) and config term-map. Defined = `Full Term (ABC)` / `ABC (Full Term)` / glossary entry, at or before first use. Plural/possessive normalized. | P1, high confidence |
| `structure` | Required blocks present: title, abstract/exec summary, date/version, author, limitations, glossary (configurable set) | Missing limitations → P0 candidate (judge confirms materiality); missing glossary → P2 if terms otherwise defined; others P1 |
| `links` | Relative paths: exist on disk. http(s): HEAD → small-GET fallback, timeout; classify **broken / unreachable / skipped / uncertain** — only *broken* is a finding; `--offline` skips network | P1 if supporting a claim (judge cross-references), else P2 |

Broader jargon (bolded terms, lowercase terms of art) is **not** lane-1: the judge flags
"possible undefined jargon" as a soft finding.

### Lane 2 — LLM judge (`audit-prompt.md`)

Judged criteria (refined by the best-practices research): **apparent overclaim /
unsupported claim / internally inconsistent number** (NOT "factual error" — the judge has
no retrieval; it flags "needs verification", it does not adjudicate truth); marketing
language in a technical claim; buried lede; honesty about limitations and uncertainty;
audience fit; flow; table/figure clarity; possible undefined jargon (soft).

Judge outputs findings in the shared schema, with `confidence` mandatory.

### Severity rubric (impact × confidence, with per-check examples)

- **P0 — trust-breaking:** apparent overclaim stated as fact; internally inconsistent
  number (says 0.88 in §5, 0.78 in abstract); missing/dishonest limitations in a doc that
  makes empirical claims. *Example:* "our tool guarantees GDPR compliance" with no
  evidence → P0. *Counterexample:* a hedge that's merely wordy → P2.
- **P1 — comprehension-breaking:** acronym undefined at first use; buried lede (key
  finding absent from abstract); broken link that supports a claim; missing structural
  block a practitioner needs.
- **P2 — polish:** tone, wordiness, dead footer link, high FK in a non-critical section,
  table formatting.

## Modes

1. **Default (recommend):** lane 1 + lane 2 → merged report (schema above). No edits.
2. **Fix (explicit request):** apply corrections P0-first. Code changes (audited repo's
   scripts or this skill's own) go through superpowers TDD. Re-run full audit after;
   report cleared vs remaining.

## Evals — three suites, explicit pass criteria

1. **Lane-1 evals** = the pytest suite (planted structural defects in fixture docs;
   exact expected findings).
2. **Lane-2 evals:** planted-defect docs (≥1 apparent overclaim, ≥1 internally
   inconsistent number, ≥1 jargon cluster, ≥1 missing-limitations doc) + **1 clean
   control + 1 near-clean control** (minor P2-only flaws).
   Pass criteria: **100% recall of planted P0s at exact severity**, location matched to
   the correct section; thresholded recall ≥80% for planted P1/P2; **false-positive
   budget** on controls: zero P0, ≤1 P1, ≤3 P2 per control doc.
3. **Merged-output eval:** one doc with defects spanning both lanes; verify dedupe and
   schema integrity.

## Out of scope (v1)

- Grammar/spell checking; PDF auditing (markdown source only); auto-publishing/CI.
- **Citation verity** (whether a cited source supports the claim): judge marks "needs
  verification"; a future evidence-verification lane may fetch sources.

## Resolved design questions (per Codex audit)

1. Term detector → **acronyms-only** in v1, allowlist + exact patterns; jargon → judge.
2. Readability → **yes, sentence-level**: section averages for overview, top-5 hardest
   sentences for actionable fixes.
3. Eval threshold → **all planted P0s at exact severity; thresholded P1/P2; FP budget on
   clean + near-clean controls** (no flat 80%).
