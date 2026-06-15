---
name: repo-prep
description: Interactively prepare a code repository for publication — LICENSE, NOTICE, AUTHORSHIP, README sections, package metadata, .gitignore, community docs (CONTRIBUTING/CODE_OF_CONDUCT/SECURITY/CHANGELOG), .github templates (issues/PR/CI/dependabot), a promo "more from the author" block, and conditional EU/Germany legal compliance (CRA, AI Act, GDPR, Impressum, product liability). Includes a dedicated authorship wizard that documents human decisions, judgment, direction, and art direction with jurisdiction-aware legal framing. Use when setting up a new repo for release, adding missing legal/meta/community files, writing an AUTHORSHIP record for AI-assisted work, or asking "prepare this repo for GitHub / open-sourcing".
---

# Repo Prep

Interactively scaffold the legal, metadata, community, and compliance files a
repository needs before publication — consistently, from a central author
profile, with author choices respected per repo.

## When to use

- Preparing a new or existing repo for GitHub / open-sourcing.
- Adding missing LICENSE, NOTICE, AUTHORSHIP, README sections, or package metadata.
- Writing a defensible **AUTHORSHIP** record for AI-assisted work (the wizard).
- Adding community docs or `.github/` templates.
- Checking **EU/Germany compliance** obligations for a repo.

## Operating principles

- **Interactive, not assumed.** Ask the user for choices (see *Asking questions*
  below); respect the author profile's `defaults` but confirm per repo. Don't
  blindly dump templates.
- **Idempotent.** Detect what already exists; skip or refresh, never clobber
  silently. Show a plan before writing.
- **Evidence over assertion** (especially authorship): mine the repo for facts.
- **Confirm outward-facing actions** (anything via `gh`, pushes) before running.
- Follow the user's git conventions — commit only when asked.

## Asking questions (interview transport)

Prefer **cenno** when it is installed — it gives a nicer panel, progress dots,
and voice input (great for the reflective authorship answers).

1. **Detect cenno once per run:** `ToolSearch` for
   `mcp__cenno__ask_sequence`. If the tools resolve, use cenno; otherwise fall
   back to `AskUserQuestion` (choices) / plain conversational prompts (free text).
2. **When using cenno:**
   - Multi-question flows (the authorship wizard, scope selection) →
     `mcp__cenno__ask_sequence` with `flow: "question"`; it auto-fills progress dots.
   - Single questions → `mcp__cenno__ask_user`.
   - Use `input.kind: "choice"` + `choices` for pick-one; `"confirm"` for yes/no;
     `"voice_text"` for reflective free-text (Decisions, Judgment, Direction, Art
     Direction); `"scale"` for ratings.
   - Parse the returned JSON (`{answers: [...]}` / `{answer, ...}`). Handle
     `{answered: false}` (timeout) by retrying or falling back.
3. **If cenno is wanted but not installed**, mention it can be set up via the
   `cenno` skill; do not block — fall back gracefully.

## Central author profile (single source of truth)

Identity, promo links ("ads"), and defaults live in
`~/.config/personal-os/repo-prep/profile.toml` (override with `REPO_PREP_PROFILE`).

1. On first run, if it doesn't exist, copy `assets/templates/profile.example.toml`
   there and walk the user through filling it (name, email, github, url, promo
   projects, defaults). It is pre-seeded for this author.
2. Read it at the start of every run to resolve `{{author}}`, `{{email}}`,
   `{{github}}`, the promo block, and default choices.

## Workflow

1. **Detect** — inspect the repo: manifest/ecosystem (`pyproject.toml`,
   `package.json`, `Cargo.toml`, `go.mod`), existing files, `git remote`, default
   branch, whether it's already on GitHub. Read the author profile.
2. **Scope** — confirm which components to do via `AskUserQuestion` (core /
   community / .github / promo / compliance / gh remote). Pre-fill from profile
   `defaults`.
3. **Resolve placeholders** — once, per `references/checklist.md`.
4. **Generate** — for each chosen component, create files from
   `assets/templates/` and `assets/github/`, filling placeholders. Use
   `scripts/fetch_license.py` for LICENSE. Edit package metadata inline.
5. **Authorship** — if doing AUTHORSHIP.md, run the wizard (below), don't just
   fill the template.
6. **Compliance** — if requested or the author is EU-based, run the gating
   questions in `references/eu-germany-compliance.md` and add only what applies.
7. **gh remote** (optional) — confirm, then create/configure the repo.
8. **Verify** — run the test suite (metadata edits can break builds); show the
   diff; commit only if asked.

Full item-by-item detail, placeholder table, and ecosystem detection:
**`references/checklist.md`** (read it before generating).

## The authorship wizard

A first-class feature. To produce a defensible `AUTHORSHIP.md` for AI-assisted
work, **read and follow `references/authorship-wizard.md`**. It:

- gathers external evidence first (ADRs, git log, changelog, AI session logs,
  `CLAUDE.md`/`AGENTS.md`, design tokens) and offers a draft to edit;
- asks the **jurisdiction** first, then interviews across five sections —
  **Decisions, Exercise of Judgment, Goal Setting & Direction, Art Direction,
  AI Implementation**;
- writes a **Legal & Copyright** section with jurisdiction-aware framing
  (US human-authorship bar, EU/Germany "own intellectual creation", UK CGW);
- always states it is **not legal advice**.

Output template: `assets/templates/AUTHORSHIP.md`.

## EU / Germany compliance

`references/eu-germany-compliance.md` covers CRA (SBOM, vuln reporting), AI Act
Art. 50 transparency, German Impressum (DDG), GDPR, the Product Liability
Directive, and the EAA. Obligations are **conditional** — ask the gating
questions and add only what applies. Not legal advice.

## Resources

- `assets/licenses/` — bundled MIT, BSD-3-Clause (offline); others fetched.
- `assets/templates/` — AUTHORSHIP, CODE_OF_CONDUCT, CONTRIBUTING, SECURITY,
  NOTICE, CHANGELOG, profile.example.toml.
- `assets/github/` — PR + issue templates, dependabot, CI workflows (python/node).
- `scripts/fetch_license.py` — write a filled LICENSE for any SPDX id.
- `references/` — `checklist.md`, `licenses.md`, `authorship-wizard.md`,
  `eu-germany-compliance.md`.
