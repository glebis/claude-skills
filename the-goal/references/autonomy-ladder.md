# The autonomy ladder — choosing the rung to elevate the constraint

Once Step 4 (elevate) calls for adding capacity, pick the *lowest* rung that relieves the constraint. Higher rungs cost more operating expense (tokens, maintenance, trust) and carry more risk. Do not climb past what the constraint needs.

## Decision rule (compressed)

- Know the end + a fixed input you have now → **Goal**
- The same constraint task recurs and you re-explain it each time → **skill**
- New work keeps arriving over time and must be processed as it lands → **loop** (or, better, a deterministic **workflow** triggered on a **schedule**)
- Must run unattended at set times → **/schedule → cron → launchd**
- Repeatable and worth hardening into a deterministic pipeline → have an agent author a **workflow**
- The constraint needs always-on or embedded capacity → **Agent SDK** service
- Must never silently fail → **durable execution (Temporal)**

## The rungs

| Rung | What it is | Use when the constraint is… | Cost / risk |
|---|---|---|---|
| **Goal** | One autonomous multi-turn run to a verifiable end-state | a bounded, knowable outcome you can describe and check | low; the default first build |
| **Skill** | A packaged, reusable prompt/procedure invoked by command | a repeated constraint task you keep re-explaining | low; one-time authoring |
| **Loop** | A recurring run over changing input | a stream of new work that must be handled as it arrives | token-hungry; prefer a deterministic workflow if the steps are fixed |
| **/schedule** | Time-triggered runs of a Goal/skill | work that must happen at set times, unattended | needs a session/host running; skills run via schedule, not via loop |
| **Workflow** | Agent solves once, then emits deterministic re-runnable steps | a fixed, repeatable constraint process worth hardening | client feature; can raise token cost — measure |
| **Agent SDK** | An agent embedded in an app/pipeline | the constraint needs embedded or always-on capacity | highest maintenance; real software |
| **Temporal / durable** | Crash-proof, retrying, stateful execution | the constraint process must never silently fail | infrastructure; adopt only when reliability is the constraint |

## Principles

- **Subordinate before you elevate.** If protecting the constraint's time or removing a hand-off (Step 2/3) relieves it, build nothing.
- **Prefer determinism over recurring LLM loops** when the steps are fixed — cheaper, auditable, and the constraint usually wants reliability, not creativity.
- **The hybrid endgame:** an agent *authors* the deterministic workflow that then runs the constraint cheaply. "Agent as workflow developer, not workflow executor."
- **One rung, one constraint.** Build a single thing aimed at Herbie, ship it, then re-run the diagnosis before climbing further.
