# i18n Studio API reference

The tool lives at `~/ai_projects/i18n-studio` (repo: github.com/glebis/i18n-studio).
`server.mjs` exposes JSON routes on `http://localhost:<PORT>` (default 4331) and
serves the single-page editor at `/`.

## Target model

Edits **Astro-style i18n files**: each `*.ts` file in the target directory is
`export default { <lang>: { ... }, ... }`. Leaves are strings (editable) or
`${...}` template literals / numbers (computed, read-only). Keys are addressed by
**dot-path** with numeric array indices, e.g. `weeks.2.sessions.1.t`.

## Configuration (flags > env > default)

| Flag | Env | Default |
|---|---|---|
| `--dir <path>` | `I18N_STRINGS_DIR` | `<cwd>/src/i18n/strings` |
| `--langs en,ru` | `I18N_LANGS` | `en,ru` |
| `--voice "..."` | `I18N_VOICE` | editorial default |
| `--port 4331` | `PORT` | `4331` |

## Acceptance sidecar

Review state is stored in `<strings-dir>/.i18n-status.json`, keyed
`file::lang::path` → hash of the accepted value. A cell is `accepted` only while
its current value still matches that hash, so any edit auto-invalidates it. The
`.ts` reader ignores this file. Commit it to share review progress, or gitignore
it to keep acceptance local.

## Routes

### `GET /api/strings`
```json
{
  "langs": ["en", "ru"],
  "files": [
    { "file": "Hero.ts",
      "entries": [
        { "path": "h1",
          "en": { "value": "Impact first", "editable": true, "accepted": false },
          "ru": { "value": "Сначала — результат", "editable": true, "accepted": true } }
      ] }
  ]
}
```
- A language cell is `null` when that key is absent in that language.
- `editable: false` ⇒ computed; cannot be written.
- `accepted` is present on editable cells only.

### `POST /api/save`
Body `{ file, lang, path, value }`. AST-safe single-literal write (minimal diff).
Drops acceptance for that cell (an edit ⇒ pending). `{ ok, saved }` / `{ ok:false, error }` (400).

### `POST /api/save-many`
Body `{ edits: [{ file, lang, path, value }, ...] }`. Batch write, used for
duplicate propagation. Returns `{ ok, results: [{ ok, file, lang, path, error? }] }`.

### `POST /api/accept`
Body `{ file, lang, path, value, accepted }`. Toggles review acceptance; `value`
is the current text (the client holds the just-saved on-disk value). `{ ok }`.

### `POST /api/suggest`
Body `{ sourceText, from, to, path }`. Returns `{ ok, suggestions: [...] }` — 3
candidates, most natural first, told to preserve HTML tags/entities, keep length
similar, and not translate identifiers / proper nouns. Proposals only; nothing is
written until a `save`. Shaped by `--voice`. Uses the Claude Agent SDK via the
logged-in Claude Code subscription (no API key); a stale `ANTHROPIC_API_KEY` is
dropped at startup.

## Programmatic library (no server)

For pure read/write without HTTP, import the AST layer directly (set the target
dir first, since `config.mjs` reads it at import time):
```js
process.env.I18N_STRINGS_DIR = '/abs/path/to/src/i18n/strings';
const { readAll, write } = await import('/Users/<you>/ai_projects/i18n-studio/strings.mjs');
readAll();                              // entries[] (without accepted flags)
write('Hero.ts', 'ru', 'h1', 'текст'); // AST-safe write
```
Acceptance helpers live in `status.mjs` (`readStatus`, `setAccepted`); `suggest`
has no library entry point — use the HTTP route.

## Gotchas

- **Computed strings are read-only** (`editable: false`).
- **A missing target key is read-only** until added once in the `.ts` source.
- **Verify HTML/entities** survive a suggestion before saving.
- **Hot reload** needs the target project's dev server running; the write lands on
  disk regardless.
- **One save = one leaf**; use `save-many` for batches.
