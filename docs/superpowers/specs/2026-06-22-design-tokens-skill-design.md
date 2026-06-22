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

- Files: `.tokens` or `.tokens.json` (media type `application/design-tokens+json`).
  We adopt `*.tokens.json` as a house convention, not a standard requirement.
- Keys: `$value` required. `$type` required **directly or by DTCG type resolution**
  (inferred from an alias target or inherited from a parent group). `$description`,
  `$extensions`, `$deprecated` are optional.
- Aliasing: `{group.token.name}` curly-brace references for whole-value aliases.
  DTCG 2025.10 also defines JSON Pointer `$ref` for property-level references; v1's
  resolver handles the curly-brace subset and explicitly flags `$ref` as unsupported
  (see Out of scope), so v1 is a *useful DTCG subset*, not a complete resolver.
- Layering/theming: `$extends` is DTCG **group inheritance** (target is a group;
  same-path tokens override, different paths merge, an override replaces the whole
  token). Our global-base / project-override **registry is a skill-level convention
  built on top of** `$extends`, not part of the standard.
- Tooling: Style Dictionary v4 and Tokens Studio read DTCG directly. Figma, Pencil,
  Penpot, Sketch, Supernova, zeroheight consume it **via their own import / plugin /
  API / adapter** where available — not a guarantee that any of them import plain
  DTCG with zero tooling. Each adapter is verified before we claim it.

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

**This registry layering is a skill convention, not DTCG.** DTCG `$extends` only does
group inheritance within the reference graph. `merge` must therefore define its own
rules explicitly (see Architecture) and the spec names them as a project convention,
not standard behavior.

## Token types (v1 cut — YAGNI)

In scope: `color`, `dimension` (spacing / radius / size), `duration`, and the
`typography` composite. Because `typography` depends on them, its supporting
primitive types are **also first-class in v1**: `fontFamily`, `fontWeight`, and
`number` (for `lineHeight`). `shadow` (a composite over color/dimension/number) is
in scope but lands in the same phase as composite-aware export, not before it.

Deferred until needed: composite gradient, border, transition, strokeStyle,
`cubicBezier` as a first-class authored type.

## Architecture

Skill markdown drives the human-facing doors and orchestration; a small,
dependency-free Python core (`tokens.py`) does all deterministic work. Style
Dictionary is an **optional** power-up for richer platform targets when Node is
present — never required for the common path.

**The core implements a named, deterministic DTCG subset, not the full 2025.10
processing model.** Explicitly in: whole-value `{alias}` resolution, circular-alias
detection, group-level `$type` inheritance, `$extends` group merge with our
documented precedence, value-syntax validation for the v1 types. Explicitly out
(v1): JSON Pointer `$ref`, `$root`, full name-restriction enforcement. Anything in
this subset that diverges from DTCG's processing order is labelled a project
convention in code comments and docs.

### Deterministic core: `tokens.py` (Python stdlib only)

| Command | Responsibility |
|---------|----------------|
| `validate` | Legal `$type`s, every alias resolves, no circular `$extends` |
| `merge`    | Apply global-base ← project-override layering. **Documented precedence:** local path wins over inherited; different paths merge; a token override replaces the whole token; missing parent is a hard error; aliases resolve *after* merge. These rules are a project convention, stated as such. |
| `resolve`  | Flatten aliases to concrete values, per theme (light/dark/…) |
| `export-css` | Serialize to CSS custom properties with **explicit per-type rules**: color objects → CSS color string; `{value, unit}` dimensions → `value+unit`; composites expand to multiple vars with a documented naming scheme (e.g. `--type-body-font-size`, `--type-body-line-height`); shadow arrays → comma-joined `box-shadow` value. Emits `:root` + theme selectors. |

`resolve` and `export-css` are pure functions over a parsed token tree, enabling
golden-file tests. The CSS naming scheme for composite expansion is fixed in v1 and
covered by golden tests so it never drifts silently.

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

## Delivery phases

One `design-tokens` skill, shipped in vertical slices so each phase is independently
useful and testable. We do not build all verbs at once.

| Phase | Ships | Why first/last |
|-------|-------|----------------|
| **v1 (core)** | `validate`, `merge`, `resolve`, `export-css`; `setup edit` (scaffold+validate); `use` → CSS vars + Claude context file | The deterministic spine. Everything else is an adapter over this. |
| **v1.1** | `setup interview` door | Pure orchestration over the v1 core; no new core logic. |
| **v1.2** | Style Dictionary adapter (Tailwind/Swift/Android) | Optional, gated on Node; isolated. |
| **v1.3** | Import door (palette / CSS / Figma export / Pencil) + Pencil injection via `set_variables` | Each importer is a verified adapter; added one at a time. |
| **v1.4** | `share` (git + export bundle + HTML/MD token doc) | Depends on a stable resolved-set output. |
| **v2** | `skillify` (graduate a set into a brand-skill for `publish-skill`) | Highest leverage but depends on everything above being stable. |

Each phase gets its own implementation plan. This spec is the umbrella; the first
plan covers **v1 only**.

## Homes

- Skill code: `~/ai_projects/claude-skills/design-tokens/`
- Global token sets: `~/.claude/design-tokens/` (may be its own git repo for sharing)
- Spec: this file, in the `claude-skills` repo.

## Out of scope (v1)

- JSON Pointer `$ref` / `$root` (curly-brace whole-value aliases only in v1)
- Full DTCG name-restriction enforcement
- Real-time two-way Figma sync (export/import only)
- A hosted token registry / web UI
- Composite token types listed under "Deferred" above
- Multi-user permissions on shared sets (git is the access layer)
