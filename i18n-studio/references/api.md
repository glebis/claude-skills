# i18n Studio API reference

The tool lives at `~/ai_projects/i18n-studio` (repo: github.com/glebis/i18n-studio).
`server.mjs` exposes three JSON routes on `http://localhost:<PORT>` (default 4331)
and serves the single-page editor at `/`.

## Target model

The tool edits **Astro-style i18n files**: each `*.ts` file in the target
directory is `export default { <lang>: { ... }, <lang>: { ... } }`. Leaves are
strings (editable) or `${...}` template literals / numbers (computed, read-only).
Keys are addressed by **dot-path** with numeric array indices, e.g.
`weeks.2.sessions.1.t`.

## Configuration (flags > env > default)

| Flag | Env | Default |
|---|---|---|
| `--dir <path>` | `I18N_STRINGS_DIR` | `<cwd>/src/i18n/strings` |
| `--langs en,ru` | `I18N_LANGS` | `en,ru` |
| `--voice "..."` | `I18N_VOICE` | editorial default |
| `--port 4331` | `PORT` | `4331` |

Run from a target repo root with no flags to auto-detect `./src/i18n/strings`,
or pass `--dir` to point anywhere.

## Routes

### `GET /api/strings`
Returns the full corpus.
```json
{
  "langs": ["en", "ru"],
  "files": [
    { "file": "Hero.ts",
      "entries": [
        { "path": "h1",
          "en": { "value": "Impact first", "editable": true },
          "ru": { "value": "Сначала — результат", "editable": true } },
        { "path": "date",
          "en": { "value": "`${d.en.month} ...`", "editable": false },
          "ru": { "value": "`${d.ru.month} ...`", "editable": false } }
      ] }
  ]
}
```
- A language cell is `null` when that key is absent in that language.
- `editable: false` ⇒ computed (`${...}`), number, etc. Cannot be written via the API.

### `POST /api/save`
Body: `{ "file": "Hero.ts", "lang": "ru", "path": "h1", "value": "..." }`
Writes the single string literal via `ts-morph` — a minimal one-line diff, all
surrounding formatting preserved. Returns `{ "ok": true, "saved": {...} }` or
`{ "ok": false, "error": "..." }` (HTTP 400) if the path is not an editable literal.

### `POST /api/suggest`
Body: `{ "sourceText": "...", "from": "en", "to": "ru", "path": "h1" }`
Returns `{ "ok": true, "suggestions": ["...", "...", "..."] }` — 3 candidate
translations, most natural first. The model is told to preserve HTML tags/entities
exactly, keep length similar, and not translate code identifiers / proper nouns.
Suggestions are **proposals only**; nothing is written until a `save`.

Suggestion quality is shaped by `--voice`. Suggestions call the Claude Agent SDK,
which authenticates via the logged-in Claude Code subscription (no API key). A
stale `ANTHROPIC_API_KEY` in the env is dropped at startup so session auth is used.

## Programmatic library (no server)

For pure read/write without HTTP, import the AST layer directly (set the target
dir first, since `config.mjs` reads it at import time):
```js
process.env.I18N_STRINGS_DIR = '/abs/path/to/src/i18n/strings';
const { readAll, write, LANGS } = await import('/Users/<you>/ai_projects/i18n-studio/strings.mjs');
readAll();                              // same shape as GET /api/strings files[]
write('Hero.ts', 'ru', 'h1', 'текст'); // AST-safe write
```
`suggest` has no library entry point; use the HTTP route for translation candidates.

## Gotchas

- **Computed strings are read-only.** `editable: false` cells (dates, interpolated
  copy) must be edited by hand in the `.ts` source.
- **HTML/entities must survive translation.** When applying a suggestion, verify tag
  and entity counts match the source before saving.
- **Hot reload** only happens if the target project's own dev server is running;
  the write itself always lands on disk regardless.
- **One save = one leaf.** Batch by issuing multiple saves; there is no bulk write.
