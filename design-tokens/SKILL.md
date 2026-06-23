---
name: design-tokens
description: This skill should be used to set up, validate, resolve, and export design tokens following the DTCG (Design Tokens Community Group) Format Module 2025.10 standard. Use when the user wants to define a design token set globally or per project, compile tokens to CSS variables, layer a project's tokens over a global brand base, or produce an on-brand context file for other generation skills. Triggers on "set up design tokens", "create a token set", "compile tokens to CSS", "design system variables", "brand tokens".
---

# Design Tokens

Manage [DTCG 2025.10](https://www.designtokens.org/tr/drafts/format/) design tokens
with a dependency-free Python core. v1 covers the deterministic spine: scaffold,
validate, merge (global base + project override), resolve aliases, and export CSS.

## Standard vs convention

- **Standard (DTCG):** `*.tokens.json`, `$value`/`$type`, whole-value `{alias}` references.
- **Skill convention (NOT DTCG):** global-base / project-override layering via `merge`,
  and theme-as-override-file. These are labelled in code; do not present them as standard.

## v1 scope

Supported `$type`: `color` (string values), `dimension`, `duration`, `fontFamily`,
`fontWeight`, `number`, `typography`, `shadow`. Outputs: CSS custom properties, a
Google-Labs **DESIGN.md** (alpha), a standalone HTML preview, and **generation
prompts** (gpt-image-2 / nano-banana CLI lines + a `/tufte-report` theme) via the
prompt door. CSS **import**
covers color/dimension/duration/fontFamily/number; composite values (box-shadow,
gradients, multi-part typography) are skipped and reported. Not in v1: JSON Pointer
`$ref`, `$root`, structured color objects, name-restriction enforcement, Style
Dictionary, Figma/Pencil importers, share bundles, `skillify` (see the phased spec).

## Commands

Run via `scripts/tokens <command>` (or `PYTHONPATH=scripts python3 -m dtokens.cli`):

| Command | What it does |
| --- | --- |
| `setup-edit <dest> [--from SRC]` | Scaffold a token file at `<dest>` and validate it (refuses to overwrite). With `--from`, deterministically clone an existing set's structure + content to edit (byte-stable for a given source) instead of the blank template. Ships `templates/base.tokens.json` (minimal) and `templates/monaspace.tokens.json` (a real set extracted from a live site — see *Extracting from a site*). |
| `import <css> [-o OUT]` | Import a CSS file's `:root` custom properties into DTCG, preserving variable names. Skips composites (shadow/gradient) and reports them on stderr. |
| `validate <file>` | Print `OK` or a list of errors; exit 1 if invalid. |
| `merge <base> <override> [-o OUT]` | Layer project override on global base. |
| `resolve <file> [-o OUT]` | Flatten aliases to concrete values (JSON map). |
| `export-css <file> [--selector SEL] [-o OUT]` | Emit CSS custom properties. |
| `design-md <file> [--name N] [--description D] [-o OUT]` | Emit a Google-Labs [DESIGN.md](https://github.com/google-labs-code/design.md) (alpha) — YAML token frontmatter + prose body. |
| `preview <file> [--name N] [--full] [--description D] [-o OUT]` | Emit a standalone HTML swatch page (colors, type specimens, spacing, rounded, shadow). With `--full`, emit a **landing-page mockup** instead — the brand applied in situ (hero, prose, accent band, footer), driven entirely by the role/type/space tokens via `:root` vars. Type specimens load their families via a deterministic Google Fonts `@import` so brand faces render (degrades to a generic fallback offline / for non-Google fonts). |
| `prompt <file> [--target gpt-image-2\|nano-banana\|tufte\|all] [--preset P ...] [--platform P] [--subject S] [--name N] [-o OUT]` | The **prompt door**: turn resolved tokens into ready-to-paste generation prompts. Image targets emit per-preset CLI invocations with the brand's hex/fonts/shape baked into the subject; `tufte` emits a CSS `:root` theme mapping brand roles onto `/tufte-report`'s variables. |
| `use <file> [--name N] [--description D] [--out-dir DIR] [--serve/--no-serve] [--port N] [--no-open]` | Validate + resolve, then write `tokens.css`, `DESIGN.md`, `preview.html`, `preview-full.html` (landing-page mockup), `image-prompts.md`, and `tufte-theme.css`. **Serves the output over HTTP and opens it by default when interactive** (see below). |
| `serve <path> [--port N] [--no-open]` | Serve a generated `.html` (or an output dir) over `http://127.0.0.1` and open it. Use this to view previews — `file://` URLs are unique origins and break web-font loads, `fetch`, and extensions. |

## Serving previews (default)

Generated HTML is meant to be **served, not opened from disk**. Browsers treat
`file://` URLs as unique security origins, which breaks cross-origin web-font
loads, `fetch`, and many extensions (`Unsafe attempt to load URL … 'file:' URLs
are treated as unique security origins`). So `use` (and `preview` when it writes a
file) start a tiny stdlib HTTP server on `http://127.0.0.1` and open the result —
**by default when run interactively** (a TTY). In scripts / CI (non-TTY) serving
is skipped so nothing blocks; force it either way with `--serve` / `--no-serve`.
`serve <path>` does the same for any existing file or directory. Dependency-free
(`http.server`).

## Extracting tokens from a live site

Tokens can be reverse-engineered from any shipping site, then saved as a template.
The method doesn't matter — pick what the site allows:

1. **Fetch the CSS** (static sites): grab the linked stylesheet(s), then resolve
   the variable indirection to ground values. Modern design systems alias twice —
   e.g. Monaspace's `--color-neon-primary: rgb(var(--color-neon-primary-rgb))` and
   `--color-neon-primary-rgb: 245 184 165` → `#F5B8A5`. Base scales
   (`--base-size-16: 1rem`) give the spacing/radius steps.
2. **Computed styles** (JS-rendered sites): drive a real browser (`/browser-mate`)
   and read `getComputedStyle(:root)` plus key elements — yields ground-truth values
   no matter how they're authored.
3. **`import <css>`**: if the site exposes a flat `:root` block, pipe it straight
   through the importer (names preserved).
4. Hand-curate the extracted values into `<name>.tokens.json` with explicit role
   aliases (`primary`, `text`, `background`, …) so the prompt door and tufte map
   light up, and `validate`.

`templates/monaspace.tokens.json` is the worked result for
[monaspace.githubnext.com](https://monaspace.githubnext.com/) — its five-font
superfamily (Neon/Argon/Xenon/Radon/Krypton) as accent colours over the GitHub
dark canvas (`#0D1117`), on the 4/8/16/24 base scale. Scaffold from it with
`setup-edit my.tokens.json --from templates/monaspace.tokens.json`.

## Prompt door (tokens → generation)

The spine ends at CSS/DESIGN.md; the **prompt door** carries the brand onward
into image and report generation so it never needs hand-translating. All of this
is **skill convention**, not DTCG — colour *roles*, the curated preset picks, and
the tufte variable map are generation aids layered on the standard.

- **Brand summary** (`brand_summary.py`): distils resolved tokens into palette
  (with roles inferred from token names: `primary`, `text`, `background`,
  `accent`, `success`, `warning`, `danger`, `muted`), fonts, type specimens, and
  a shape word from the largest corner radius (`sharp`/`soft`/`rounded`/`pill`).
- **`gpt-image-2`**: emits CLI lines across that tool's **unique** presets
  (`editorial`, `bauhaus`, `isometric`, `poster`) so one brand yields distinct
  moods; the brand's exact hex/fonts/shape are baked into each subject.
- **`nano-banana`**: steers to *its* edge — accurate in-image text (`--model
  pro`) and reference-image anchoring — over the shared presets. (It has no
  presets unique to itself; its set is a subset of gpt-image-2's shared eight.)
- **`tufte`**: emits a `:root` block mapping brand roles onto `/tufte-report`'s
  own variables (`--ink`, `--bg`, `--spark-primary/secondary/tertiary`,
  `--status-red/amber/green`, `--accent`). Roles with no matching token fall back
  to tufte-report's defaults, labelled inline. (`/tufte-report` consumes a theme,
  not a DESIGN.md.)

## DESIGN.md output

`use` and `design-md` emit a **DESIGN.md** — the agent-facing format read by Claude
Code, Cursor, v0, Lovable, Stitch. It is complementary to DTCG: DTCG `.tokens.json`
is the rigorous source of truth; DESIGN.md is the prose+tokens artifact agents apply.
Our resolved tokens map to its frontmatter as: `color` → `colors`, `typography` →
`typography`, `dimension` under `space*` → `spacing`, `dimension` under
`radius/rounded*` → `rounded`. Names are flattened (drop the top group, dots → `-`).
Types without a DESIGN.md home (`duration`, `shadow`, `number`, `fontFamily`,
`fontWeight` standalone) are noted in the Overview, not the frontmatter. This
name/bucket mapping is a skill convention over the DESIGN.md alpha schema.

## Storage convention

Token files are **canonical source — keep them visible and committed, never in a
hidden dotdir** (a leading dot reads as ignorable tool state; Style Dictionary uses
`tokens/`, DESIGN.md lives at repo root, DTCG mandates the extension but no path).

- Global sets: `~/.claude/design-tokens/<set>/base.tokens.json`
- Project, single set: `<project>/design.tokens.json` + `<project>/DESIGN.md` at root
- Project, multi-scope: `<project>/tokens/base.tokens.json` + `<project>/tokens/<name>.tokens.json`
- Multiple themes (light/dark): keep one override file per theme and merge it before `use`.
- Reserve a dotdir, if any, only for *generated* output (`tokens.css`, `preview.html`).

## Tests

`cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/ -v`
