---
name: anon
description: De-identify a session transcript (file or folder) by redacting PII LOCALLY before any sharing or cloud use. Produces a redacted GREEN copy with unique reserved-sentinel placeholders ([CONFIDE_PERSON_0001], [CONFIDE_EMAIL_0001], [CONFIDE_DATE_0002]...) plus a counts-only stats summary, and a local secret <name>.map.json (0600, gitignored) that enables confide:rehydrate to restore real values after a cloud analysis. Use when the user says "anonymize this transcript", "redact PII", "de-identify session", "make safe to share", "strip personal data", "anonymize notes before sending to an LLM", or points at a transcript/folder that should be scrubbed. Local-only by default — raw text never leaves the machine; the map is the only artifact with originals and stays local; nothing printed is PII; human review is still required before sharing.
---

# confide:anon — local PII redaction

Redact personally identifying information from a transcript (or a whole folder) using the
layered local stack in `shared/confide_core.py`: regex (emails / URLs / phones / IDs / dates)
→ Natasha (RU named entities) → local LLM (quasi-identifiers). Spans are interval-merged and
replaced with placeholders. The result is a **GREEN** copy safe to review.

By default anon emits a **reversible map**: unique reserved-sentinel placeholders (the *same
EXACT* value always becomes the *same* `[CONFIDE_<TYPE>_<NNNN>]`, e.g. `[CONFIDE_PERSON_0001]`,
`[CONFIDE_EMAIL_0001]`, `[CONFIDE_DATE_0002]`) plus a sibling `<name>.map.json` (structured:
`schema_version`, `doc_id`, `green_sha256`, `created`, `entries[]`) mapping each placeholder to
its original. The `CONFIDE_` sentinel is reserved — a real transcript essentially never
contains it, so there is no collision risk and rehydrate never touches ordinary prose like
"Person 1". This is **exact-value** matching, not entity coreference: inflected forms (e.g. RU
"Марина" vs "Марины") are SEPARATE placeholders (no lemmatized merge). That map is the
**secret** — the ONLY artifact with originals; it stays **local** and enables
**confide:rehydrate** to put real values back into a cloud analysis of the GREEN text
(round-trip: redact → analyze the green → rehydrate locally). Use `--no-map` for the legacy
non-reversible `[TYPE]` style (no map written).

## Privacy invariants (do not violate)
- **Local-only.** No cloud APIs. Raw text never leaves the machine.
- **By design, original PII is written ONLY to the local, 0600, gitignored `<name>.map.json`,
  which never leaves the machine.** It is never printed, and never written to the GREEN copy
  (the GREEN holds placeholders only; the original file is read, never rewritten). The map is
  the SECRET — the one artifact with originals. A `.gitignore` covering `*.map.json`,
  `*.view.html`, and `*.restored.md` is written/updated in the output dir so these local-only
  artifacts can never be committed. If the output dir looks cloud-synced (iCloud / Dropbox /
  OneDrive / Google Drive), anon prints a WARNING that the secret map would be uploaded.
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
- `<name>.map.json` — the reversible map (secret; 0600; gitignored; local only). Skipped with
  `--no-map`. A `.gitignore` with `*.map.json` is also written/updated in the output dir.

Options:
- `--layers regex,natasha,llm` — override which detection layers run (default from config).
  Use `--layers regex` for a fully offline, deterministic pass (no models/network).
- `--out DIR` — write outputs to DIR instead of next to each input.
- `--dry-run` — compute and print stats only; write no files.
- `--no-map` — disable the reversible map; emit non-unique `[TYPE]` placeholders, no map.json.

Already-emitted `*.green.md` / `*.stats.json` / `*.map.json` are skipped, so a folder can be
re-run safely.

## After running
1. Report the counts summary (types, layers, redaction rate) — never paste PII.
2. Tell the user the GREEN copy still needs human review before sharing.
3. Remind them the `<name>.map.json` is the secret (originals) — it stays local, never
   committed/shipped — and that **confide:rehydrate** uses it to restore real values into a
   cloud analysis of the GREEN text.
4. Offer **confide:red** to probe what an attacker could still infer/link.

## Setup
Layer availability (Natasha, local LLM via Ollama) and defaults come from config — run
**confide:setup** first if Natasha/Ollama aren't installed. `--layers regex` always works offline.
