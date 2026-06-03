---
name: view
description: Build a self-contained interactive HTML that lets you SEE de-identification and restoration — original ↔ redacted ↔ rehydrated, with color-coded PII spans and All/None/Selected toggles. Use when the user says "show me what was redacted", "visualize the de-id", "compare original and redacted", "highlight the PII", "view redaction diff", "see what rehydrate restored", or wants to inspect exactly which spans each type/layer removes. LOCAL only — the HTML embeds REAL values (like a vault artifact): written locally, gitignored, banner-marked private, never shipped or committed.
---

# confide:view — visual de-id diff (what redaction & rehydrate do)

Produce ONE standalone `.html` that renders a transcript with every PII span
highlighted and color-coded by type, and lets you toggle between the original and
the redacted views interactively. It reuses the span data from the shared core
(`shared/confide_core.py`) — a thin renderer, no new detection logic.

## Privacy invariants (do not violate)
- **The HTML embeds REAL values** (originals + placeholders) so you can compare them.
  It is therefore a **vault artifact**: same posture as the relationship-graph HTML.
- **Local only.** Written next to the input, a sibling `.gitignore` excludes
  `*.view.html` (and `*.map.json`), and a red **PRIVATE** banner sits at the top.
  Never share it, never commit it, never ship it.
- **Counts only to stdout.** The terminal output carries span counts by type — never
  PII values or redacted-text dumps.
- **Self-contained & offline.** Inline CSS + JS, no CDN / external resources, so it
  renders offline and can never 404. Default detection layer is `regex` (no network,
  no models).

## Run it
```bash
python3 skills/view/scripts/view.py ORIGINAL.txt
```
If a `<name>.map.json` sits next to the input (from **confide:anon**), it is picked up
automatically so the view shows exactly that known PII; otherwise PII is detected with
the local layers and a fresh reversible map is built in memory.

Options:
- `--map MAP.json` — supply the reversible map explicitly.
- `--layers regex,natasha,llm` — choose detection layers (default `regex`, offline-safe).
- `--out DIR` — write the `.view.html` into DIR instead of next to the input.

It writes `<name>.view.html` and ensures a sibling `.gitignore`.

## What the HTML shows
- The transcript with each PII span wrapped in
  `<mark class="pii TYPE" data-orig=… data-ph=…>`, **colored by type** (PERSON, DATE,
  EMAIL, …). Hover a span to see `original ↔ placeholder`.
- An interactive **state toggle**:
  - **All** — fully redacted: every span shows its placeholder.
  - **None** — original: nothing masked.
  - **Selected** — mask only the PII types you check (per-type checkboxes in the legend).
- A **legend + counts by type**.

## After running
1. Open the `<name>.view.html` locally in a browser to inspect the de-id.
2. Report the counts summary (types) — never paste PII.
3. Remind the user the file is **private/local** and must not be shared or committed.

## Setup
The default `regex` layer always works offline. For Natasha (RU NER) or the local LLM
layer, run **confide:setup** first; otherwise pass `--layers regex`.
