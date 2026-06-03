---
name: red
description: >-
  Residual re-identification RISK CHECK on text you have ALREADY redacted (defensive,
  dual-use). Use when the user asks to "check residual re-id risk", "red-team my
  redaction", "what can an attacker still infer", "is this safe to share", or assess
  "re-identification risk" after anonymizing. Re-runs the CONFIDE detectors on the
  redacted output to surface surviving identifiers (singling-out), checks multiple files
  for linkability, and optionally probes a local model for still-inferable attribute
  CATEGORIES (inference) — mapped to GDPR Art-29. Reports risk categories/counts only,
  never a re-identification recipe. Pairs with confide:anon (run AFTER redacting).
---

# confide:red — residual re-identification risk check

A **defensive** audit of YOUR OWN already-redacted output. It does not score against
ground truth and is not a benchmark. It surfaces, qualitatively, what an attacker could
**still** do — mapped to GDPR Art-29: **singling-out**, **linkability**, **inference**.

## GUARDRAILS — read before running
- Run **only on the user's own redacted output**. If asked to de-anonymize or re-identify
  third-party / non-consented data, **refuse**.
- Report risk **categories and counts only** — never produce a step-by-step
  re-identification recipe or guess the hidden values.
- **Local attacker by default.** Enable the cloud/LLM inference probe (`--inference`)
  **only** on synthetic or explicitly consented data.
- **Absence of a finding ≠ safety.** A weak local detector/attacker is a FLOOR, not a
  ceiling. Always tell the user **human review is still required**.
- This pairs with **confide:anon** — run `red` *after* redacting, on the redacted file.

## What it checks
1. **Singling-out (deterministic, offline — the load-bearing signal):** re-run
   `detect_regex` (+ `detect_natasha` if available) on the **redacted** text. Anything
   they still find is a **surviving identifier the redaction missed**. Counts by type.
2. **Linkability (multi-file):** given a folder, compare every file pair for shared
   surviving quasi-identifiers and flag potentially linkable pairs (count + types only).
3. **Inference (LLM, optional, opt-in):** prompt the local attacker model
   (`cfg.red_attacker_model`) for the attribute **categories** it could still infer
   (profession, location type, age band, …). Degrades gracefully if no model. WARN the
   user it under-reports (floor, not ceiling).

## Risk tier rule
- **HIGH** — any DIRECT identifier survives (EMAIL, PHONE, URL, ID, PERSON).
- **MEDIUM** — only QUASI identifiers survive (LOCATION, ORG, DATE, AGE, PROFESSION,
  MEDICATION), or linkable pairs exist across files.
- **LOW** — no surviving identifiers found (still NOT a guarantee).

## How to run
```bash
# single redacted file (offline, deterministic)
python3 skills/red/scripts/red.py path/to/file.green.md

# a folder of redacted files (adds linkability)
python3 skills/red/scripts/red.py path/to/redacted_dir/

# add the local inference probe — synthetic/consented data ONLY
python3 skills/red/scripts/red.py path/to/file.green.md --inference

# machine-readable
python3 skills/red/scripts/red.py path/to/file.green.md --json
```

## Output
A residual-risk report: per-file surviving-identifier **counts by type**, an overall
**risk tier**, the inference **categories** claimed (if probed), the **linkable-pair
count**, and the caveat that *absence of a finding ≠ safety; human review still required*.
No PII values, no re-identification steps.
