# Evals for whitepaper-audit (lane 2 — the LLM judge)

Lane 1 (deterministic) is validated by the pytest suite in `scripts/tests/`.
Lane 2 validates the **judge** (audit-prompt.md) against planted defects, mirroring the
planted-signal gold-standard approach: you only trust a reviewer you've tested against
known answers.

## Cases

| File | Planted defects (documented as HTML comments in-file) |
|---|---|
| `cases/planted-defects.md` | `inconsistent-number` (P0) · `unsupported-claim` overclaim (P0) · `jargon-undefined` cluster (P1) |
| `cases/missing-limitations.md` | `limitations-present` (P0) — empirical claims, no limitations section |
| `cases/clean-control.md` | none — well-hedged, defined terms, CIs, limitations, glossary |

## Procedure

1. For each case, give the judge the audit prompt (`references/audit-prompt.md`) with the
   case file as {PATH} and audience "general technical practitioners". **Strip the HTML
   comments first** (`sed '/<!--/,/-->/d'`) so the judge cannot read the answer key.
2. Compare the judge's JSON findings to the planted defects.

## Pass criteria (from DESIGN.md v0.2; per Codex audit)

- **100% recall of planted P0s at exact severity**, location matched to the correct
  section. (`unsupported-claim` vs `marketing-tone` is an accepted check_id alias for the
  overclaim plant; `jargon-undefined` vs `acronym-undefined` likewise.)
- Planted P1/P2: recall ≥ 80%.
- **False-positive budget on the clean control:** zero P0, ≤1 P1, ≤3 P2.
- Judge output must validate against the finding schema (all required keys, verbatim
  evidence quotes that actually appear in the document).

Record results per run in `evals/RESULTS.md` (date, model, pass/fail per criterion).
Re-run after any change to `audit-prompt.md` or the checklist.
