---
name: audit
description: Run a corpus-scale, STATS-ONLY PII audit over a folder of session transcripts LOCALLY and produce an aggregate report — counts by type and by layer, the per-session redaction-rate distribution, document lengths, and a coarse residual proxy. Use when the user says "audit my sessions", "scan folder for PII", "how much PII across these transcripts", "PII stats for my corpus", "is my redaction holding at scale", or points at a directory of transcripts and asks how much personal data it contains. Fully local — raw text never leaves the machine; the report carries ZERO PII values, transcript substrings, or filenames (only anonymized own-NN ids and counts), so the aggregates are safe to surface. Run it on a RED (raw) corpus to size the PII, or on a GREEN (already-redacted) corpus to check residual leakage.
---

# confide:audit — corpus-scale, stats-only PII audit

Measure how much PII lives across a whole folder of sessions, without ever exposing any
of it. The audit runs the layered LOCAL detector stack from `shared/confide_core.py`
(regex → Natasha → local LLM) over each file and emits **only aggregates**. This mirrors
the `real_session_eval` privacy contract: read text only in-process, emit counts.

## Privacy invariants (do not violate)
- **Local-only.** No cloud APIs. Raw transcript text never leaves the machine.
- **Stats-only output.** The report (markdown + json + optional HTML) contains ONLY
  counts and rates — never a transcript substring, never a detected PII value.
- **No filenames.** Per-file rows are keyed by anonymized ids `own-00`, `own-01`, …
  The original path/name is never written or printed. On an unreadable file, only the
  index + exception class name is recorded.
- **Safe to surface.** Because it is counts-only, the aggregate report can be shared
  with a cloud agent or pasted into a chat. The PII stays on the machine.

## What it reports
- `n_files`, total / mean / min / max document chars
- `spans_by_type` (PERSON, EMAIL, PHONE, DATE, …) and `spans_by_layer` (regex / natasha / llm)
- `overall_redaction_rate` plus the **per-session** redaction-rate distribution
  (min / median / mean / max)
- a **coarse residual proxy**: spans still detectable after redaction — ~0 on a clean RED
  corpus, a leakage signal on a GREEN corpus.

## Run it
Point it at a folder (recurses, processes every `.md`/`.txt`; skips confide's own
`*.green.md` / `*.stats.json` outputs):

```bash
python3 skills/audit/scripts/audit.py FOLDER
```

Options:
- `--list paths.txt` — also/instead audit absolute paths listed one per line.
- `--layers regex,natasha,llm` — choose detection layers (default from config).
  Use `--layers regex` for a fully offline, deterministic pass (no models/network).
- `--out report.md` — report path; a `report.json` sibling is written alongside.
- `--html` — also write a Tufte-ish dashboard (`report.html`, counts only).

Writes the markdown + json report (and optional HTML) and prints the aggregate summary —
all counts only.

## RED vs GREEN
- **RED (raw) corpus:** sizes the PII problem before any redaction.
- **GREEN (redacted) corpus:** the residual proxy and remaining `spans_by_type` tell you
  whether redaction is holding at scale.

## After running
1. Report the aggregate summary (file count, span totals by type/layer, redaction-rate
   distribution, residual proxy) — never paste PII.
2. If residual is non-trivial on a GREEN corpus, point the user at **confide:anon** to
   re-redact and **confide:red** to probe re-identification risk.

## Setup
Layer availability (Natasha, local LLM via Ollama) comes from config — run
**confide:setup** if they aren't installed. `--layers regex` always works offline.
