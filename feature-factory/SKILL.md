---
name: feature-factory
description: This skill should be used when taking a single software feature from intent to shipped as a solo developer — goal-first, TDD, deterministic verification, evidence only where it earns its keep, and human judgment at the two moments that matter (goal approval, merge). Trigger when the user says "let's build feature X", "ship this feature", "run this through the factory", "write a goal contract", "feature-factory", or wants a disciplined intent→merge loop that resists process bloat. NOT for whole-product planning, multi-feature roadmaps, or autonomous multi-agent swarms.
---

# Feature Factory

A goal-driven, local-first loop for taking **one** feature from intent to shipped. The whole method exists to hold a single line in tension: **don't let the process outrun the feature.** Keep the spine (goal → TDD → deterministic verify → human merge → evidence-when-it-matters); delete ceremony aggressively.

This is a **behavior guide, not an engine.** Do not build generic config, executors, telemetry, optimizers, or a universal `factory verify` wrapper. Run the behavior; package nothing the feature didn't earn.

## Core principle

*The human defines the desired system state. Agents maintain the specifications. Tests and evidence decide whether reality complied.* Two human gates are always required — approve the Goal Contract (cheap-to-change moment) and review the merge (irreversible moment) — plus a **conditional third** (plan approval) when a size/risk trigger fires (see step 2). Everything between is a single focused agent loop.

## When to apply vs skip

- **Apply** to a bounded, shippable feature.
- **Skip the heavy parts** for trivial changes — an S-size fix is just: short goal in your head → TDD → run the repo's checks → merge. Don't generate documents for a one-liner.
- **Refuse XL** — if the feature is multi-day with shared contracts, migrations, auth/billing, or product ambiguity, **split it first**; do not run an XL feature through this loop whole.

## The loop (six steps)

### 1. Intake — create or repair a Goal Contract
**Make a quick size call now** (step 2 formalizes it) — you need it to decide how heavy intake should be. For **S-size/trivial** changes, skip the file — a short goal stated in chat and confirmed by the human is enough; jump to step 3. Otherwise, copy `assets/goal-contract.md` into the target repo as `goal.md` under a feature dir (suggested: `docs/factory/<date>-<slug>/goal.md`); see `assets/goal-contract-example.md` for a filled example of the calibration expected. The template's core fields are enough for M features — the conditional half is for L or when a trigger fires. **Draft it from the request first, then have the human confirm/correct each field** — don't block on a blank form, and don't proceed past intake until the human has approved the wording. Enforce:
- All `<!-- required -->` fields present: **Smallest shippable slice** and **Stop condition**.
- Respect the caps (`≤3`, `≤5`). A capped goal stays a goal, not waterfall-in-markdown.
- **Every desired outcome maps to concrete evidence.** Reject vague/solution-coupled outcomes.
- **Fail rule:** if a goal can't produce evidence, it's a wish with better formatting — it doesn't pass.
- Agents may propose **Goal Amendments**; never silently rewrite the goal.

### 2. Size + risk triage — decide how much process
- **Size:** S (<½ day, no public API/migration) · M (1–2 days, some UI/integration) · L (multi-day; shared contracts, migrations, auth/billing/permissions, AI behavior, data retention) · XL (split first).
- **Risk:** R0 none · R1 internal dev-assist · R2 user-facing low-stakes · R3 sensitive data/recommendations/profiling · **R4 prohibited/high-risk (EU AI Act Art 5, or your jurisdiction's equivalent) or needs legal review → STOP**, do not implement until externally reviewed. Also screen Art 50 labelling (or local equivalent) for AI-generated/chatbot/deepfake output.
- **Default to less process.** Add plan approval, a tracker, visual evidence, or an audit (plan and/or diff — see step 4) **only** when size/risk triggers fire (see `references/process-budget.md`). When in doubt, do less.
- **Plan audit (when plan approval fires):** before building, have an independent fresh-context reviewer (a separate agent/model, e.g. Codex) check the goal+plan against the **actual codebase** for ordering, architecture, and correctness flaws. This is the cheapest place to catch blockers — fix the plan, don't discover them mid-build. Same timeout + self-review fallback as step 4.

### 3. TDD implementation loop
Work on a **feature branch or worktree** — the merge gate is only a real decision point if the work isn't already on the mainline. Then red → green → refactor, in a **single focused loop. No swarm, no parallel fan-out, no speculative abstraction, no silent scope expansion.** Write the failing test first. Use any available TDD skill (e.g. `superpowers:test-driven-development`); otherwise just follow red → green → refactor directly.
- **Spike escape hatch:** if you don't yet know enough to write the failing test (unfamiliar library, unclear API behavior), timebox a throwaway spike, discard the spike code, then start red → green with what you learned. Don't fake a test, and don't let the spike quietly become the implementation.
- **Determinism:** no wall-clock/sleep-based test assertions — use synchronous barriers/callbacks.
- **Contract change ⇒ verify all call-sites:** changing a shared function's contract requires enumerating every caller/parallel path and proving each honors it.

### 4. Verification & audit discipline
Run the target repo's **real** verify commands (test · lint · typecheck · build, plus secrets-scan if available) — identical locally and in CI. If the repo has a `factory verify` / project verify command, call it; **if not, use the repo's actual commands and record them (the exact commands + output) in `evidence/verify.log` under the feature dir. Do not invent a universal wrapper before the repo earns it.**
- **Flake = failure, not retry.** Any intermittent fail blocks merge until root-caused or rewritten deterministically. No quarantine.
- **Audit (independent fresh-context review) is a standard step, not an afterthought.** A separate agent or model with fresh context (e.g. Codex, or a different model) reviews the work at two touchpoints: **(a) plan audit** before building (see step 2) and **(b) diff audit** before the merge gate. How it scales with size/risk — when it's required, when it's skippable, timeout + self-review fallback — is defined once in `references/process-budget.md`; follow that table rather than re-deriving it. Persist findings in `evidence/audit-*.md`; fold them back into the plan/diff before proceeding (an audit you don't act on is theatre). The human gates still decide — an audit informs them, it doesn't replace goal/merge approval.

### 5. Evidence packaging
Persist only **relevant** evidence under the feature dir's `evidence/`: `verify.log` (commands + output), and — **only for qualifying UI changes** — screenshots in `evidence/screenshots/` (what qualifies, and the one-viewport default, is defined in `references/process-budget.md` under "Visual evidence"). Goal-traceability table only when it adds signal. Evidence is an artifact, not a claim: "done" must be auditable. Do **not** let the evidence folder become the product.
- **Escape hatch — statistical/behavioral claims:** if a desired outcome is a measured effect on noisy real-world data (engagement, latency distributions, refusal rates, ML metrics) rather than a pass/fail test, a green suite does **not** prove it. Pre-register the metric in the Goal Contract and evaluate it as a real experiment (permutation-test it, adversarially review the analysis) — using the [`rigorous-experiments`](https://github.com/glebis/claude-skills/tree/main/rigorous-experiments) skill if available, otherwise a held-out check. Don't assert a measured outcome you didn't actually test — that's the same gamed-proxy failure the fail rule catches, one layer down.

### 6. Retro deletion hook (the curator)
After shipping, write exactly four lines in `retro.md` under the feature dir (append to `goal.md` only when a separate file is impractical — one greppable default beats two conventions):
1. What slowed shipping?
2. What caught a real bug?
3. Which artifact was never used?
4. **What gets deleted before the next feature?**

This is the entire self-improvement mechanism at small N — manual, human-readable, impossible to over-build. Do **not** add usage telemetry, dashboards, or counters. (Aggregate into a markdown table only after ~5 features; consider anything heavier only after ~10.)

## Semantic-preservation guard (when editing this method's own artifacts)
This guard applies when editing the method itself — the Goal Contract template, the risk rubric, or the verify checks — **not** during ordinary feature work. When any edit, optimizer, or rewrite touches those artifacts, **do not let polished prose delete load-bearing constraints.** Before accepting a rewrite, confirm it preserves: required fields, the `≤N` caps, the fail rule, stop condition, smallest shippable slice, risk classification, evidence mapping, no-silent-rewrite, and no-engine/config-abstraction. On conflict, **preserve operational utility over readability.** Details: `references/semantic-preservation.md`.

## Issue tracking — bd or Linear, per feature (no abstraction)
Tracking is **conditional**: create an epic + issues **only if the feature genuinely decomposes into >1 tracked task.** A single-task S/M feature needs no tracker. The human picks one ledger per feature in the Goal Contract's `## Tracker` section (`bd | linear | none`) — there is **no adapter layer**.
- **`bd` (beads)** — default for local/solo, git-native, dependency-aware: `bd init` if no `.beads` store; epic = parent bead, tasks = child beads, deps via `bd link`.
- **Linear** — when work must be visible to others or already lives there: use whatever Linear access this environment provides (a Linear CLI or MCP); epic = project/parent issue, tasks = issues. If Linear was the human's explicit choice but isn't available here, **stop and ask** — switching to `bd`/`none` is a Goal Amendment, not a silent downgrade.
- Never open both a Linear project **and** a beads epic for the same work.

## What stays manual / out of scope (do not build)
GEPA/template optimization · artifact-usage telemetry · generic `pipeline.config` · executor abstraction · automatic tracker wiring · visual-evidence matrix · bake-off automation · risk governance beyond self-assessment prompts · auto-updating the agent-instructions file (`AGENTS.md` / `CLAUDE.md`) · **anything that smells like "the engine."** The method earns an engine only after 5–10 real features, not before.

## Portability — running this from any agent (Codex, Copilot, Gemini, …)
This skill is plain markdown and platform-neutral: the loop is shell/CLI work, not Claude-specific tooling. Anything named here (`bd`, Linear, a TDD sub-skill, a second-opinion model) is **optional** — if it isn't available in the current environment, use the stated fallback and continue; a missing optional tool never blocks unless tracking is explicitly required.

Agents that don't auto-discover skills (e.g. the Codex CLI) won't pick this up just because the files exist. To make it discoverable in a target repo, add an entry to that repo's agent-instructions file (`AGENTS.md`, or `CLAUDE.md`):

```md
## feature-factory
When asked to build/ship a single feature, or to "write a goal contract", read
<path-to>/feature-factory/SKILL.md and follow it. For non-trivial features, copy
<path-to>/feature-factory/assets/goal-contract.md to docs/factory/<date>-<slug>/goal.md.
```

When following this without a skill-runner, read `references/process-budget.md` (size/risk triggers) and `references/semantic-preservation.md` (only when editing the method's own artifacts) directly.

When copying this skill into another repo, copy only its content files (`SKILL.md`, `assets/`, `references/`) — local tool state (e.g. `.enzyme/`, `.claude/`) may sit alongside them and must not ship.

## Background
Distilled from the feature-factory method — public repo: **https://github.com/glebis/feature-factory** (README + Goal Contract template). The fuller design spec and the three external-audit research streams are kept privately; this skill is the runnable distillation. The highest-risk assumption to stay honest about: a process that worked on one bounded, logic-heavy pilot is not yet proven to stay lightweight on messy UI/integration work — pressure-test it on a deliberately different feature next.
