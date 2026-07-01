---
name: the-goal
description: A Theory-of-Constraints diagnostic for deciding what to automate with AI agents. Before building any automation, skill, Goal, loop, or schedule, it walks Goldratt's Five Focusing Steps over the user's work system to find the real bottleneck, then recommends the single highest-leverage automation aimed at the constraint plus a what-NOT-to-automate list. Use when the user asks "what should I automate", "where do I point my agents", "prioritize my automation backlog", "which workflow should I agentify", "is this worth building", "find my bottleneck", "what's the highest-leverage thing", when they are about to build a Claude Code skill/Goal/loop/schedule and aren't sure it matters, or during a review of their automations. Guards against the common failure of automating busywork (a local optimum) instead of the constraint.
---

# The Goal — constraint-first automation

Named after Eliyahu Goldratt's *The Goal*. The lesson this skill encodes: **a local optimum is not a global one.** Automating something that feels productive but is not the system's constraint produces no throughput gain. Most wasted automation effort dies here. This skill finds the constraint first, then points exactly one automation at it.

## When to use

Use before building anything, and during reviews:
- "What should I automate?" / "Where do I point my agents?" / "What's the highest-leverage thing right now?"
- The user is about to build a Claude Code skill, Goal, loop, schedule, or workflow and isn't sure it matters.
- The user has a pile of half-useful automations and feels busy but stuck.
- A periodic review of where agent effort is going.

If the user already knows their constraint with confidence and just wants to build, skip the diagnosis and go straight to **Step 4 (elevate)** and the **Recommendation**.

## The core distinction (state this early)

Three ways an automation idea fails, worst first:
1. **It targets a non-constraint.** The worst kind. Even a flawless automation here adds zero throughput; the bottleneck still caps the system. Cut it.
2. **It optimizes a local metric.** Feels productive (inbox zero, faster research) but the global goal does not move.
3. **"Felt busy" is not "moved the needle."** Activity is not throughput. Require a measurable throughput before recommending anything.

## Workflow — the Five Focusing Steps

Run as an interactive diagnostic, one focused question at a time. The LLM's job is to *elicit* the picture and map it to structured inputs; two scripts then do the ranking and the rung selection **deterministically**, so the core calls aren't free-form vibes. Load `references/five-focusing-steps.md` for the full method, definitions (throughput / inventory / operating expense in knowledge-work terms, drum-buffer-rope, Herbie) and example walkthroughs.

**Optional — cenno mode.** If cenno is available and the user prefers panels (or asks to "ask me in panels"), collect the inputs through cenno instead of chat: `choice` 0–3 (or a custom a2ui 0–3 slider) for the ordinal scores, `confirm` for `necessary_condition`/`policy_gate` and the seven rung facts, `text` for the goal/throughput. The answers feed the same two scripts unchanged. Load `references/cenno-mode.md` for the control mapping, `ask_sequence` batching, and how to persist the analysis. Fall back to chat if cenno isn't running — never block.

**Step 0 — Define the goal + throughput measure (gate).** What is this system *for*, and what single *rate* rises when it succeeds (revenue/quarter, products shipped/month, clients served, qualified leads)? No measurable throughput → stop and define one first. **Validate it:** "reclaimed hours" and "inbox zero" are usually operating-expense reduction or local efficiency, *not* throughput, unless free capacity is the system's explicit goal. Reject local-efficiency measures here.

1. **Identify the constraint.** Walk the flow from intent to result; list the candidate steps. For each, elicit ordinal evidence (0–3): throughput-sensitivity (would T rise if this step were 2× faster — the decisive one), wait-before, downstream-starvation, capacity-gap, whether it's a policy/approval gate, and how *annoying* it feels. Also flag `necessary_condition: true` for steps that **must be adequate to function but already are** (e.g. a sales page that converts) — the scorer then labels them "prerequisite: finish, don't over-invest" instead of lumping them with non-binding traps. Then rank deterministically:
   ```bash
   echo '[{"name":"...","throughput_sensitivity":3,"wait_before":2,"downstream_starvation":3,"capacity_gap":2,"annoyance":1}, ...]' | python3 scripts/score_constraints.py
   ```
   Honor the `verdict`: `insufficient_data` → gather more before deciding; `ambiguous` → re-scope or shorten the time window; `constraint_found` → proceed. The script flags the *annoying-but-non-binding* trap automatically.
2. **Exploit it.** Before building anything, get the most from the constraint as it is. Often a non-automation fix (stop interrupting it, batch it, remove a hand-off) beats new tooling. Recommend exploitation first.
3. **Subordinate.** Point everything else — including existing automations — at *serving* the constraint, not at optimizing non-constraints. This often means slowing or ignoring non-constraints (drum-buffer-rope).
4. **Elevate.** Only now add capacity at the constraint with one automation. Pick the rung deterministically (the LLM supplies the yes/no facts; the tree decides):
   ```bash
   python3 scripts/recommend_rung.py --recurring --fixed-steps      # or --bounded-outcome, --streaming-input, etc.
   ```
   See `references/autonomy-ladder.md` for what each rung means. Elevation costs operating expense, so it comes after exploit + subordinate, never before.
5. **Repeat (POOGI).** The constraint moves once relieved. Name the likely next constraint and queue it. Warn against inertia: do not keep polishing the old, now-non-binding step.

## Guardrails (non-negotiable)

- **Never recommend automating a non-constraint.** If the user's proposed automation targets a non-constraint, say so plainly and redirect to the constraint.
- **Require a measurable throughput** before any recommendation. "Make things better" is not a goal.
- **Name local optima out loud** when seen.
- **Exploit and subordinate before elevate.** Do not build new tooling prematurely when a cheaper exploitation fix exists.
- **One constraint-targeting automation at a time**, not a backlog of five.

## Output

Produce a short **constraint analysis** using `assets/constraint-analysis-template.md` with these sections:
- **Goal + throughput measure** — the system's purpose and the one number.
- **The constraint** — where the line stalls, with the evidence that identifies it.
- **Exploit** — the cheapest non-build fix to try first.
- **The one automation** — the single recommendation, the autonomy-ladder rung it sits on (Goal/loop/schedule/...), and why it serves the constraint.
- **Do NOT automate** — the tempting non-constraints to leave alone, named explicitly.
- **Next constraint** — where the bottleneck will likely move, queued for the repeat step.

Before delivering, run this validity checklist (not just shape):
- [ ] throughput is a *rate* tied to the system goal (not a local-efficiency proxy)
- [ ] constraint backed by the scorer's `constraint_found` verdict (or unknowns named)
- [ ] an exploit fix is offered *before* the build
- [ ] exactly **one** automation, with its autonomy-ladder rung
- [ ] the do-NOT-automate list names the rejected non-constraints
- [ ] a next-constraint is queued

End with the call to action: **pick the single constraint-targeting automation and define it as a Goal** (verifiable end-state + conditions), then build it.

## Referenced skills

- **`name-audition`** — sibling diagnostic; same "a local optimum is not safe" discipline, applied to names. (Cross-reference only; not a handoff.)
