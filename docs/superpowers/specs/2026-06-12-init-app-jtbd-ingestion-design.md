# JTBD Ingestion for init-* skills — Design Spec

**Date:** 2026-06-12
**Status:** Approved — ready for planning
**Author:** Gleb + Claude (brainstormed)

## 1. Purpose

Extend the project-scaffolding skills (`init-tauri-app` now; `init-xcode-app` later) to optionally
ingest a `jtbd.json` artifact produced by the `/jtbd` skill and pre-populate the new project's
product context. This extends the existing superpowers handoff contract
(`claude-skills/jtbd/references/superpowers_handoff.md`) one hop further:
**jtbd.json → brainstorm → plan → code** becomes **jtbd.json → scaffolded project files**.

The feature is purely additive: with no artifact, the skill behaves exactly as it does today.

## 2. Source contract

`/jtbd` emits `jtbd.json` (schema: `solopreneur-vault/references/jtbd-schema.md`) with fields:
`name`, `hook`, `jtbd.{situation,motivation,outcome}`, `problem.{what_hurts,cost_today}`,
`needs.{functional[],emotional[],social[]}`, `switch_forces.{push,pull,habit,anxiety}`,
`outputs[]`, `before_after.{before,after}`, `scenarios[]`, `guardrails[]`,
`evidence.{source,quotes[],weaknesses[]}`, `open_questions[]`, `version`.

Required for ingestion: `name`, `hook`, `jtbd`. All others optional → empty sections if absent.

## 3. Where it slots in (runtime flow)

A new optional step **1.5 — Ingest JTBD (optional)**, between "1. Gather inputs" and "2. Scaffold
base" in SKILL.md.

### 3.1 Resolve & confirm
Resolution order (first hit wins):
1. Explicit path passed to the skill (e.g. invoked with `~/jtbd/<slug>/jtbd.json`).
2. `./jtbd.json` (cwd / intended parent).
3. `~/jtbd/<name>/jtbd.json` (using the gathered app name).

On a hit, **echo the `hook` and ask the user to confirm** before using it. No silent pickup.

### 3.2 Validate
- Parse JSON. If parse fails or `name`/`hook`/`jtbd` missing → **warn and proceed without
  ingestion** (never abort the scaffold over a malformed brief).
- Missing optional fields render as empty/omitted sections, not errors.

### 3.3 Pre-fill
If a valid artifact is confirmed, pre-fill the name/identifier prompts from `name`
(default `<name>` / `com.glebkalinin.<name>`), still user-confirmable.

## 4. Generated artifacts (the mapping)

| Source field(s) | Destination |
|---|---|
| `name`, `hook` | `README.md` tagline; `docs/PRODUCT.md` title |
| `jtbd.{situation,motivation,outcome}` | `docs/PRODUCT.md` "The Job"; AGENTS.md product section (who/when + outcome) |
| `problem.{what_hurts,cost_today}` | `docs/PRODUCT.md` "Problem" |
| `needs.{functional,emotional,social}` | `docs/PRODUCT.md` "Needs" |
| `switch_forces.*` | `docs/PRODUCT.md` "Switch forces" |
| `before_after.*` | `docs/PRODUCT.md` "Before / After" |
| `scenarios[]` | `docs/PRODUCT.md` "Scenarios" |
| `guardrails[]` | AGENTS.md "Must NOT do" list; `docs/PRODUCT.md` "Guardrails"; `docs/internal/guardrails-check.md` review checklist |
| `evidence.quotes[]` | `docs/PRODUCT.md` "Evidence" |
| `open_questions[]` | `docs/PRODUCT.md` "Open questions" |
| `hook`, source path, `version` | AGENTS.md product section footer; `docs/PRODUCT.md` footer (`Source JTBD: <path>`) |
| (whole file) | copied verbatim to **project-root `jtbd.json`** (handoff Pattern 3 discovery) |

Four concrete outputs:
1. **`docs/PRODUCT.md`** — full human-readable brief (all sections above) + `Source JTBD: <path>` footer.
2. **AGENTS.md "Product context" section** — injected into the core AGENTS.md: one-line `hook`,
   who/when + outcome, a **"Must NOT do (from JTBD guardrails)"** bullet list, and a link to
   `docs/PRODUCT.md`. Placed near the top so every coding agent reads the *why* first.
3. **`docs/internal/guardrails-check.md`** — a manual pre-release review checklist, one unchecked
   box per guardrail (`- [ ] <guardrail>`). Documentation/process only; not CI-enforced.
4. **Root `jtbd.json`** — verbatim copy of the source (never mutate the original).

## 5. Reuse across skills

The mapping is factored into reusable assets so `init-xcode-app` consumes them verbatim:
- `assets/jtbd/jtbd-map.md` — the field→destination mapping + rendering rules (this spec §4).
- `assets/jtbd/PRODUCT.md.template` — the brief template with `{{placeholders}}`.
- `assets/jtbd/agents-product-section.md.template` — the AGENTS.md injection block.
- `assets/jtbd/guardrails-check.md.template` — the checklist template.

Only the **AGENTS.md injection point** is skill-specific (where in that skill's AGENTS.md the
product section lands). Everything else is shared.

## 6. Error handling

- Malformed/partial JSON → warn, skip ingestion, scaffold normally.
- `name` in jtbd ≠ user's chosen app name → use the user's choice; copy jtbd.json unchanged.
- Source path unreadable after confirmation → warn, skip ingestion.
- Never edit or move the user's source artifact; only copy.

## 7. Testing

- Fixture: `assets/jtbd/fixtures/sample-jtbd.json` (a minimal valid artifact).
- Smoke: scaffold with the fixture as the jtbd path; assert that `docs/PRODUCT.md`,
  the AGENTS.md "Product context" section, `docs/internal/guardrails-check.md`, and root
  `jtbd.json` all exist and contain the fixture's `hook` and at least one guardrail.
- Negative: run with a deliberately malformed jtbd.json → assert the scaffold still completes and
  no product artifacts are written.

## 8. Non-goals

- No module/framework auto-inference from JTBD content (stays a human technical choice).
- No `/jtbd` auto-invocation when no artifact is found (proceed as today).
- No mutation of the user's source artifact.
- No CI/lint enforcement of guardrails (checklist is manual).
- `init-xcode-app` itself (separate skill) — this spec only makes the mapping reusable by it.
