# Design: `design-tokens` skill

**Date:** 2026-06-22
**Status:** Approved design, pending spec review

## Problem

There is no single source of truth for design decisions (color, spacing, type,
shadow, motion) across Gleb's work. Brand values get hardcoded and copy-pasted
between code, Pencil mockups, Claude generation skills, and collaborators, causing
drift. We want a skill that lets a person **set up** a design-token set (globally or
per project), **use** it across all those consumers, **share** it with people and
machines, and optionally **graduate** a set into a standalone brand-skill.

## Standard

Use the **Design Tokens Community Group (DTCG) Format Module 2025.10** — the first
stable, vendor-neutral token format (W3C Community Group; not a formal W3C Standard).
We do not invent a format.

- Files: `*.tokens.json` (media type `application/design-tokens+json`)
- Keys: `$value`, `$type` (required); `$description`, `$extensions`, `$deprecated` (optional)
- Aliasing: `{group.token.name}` curly-brace references
- Layering/theming: `$extends` + group inheritance
- Tooling that already reads this: Figma, Style Dictionary v4, Tokens Studio, Pencil
  (as variables/themes), Penpot, Sketch, Supernova, zeroheight.

## Scope model

Global brand base + per-project deltas, resolved by layering.

```
~/.claude/design-tokens/
  registry.json                 # named sets: lab, confide, personal, …
  <set>/base.tokens.json        # global brand source of truth
<project>/.design-tokens/
  project.tokens.json           # $extends a global set; overrides only what differs
```

`registry.json` maps set-name → path and metadata. A project file names its parent
set and overrides only the deltas; resolution merges parent + child.

## Token types (v1 cut — YAGNI)

In scope: `color`, `dimension` (spacing / radius / size), `typography`
(fontFamily / fontSize / fontWeight / lineHeight), `shadow`, `duration`.

Deferred until needed: composite gradient, border, transition, strokeStyle,
cubicBezier-as-first-class.

## Architecture

Skill markdown drives the human-facing doors and orchestration; a small,
dependency-free Python core (`tokens.py`) does all deterministic work. Style
Dictionary is an **optional** power-up for richer platform targets when Node is
present — never required for the common path.

### Deterministic core: `tokens.py` (Python stdlib only)

| Command | Responsibility |
|---------|----------------|
| `validate` | Legal `$type`s, every alias resolves, no circular `$extends` |
| `merge`    | Apply `$extends` layering (global base ← project overrides) |
| `resolve`  | Flatten aliases to concrete values, per theme (light/dark/…) |
| `export-css` | Emit `:root { --token: value }` (+ theme selectors) |

`resolve` and `export-css` are pure functions over a parsed token tree, enabling
golden-file tests.

### The four verbs (skill commands)

| Verb | Behavior |
|------|----------|
| `setup` | Three entry doors, all producing a valid DTCG file at the chosen scope (global or project): **interview** (guided Qs → DTCG), **import** (palette / CSS / Figma export / Pencil variables → normalized DTCG), **edit** (scaffold template + validate). |
| `use` | Resolve (merge global+project, flatten aliases) → always emit **CSS variables**; emit **Tailwind / Swift / Android** if Style Dictionary present; **inject into Pencil** via `set_variables`; **write a context file** Claude generation skills read to stay on-brand. |
| `share` | Commit to git; **export bundle** (DTCG JSON + compiled CSS + readable HTML/MD token doc); output stays plain DTCG so Figma / Tokens Studio import it with zero tooling. |
| `skillify` | Generate a standalone **brand-skill** wrapping one resolved set, formatted for `publish-skill`, so any generation skill can stay on-brand. |

## Data flow

```
authoring door  ──►  *.tokens.json  (canonical, git)
                         │  tokens.py merge + resolve (deterministic)
                         ▼
                    resolved set ──► css vars / tailwind / swift
                                 ──► Pencil variables (set_variables)
                                 ──► Claude context file
                                 ──► brand-skill (skillify) ──► publish-skill
```

## Error handling

Validation fails loudly and specifically on: unknown `$type`, unresolved alias,
circular `$extends`, malformed JSON. `use`/`share` refuse to run on an invalid set;
the error names the offending token path.

## Testing

Golden-file tests: a sample global `base.tokens.json` + a project override file
compile, through merge → resolve → export-css, to a known CSS output. Validation
tests cover each failure mode (bad type, dangling alias, cycle). Tests run with
stdlib only; no Node required.

## Homes

- Skill code: `~/ai_projects/claude-skills/design-tokens/`
- Global token sets: `~/.claude/design-tokens/` (may be its own git repo for sharing)
- Spec: this file, in the `claude-skills` repo.

## Out of scope (v1)

- Real-time two-way Figma sync (export/import only)
- A hosted token registry / web UI
- Composite token types listed under "Deferred" above
- Multi-user permissions on shared sets (git is the access layer)
