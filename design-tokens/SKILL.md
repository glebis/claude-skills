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
`fontWeight`, `number`, `typography`, `shadow`. Outputs: CSS custom properties and a
Google-Labs **DESIGN.md** (alpha). Not in v1: JSON Pointer `$ref`, `$root`,
structured color objects, name-restriction enforcement, Style Dictionary, importers,
share bundles, `skillify` (see the phased spec).

## Commands

Run via `scripts/tokens <command>` (or `PYTHONPATH=scripts python3 -m dtokens.cli`):

| Command | What it does |
| --- | --- |
| `setup-edit <dest>` | Scaffold a template token file at `<dest>` and validate it (refuses to overwrite). |
| `validate <file>` | Print `OK` or a list of errors; exit 1 if invalid. |
| `merge <base> <override> [-o OUT]` | Layer project override on global base. |
| `resolve <file> [-o OUT]` | Flatten aliases to concrete values (JSON map). |
| `export-css <file> [--selector SEL] [-o OUT]` | Emit CSS custom properties. |
| `design-md <file> [--name N] [--description D] [-o OUT]` | Emit a Google-Labs [DESIGN.md](https://github.com/google-labs-code/design.md) (alpha) — YAML token frontmatter + prose body. |
| `preview <file> [--name N] [-o OUT]` | Emit a standalone HTML swatch page (colors, type specimens, spacing, rounded, shadow). |
| `use <file> [--name N] [--description D] [--out-dir DIR]` | Validate + resolve, then write `tokens.css`, `DESIGN.md`, and `preview.html`. |

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

- Global sets: `~/.claude/design-tokens/<set>/base.tokens.json`
- Project deltas: `<project>/.design-tokens/project.tokens.json` (override of a global set)
- Multiple themes (light/dark): keep one override file per theme and merge it before `use`.

## Tests

`cd design-tokens && PYTHONPATH=scripts python3 -m pytest tests/ -v`
