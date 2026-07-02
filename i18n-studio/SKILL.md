---
name: i18n-studio
description: This skill should be used when editing, translating, or reviewing an Astro-style i18n string corpus (files of the form export default { en: {...}, ru: {...} } under src/i18n/strings), or when the user wants to fill in missing translations, audit coverage, accept/review translations, propagate an edit across duplicate strings, get translation candidates, bulk-edit UI microcopy, or open a visual/keyboard translation editor. Drives the standalone i18n Studio tool at ~/ai_projects/i18n-studio (AST-safe minimal-diff saves via ts-morph, acceptance review state, duplicate propagation, hot-reload, and Claude translation suggestions).
---

# i18n Studio

## Purpose

i18n Studio edits **Astro-style i18n string files** safely: files shaped like
`export default { en: {...}, ru: {...} }` where leaves are UI strings. It writes
one string literal at a time through a `ts-morph` AST, so every save is a minimal
one-line diff with all surrounding formatting preserved, and a running dev server
hot-reloads. It also produces Claude translation candidates that preserve HTML
tags and tone.

Use it instead of hand-editing `.ts` string files with Edit/sed: manual edits
risk formatting churn, broken quoting/escaping, and desynced languages. The AST
layer avoids all three.

## When to use

- Filling in missing translations for a language (e.g. "translate the new hero copy to Russian", "fill the German gaps").
- Auditing coverage ("which strings are untranslated?").
- Editing UI microcopy in one or more languages.
- Getting translation candidates for a specific string.
- Opening a visual editor for a human to translate interactively ("open the translation editor").

Applies to any repo whose translations follow the `export default { <lang>: {...} }`
convention, not one specific project.

## Locate the strings directory first

The tool defaults to `<cwd>/src/i18n/strings`. Confirm the real location before
starting (it may differ):

```bash
ls src/i18n/strings 2>/dev/null || find . -path '*/i18n/strings' -type d -not -path '*/node_modules/*' | head
```

Use that path as `--dir` below. Ensure the tool is installed once:
`cd ~/ai_projects/i18n-studio && npm install`.

## Start the server (required for the API and the UI)

Start it in the background, pointed at the target strings dir, and wait until it
is reachable:

```bash
node ~/ai_projects/i18n-studio/server.mjs --dir "$PWD/src/i18n/strings" --port 4331 &
until curl -sf http://localhost:4331/api/strings >/dev/null; do sleep 0.5; done
```

Pass `--langs en,ru,de` if the corpus has languages beyond the `en,ru` default,
and `--voice "<one-line tone brief>"` to steer suggestion style. Stop it with
`kill %1` (or the printed PID) when finished.

For a human to edit visually, start the server the same way and share the URL
(`http://localhost:4331`); do not try to click the web UI programmatically.

## Drive it with the helper CLI

`scripts/i18n.mjs` (dependency-free, Node 18+) wraps the API. Point it at the
server with `I18N_URL` if the port is not 4331.

```bash
S=~/ai_projects/claude-skills/i18n-studio/scripts/i18n.mjs

node "$S" audit --to ru                          # status breakdown + untranslated/missing
node "$S" audit --to ru --pending                # also list translated-but-unaccepted
node "$S" get     Hero.ts en h1                   # read a value
node "$S" suggest Hero.ts h1 --from en --to ru    # 3 candidates (proposals only)
node "$S" set     Hero.ts ru h1 "Сначала — результат"  # AST-safe write (→ pending)
node "$S" accept  Hero.ts ru h1                   # mark reviewed/accepted
node "$S" unaccept Hero.ts ru h1                  # back to pending
```

Typical translation-fill loop: `audit --to <lang>` to see the breakdown and gaps →
for each gap, `suggest` from the source language → review the candidate (see rules
below) → `set` the chosen value → `accept` once it is right.

Acceptance is a durable review state (sidecar `.i18n-status.json`); editing a
value automatically drops it back to pending. For a human reviewer, the fullscreen
review mode (below) is faster than the CLI.

The raw routes (`GET /api/strings`, `POST /api/save`, `POST /api/suggest`), data
shapes, dot-path rules, config flags, and a no-server library path are documented
in `references/api.md`. Read it before doing anything beyond the CLI above.

## Visual editor: review mode, filters, duplicates

For a human, the browser UI is the fast path. Start the server, share the URL, and
point out:

- **Source → target switch** in the header (work any language against any reference).
- **Filters:** show all / untranslated / pending / accepted / duplicates / code-like,
  by file, with sort (file / path / status / duplicates-first) and live counts.
- **Hide code-like:** asset paths, CSS vars/colors, class names and identifiers are
  detected and hidden from the queue by default (they rarely need translation).
- **Accept** button per row (and a duplicates badge `×N`).
- **Duplicate propagation:** after editing a string that others shared, a banner
  offers *apply to all* — one click updates every entry that held the old value.
- **Fullscreen review** (`review ▸`): steps through the filtered set one at a time,
  fully keyboard driven with a visible legend — `←/→` or `j/k` move, `a` accept &
  next, `p` pending, `e` edit, `s` suggest, `1/2/3` apply a suggestion, `u` undo,
  `Esc` close, `>` focus. Tab lands on the edit field; clicking the file name
  filters the list to that file. This is the tool for grinding through thousands.
- **Focus mode** (`Shift + .`): hides all chrome, leaving only the strings.

## Rules that matter

- **Never blindly apply a suggestion.** Before `set`, verify the candidate keeps the
  same HTML tags and entities as the source (`<b>`, `<span ...>`, `&nbsp;`, `&#39;`,
  `&mdash;`) in the same positions, and does not translate code identifiers or
  proper nouns. Suggestions are proposals, not decisions.
- **Computed strings are read-only.** Entries with `editable: false` (dates,
  `${...}` interpolated copy) cannot be saved via the tool; edit them by hand in
  the `.ts` source.
- **Dot-paths use numeric indices for arrays**, e.g. `weeks.2.sessions.1.t`.
- **One save writes one leaf.** Loop for bulk work; there is no batch write.
- **Hot reload** needs the target project's own dev server running; the write lands
  on disk either way.
- **Confirm before mass edits.** Auto-translating a whole language is a large,
  outward-facing change to the product copy; surface the gap list and confirm scope
  with the user before writing many strings.
