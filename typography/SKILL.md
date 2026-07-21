---
name: typography
description: This skill should be used when applying proper typography to prose text or files in Russian, English, German, or French — smart quotes per locale («ёлочки», “curly”, „Gänsefüßchen“, « guillemets »), correct dashes (тире, em/en dash, Gedankenstrich, tiret), non-breaking spaces, ranges, ellipsis, and French espaces insécables before ! ? ; :. Fully deterministic via a pinned typograf-based CLI; never apply these rules by hand. Triggers on "типографика", "typograf", "оттипографь", "smart quotes", "fix typography", "неразрывные пробелы".
---

# Typography (deterministic, multi-locale)

Apply canonical typography via `scripts/typo.js`, a pinned-config wrapper around the `typograf` npm library plus deterministic post-rules for German and French gaps. **Never rewrite quotes/dashes/spaces manually** — always run the script so results are deterministic and idempotent.

## Setup (first run only)

If `scripts/node_modules` is missing: `cd <skill-dir>/scripts && npm install`

## Usage

```bash
# stdin → stdout; default locale chain ru,en-US
echo '"Привет" - мир' | node <skill-dir>/scripts/typo.js
# → «Привет» — мир

# Pick locale (first entry = primary): en-US, en-GB, de, fr, ru, uk, pl, …
node <skill-dir>/scripts/typo.js --locale=de file.md
node <skill-dir>/scripts/typo.js --locale=fr,en-US file.md

# Fix files in place / preview / CI check
node <skill-dir>/scripts/typo.js --in-place --locale=en-US file1.md file2.md
node <skill-dir>/scripts/typo.js --diff file.md
node <skill-dir>/scripts/typo.js --check src/**/*.md   # exit 1 + list if changes needed

# HTML entity output (&laquo; &nbsp; &mdash;) for HTML sources
node <skill-dir>/scripts/typo.js --html-entities file.html

# Conservative mode: quotes/dashes/spaces only (no date/money/number/symbol rewriting)
node <skill-dir>/scripts/typo.js --safe file.md
```

## Per-locale behavior

- **ru** — «ёлочки» (nested „лапки“), ` — ` with nbsp before, `5-6` → `5–6`, nbsp after short prepositions and №, `...` → `…`, `т.е.` → `т. е.`
- **en-US / en-GB** — “curly quotes” with ‘nested’, spaced hyphen → em dash, `…`
- **de** — „Gänsefüßchen“, Gedankenstrich: spaced hyphen → ` – ` (en dash, nbsp before)
- **fr** — « guillemets » with narrow nbsp (U+202F) inside, tiret ` — `, espace fine insécable before `! ? ; :` (URLs like `https://` are left untouched)

## Hanging punctuation (optional, configurable)

Three routes, in order of preference by constraint:

1. **No markup changes allowed** → copy `assets/hang-punctuation.js` into the site and load it. It uses native CSS `hanging-punctuation` where supported (Safari) and falls back to DOM-only span wrapping elsewhere; source files stay untouched. Configure targets via `window.HANG_PUNCT = { selector: '...' }` before the script.
2. **Markup changes acceptable, ru text** → run `typo.js --optalign` (HTML input only); it wraps hanging marks in classed `<span>`s. Include `assets/optalign.css` in the page. Note: `--optalign` output is not idempotent-safe with `--check` on already-spanned files; keep source pristine and treat it as a build step.
3. **Zero effort baseline** → add `hanging-punctuation: first allow-end;` to prose containers (currently Safari-only, harmless elsewhere).

## Workflow notes

- Choose `--locale` from the text's language; for mixed content, process each language's files separately.
- Run only on prose/markdown/HTML text, never on source code. For i18n string files (e.g. `src/i18n/strings/*.ts`), pipe only string contents or verify with a build after `--in-place`.
- For repo-wide fixes: `--check` first, show the user the file list, then `--in-place`.
- The tool is idempotent; if a second pass ever changes output, report it as a bug rather than hand-fixing.
- To adjust rules, edit `makeTypograf()` / `postProcess()` in `scripts/typo.js` so behavior stays pinned across sessions.
