---
name: feature-factory
description: This skill should be used when taking a single software feature from intent to shipped as a solo developer — goal-first, TDD, deterministic verification, evidence only where it earns its keep, and human judgment at the two moments that matter (goal approval, merge). Trigger when the user says "let's build feature X", "ship this feature", "run this through the factory", "write a goal contract", "feature-factory", or wants a disciplined intent→merge loop that resists process bloat. NOT for whole-product planning, multi-feature roadmaps, or autonomous multi-agent swarms.
---

# Feature Factory

A goal-driven, local-first loop for taking **one** feature from intent to shipped. The whole method exists to hold a single line in tension: **don't let the process outrun the feature.** Keep the spine (goal → TDD → deterministic verify → human merge → evidence-when-it-matters); delete ceremony aggressively.

This is a **behavior guide, not an engine.** Do not build generic config, executors, telemetry, optimizers, or a universal `factory verify` wrapper. Run the behavior; package nothing the feature didn't earn.

## Core principle

*The human defines the desired system state. Agents maintain the specifications. Tests and evidence decide whether reality complied.* Two human gates only: approve the Goal Contract (cheap-to-change moment), review the merge (irreversible moment). Everything between is a single focused agent loop.

## When to apply vs skip

- **Apply** to a bounded, shippable feature.
- **Skip the heavy parts** for trivial changes — an S-size fix is just: short goal in your head → TDD → run the repo's checks → merge. Don't generate documents for a one-liner.
- **Refuse XL** — if the feature is multi-day with shared contracts, migrations, auth/billing, or product ambiguity, **split it first**; do not run an XL feature through this loop whole.

## The loop (six steps)

### 1. Intake — create or repair a Goal Contract
Copy `assets/goal-contract.md` to the target repo (suggested: `docs/superpowers/factory/<date>-<slug>/goal.md`). Fill it *with* the human; the human approves the wording. Enforce:
- All `<!-- required -->` fields present: **Smallest shippable slice** and **Stop condition**.
- Respect the caps (`≤3`, `≤5`). A capped goal stays a goal, not waterfall-in-markdown.
- **Every desired outcome maps to concrete evidence.** Reject vague/solution-coupled outcomes.
- **Fail rule:** if a goal can't produce evidence, it's a wish with better formatting — it doesn't pass.
- Agents may propose **Goal Amendments**; never silently rewrite the goal.

### 2. Size + risk triage — decide how much process
- **Size:** S (<½ day, no public API/migration) · M (1–2 days, some UI/integration) · L (multi-day; shared contracts, migrations, auth/billing/permissions, AI behavior, data retention) · XL (split first).
- **Risk:** R0 none · R1 internal dev-assist · R2 user-facing low-stakes · R3 sensitive data/recommendations/profiling · **R4 prohibited/high-risk (EU AI Act Art 5) or needs legal review → STOP**, do not implement until externally reviewed. Also screen Art 50 labelling for AI-generated/chatbot/deepfake output.
- **Default to less process.** Add plan approval, a tracker, visual evidence, or adversarial review **only** when size/risk triggers fire (see `references/process-budget.md`). When in doubt, do less.

### 3. TDD implementation loop
Red → green → refactor, in a **single focused loop. No swarm, no parallel fan-out, no speculative abstraction, no silent scope expansion.** Write the failing test first. See the `superpowers:test-driven-development` skill for the discipline if available.
- **Determinism:** no wall-clock/sleep-based test assertions — use synchronous barriers/callbacks.
- **Contract change ⇒ verify all call-sites:** changing a shared function's contract requires enumerating every caller/parallel path and proving each honors it.

### 4. Verification discipline
Run the target repo's **real** verify commands (test · lint · typecheck · build, plus secrets-scan if available) — identical locally and in CI. If the repo has a `factory verify` / project verify command, call it; **if not, use the repo's actual commands and record them in the goal dir. Do not invent a universal wrapper before the repo earns it.**
- **Flake = failure, not retry.** Any intermittent fail blocks merge until root-caused or rewritten deterministically. No quarantine.
- **External validators (codex / fresh-context subagent) are not default** — invoke only for non-trivial diffs, shared contracts, or auth/data/risk areas, anchored on objective signals, **under a wall-clock timeout with a self-validation fallback** (never silently block on a hung validator).

### 5. Evidence packaging
Persist only **relevant** evidence under the goal dir's `evidence/`: test output, verify log, and — **only for qualifying UI changes** (user-visible layout/styling/onboarding/auth/safety) — screenshots at one primary viewport. Goal-traceability table only when it adds signal. Evidence is an artifact, not a claim: "done" must be auditable. Do **not** let the evidence folder become the product.
- **If a desired outcome is a statistical or behavioral claim** (a measured effect on noisy real-world data — engagement, latency distributions, refusal rates, ML metrics) **rather than a pass/fail test, run the evidence through the [`rigorous-experiments`](https://github.com/glebis/claude-skills/tree/main/rigorous-experiments) skill:** pre-register the metric in the Goal Contract, permutation-test it, and adversarially review the analysis. Don't assert a measured outcome you didn't actually test — that's the same gamed-proxy failure the fail rule exists to catch, one layer down.

### 6. Retro deletion hook (the curator)
After shipping, write exactly four lines:
1. What slowed shipping?
2. What caught a real bug?
3. Which artifact was never used?
4. **What gets deleted before the next feature?**

This is the entire self-improvement mechanism at small N — manual, human-readable, impossible to over-build. Do **not** add usage telemetry, dashboards, or counters. (Aggregate into a markdown table only after ~5 features; consider anything heavier only after ~10.)

## Semantic-preservation guard (always on)
When any edit, optimizer, or rewrite touches the Goal Contract template, the risk rubric, or verify checks, **do not let polished prose delete load-bearing constraints.** Before accepting a rewrite, confirm it preserves: required fields, the `≤N` caps, the fail rule, stop condition, smallest shippable slice, risk classification, evidence mapping, no-silent-rewrite, and no-engine/config-abstraction. On conflict, **preserve operational utility over readability.** Details: `references/semantic-preservation.md`.

## Issue tracking — bd or Linear, per feature (no abstraction)
Tracking is **conditional**: create an epic + issues **only if the feature genuinely decomposes into >1 tracked task.** A single-task S/M feature needs no tracker. The human picks one ledger per feature via a `tracker: bd | linear | none` line — there is **no adapter layer**.
- **`bd` (beads)** — default for local/solo, git-native, dependency-aware: `bd init` if no `.beads` store; epic = parent bead, tasks = child beads, deps via `bd link`.
- **Linear** — when work must be visible to others or already lives there: use the Linear CLI (`~/.claude/skills/linear/scripts/linear`) or the linear MCP; epic = project/parent issue, tasks = issues.
- Never open both a Linear project **and** a beads epic for the same work.

## What stays manual / out of scope (do not build)
GEPA/template optimization · artifact-usage telemetry · generic `pipeline.config` · executor abstraction · automatic tracker wiring · visual-evidence matrix · bake-off automation · risk governance beyond self-assessment prompts · auto-updating CLAUDE.md · **anything that smells like "the engine."** The method earns an engine only after 5–10 real features, not before.

## Background
Distilled from the feature-factory method — public repo: **https://github.com/glebis/feature-factory** (README + Goal Contract template). The fuller design spec and the three external-audit research streams are kept privately; this skill is the runnable distillation. The highest-risk assumption to stay honest about: a process that worked on one bounded, logic-heavy pilot is not yet proven to stay lightweight on messy UI/integration work — pressure-test it on a deliberately different feature next.
