---
name: rehydrate
description: Put the real values back into an analysis that was produced from GREEN (placeholder) text — LOCALLY, using the user's own reversible map. Completes the confide round-trip (redact -> cloud-analyze the green -> rehydrate locally). Use when the user says "rehydrate", "restore real names", "unmask the analysis", "put the names back", "de-redact this output", "reverse the placeholders", or hands you an analysis full of [CONFIDE_PERSON_0001]/[CONFIDE_DATE_0002] plus a *.map.json. Runs only on the user's own map; the map never leaves the machine; nothing fetched or transmitted. Prints counts only — never echoes restored PII. Warns on placeholders not in the map (possible LLM hallucination).
---

# confide:rehydrate — restore real values into a placeholder analysis

This is the last step of the CONFIDE round-trip:

1. **Redact** locally with `confide:anon` (default reversible mode) → a GREEN copy
   with unique reserved-sentinel placeholders (`[CONFIDE_PERSON_0001]`,
   `[CONFIDE_EMAIL_0001]`, `[CONFIDE_DATE_0002]`…) plus a secret `<name>.map.json`
   (structured: `green_sha256`, `entries[]`…) that stays on the machine.
2. **Analyze the GREEN text** anywhere — including a cloud LLM. The analysis comes
   back full of those same placeholders (sometimes mangled to `CONFIDE_PERSON_0001`,
   `[CONFIDE PERSON 0001]`… — but always keeping the full `CONFIDE_TYPE_NNNN` core).
3. **Rehydrate** here: replace every placeholder with its original value from your
   own map, producing the real analysis — without the cloud ever seeing the originals.

## Privacy invariants (do not violate)
- **Local-only, on the user's OWN map.** The map never leaves the machine. This skill
  never fetches or transmits anything.
- **Counts only on stdout.** The summary reports `restored N, unmatched M`. The
  restored text (which contains originals) is written to a local file; it is NEVER
  echoed to stdout beyond the counts.
- **Unmatched = possible hallucination.** A placeholder that is not in the map is
  reported as `unmatched` and **left in place** — we never invent a value for it.
  Warn the user that these may be LLM hallucinations.
- The `<name>.restored.md` output contains originals: it is local-only, do not share
  or commit it.

## Run it
```bash
python3 skills/rehydrate/scripts/rehydrate.py ANALYSIS_FILE [--map <name>.map.json]
```
- `ANALYSIS_FILE` — the text/analysis containing placeholders.
- `--map <name>.map.json` — the secret map from `confide:anon`. If omitted, the
  sibling `*.map.json` is auto-found (e.g. an analysis next to `session.map.json`,
  or one derived from `session.green.md`).
- `--out PATH` — output path (default: `<name>.restored.md` next to the input).
- `--verify-green <green_file>` — check the map's `green_sha256` against that GREEN
  file; warns loudly if they don't match (wrong map for this document).

Robust to LLM mangling that still keeps the full `CONFIDE_TYPE_NNNN` core:
`[CONFIDE_PERSON_0001]`, `[CONFIDE PERSON 0001]`, `CONFIDE_PERSON_0001`, and
`confide_person_0001` all restore to the same map entry. Ordinary prose lacking the
`CONFIDE` prefix (e.g. "Person 1", "patient 1", "section 2") is **never** touched, and
`0001` never eats `0010`. Rehydration is idempotent (re-running on restored text is a
no-op). Accepts both the structured map schema and a legacy flat map.

## After running
1. Report the restore summary (`restored N, unmatched M`) — never paste PII.
2. If `unmatched > 0`, flag the placeholders as possible hallucinations not in the map.
3. Remind the user the `*.restored.md` is local-only (it now contains originals).
