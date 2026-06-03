---
name: anon
description: De-identify a session transcript (file or folder) by redacting PII LOCALLY before any sharing or cloud use. Produces a redacted GREEN copy with typed placeholders ([PERSON], [EMAIL], [DATE]...) plus a counts-only stats summary. Use when the user says "anonymize this transcript", "redact PII", "de-identify session", "make safe to share", "strip personal data", "anonymize notes before sending to an LLM", or points at a transcript/folder that should be scrubbed. Local-only by default — raw text never leaves the machine; nothing printed is PII; human review is still required before sharing.
---

# confide:anon — local PII redaction

Redact personally identifying information from a transcript (or a whole folder) using the
layered local stack in `shared/confide_core.py`: regex (emails / URLs / phones / IDs / dates)
→ Natasha (RU named entities) → local LLM (quasi-identifiers). Spans are interval-merged and
replaced with typed placeholders. The result is a **GREEN** copy safe to review.

## Privacy invariants (do not violate)
- **Local-only.** No cloud APIs. Raw text never leaves the machine.
- **The original PII is never printed or written.** The only artifact containing transformed
  text is the `*.green.md` copy (placeholders only). The original file is read, never rewritten.
- **Counts only.** stdout and the `*.stats.json` files carry counts (by type, by layer,
  redaction rate) — never PII values or redacted text dumps.
- **Human review still required.** Redaction is a floor, not a guarantee. A human must read the
  GREEN copy before sharing. Pair with **confide:red** to check residual re-identification risk.

## Run it
Run the script on a single file or a directory (processes every `.md`/`.txt`):

```bash
python3 skills/anon/scripts/anon.py PATH
```

For each input it writes, next to the file (or into `--out DIR`):
- `<name>.green.md` — the redacted text (the only thing safe to look at / share after review)
- `<name>.stats.json` — counts only

Options:
- `--layers regex,natasha,llm` — override which detection layers run (default from config).
  Use `--layers regex` for a fully offline, deterministic pass (no models/network).
- `--out DIR` — write outputs to DIR instead of next to each input.
- `--dry-run` — compute and print stats only; write no files.

Already-emitted `*.green.md` / `*.stats.json` are skipped, so a folder can be re-run safely.

## After running
1. Report the counts summary (types, layers, redaction rate) — never paste PII.
2. Tell the user the GREEN copy still needs human review before sharing.
3. Offer **confide:red** to probe what an attacker could still infer/link.

## Setup
Layer availability (Natasha, local LLM via Ollama) and defaults come from config — run
**confide:setup** first if Natasha/Ollama aren't installed. `--layers regex` always works offline.
