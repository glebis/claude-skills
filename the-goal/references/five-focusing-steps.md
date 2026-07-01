# The Five Focusing Steps, adapted to AI automation

From Eliyahu Goldratt's *The Goal* and the Theory of Constraints (TOC). The book's plant becomes the user's work system; the agents (Claude Code, Codex, Hermes), Goals, loops and schedules are the capacity you can add. The discipline is unchanged: improve the constraint, not the parts around it.

## The three measures (translate to knowledge work)

- **Throughput (T)** — the rate the system produces the thing it exists for. Pick ONE number: revenue/quarter, products shipped/month, clients served, qualified leads, published pieces. Throughput is the goal made countable. Caveat: "reclaimed hours" or "inbox zero" are usually **operating-expense reduction or local efficiency, not throughput** — count them as T only when free capacity is the system's explicit goal.
- **Inventory (I)** — work started but not yet converted to throughput: half-done drafts, open loops, untriaged inputs, WIP. High inventory hides the constraint.
- **Operating expense (OE)** — what it costs to run the system: your hours, tokens, subscriptions, attention.

The TOC objective: **increase T while reducing I and OE.** Automating something that raises OE (more tokens, more tools to maintain) without raising T is a loss, even if it feels productive.

## "Herbie" — the constraint

In the book, a troop of scouts can only hike as fast as Herbie, the slowest boy. Speeding up everyone else just spreads the line; the troop's pace is still Herbie's. **For a scoped goal and a chosen time window, focus on the one primary binding constraint.** (Complex systems can have several near-binding or interacting constraints; narrowing scope/horizon usually resolves which one binds now. If two score within a hair, re-scope rather than automate both.) Find it before optimizing anything.

The constraint is usually NOT the most annoying step. It is the step where:
- work waits in a queue before it,
- everything downstream starves waiting for it,
- and the global number (T) can't rise until it does.

Common knowledge-work constraints: decisions only the user can make; sales conversations; a review/approval gate; one expert's attention; the user's own context-switching.

## The steps

### 1. Identify the constraint
Walk the flow from intent to delivered result. Ask: where does work pile up? what waits on what? if this step went 2x faster, would T actually rise? The honest answer to the last question finds Herbie. Beware: a freshly relieved constraint moves, so re-identify rather than assume.

### 2. Exploit the constraint
Wring maximum throughput from the constraint **as it is**, before spending anything. Usually not an automation:
- stop interrupting it (protect the constraint's time),
- batch or sequence work to keep it fed,
- remove a hand-off or approval that idles it,
- cut low-value work that consumes it.
Exploitation is the cheapest win and often enough. Recommend it first.

### 3. Subordinate everything else to the constraint
Every other step — and every existing automation — should run at the pace and in service of the constraint, not at its own local maximum. This is where most automation effort goes wrong: people optimize a non-constraint (faster email triage) and the line still moves at Herbie's pace. Subordination often means *slowing down or ignoring* non-constraints, which feels counterintuitive.

**Drum-Buffer-Rope:**
- **Drum** — the constraint sets the beat the whole system marches to.
- **Buffer** — protective time/capacity/WIP ahead of the constraint so it never starves. Size it to the variability of the work; a too-small "just-in-time" buffer starves a variable constraint.
- **Rope** — release new work only at the rate the constraint can absorb, so inventory doesn't balloon.
In practice: schedule and gate agent runs so they feed the constraint just-in-time, not flood it.

### 4. Elevate the constraint
Only now add capacity. This is where an automation earns its place — pointed squarely at Herbie:
- a **Goal** that does the constraint's repeatable part autonomously,
- a **skill** packaging a repeated constraint task,
- a **loop/schedule** that keeps the constraint fed or clears its queue over time,
- a **workflow** for a deterministic constraint process,
- an **Agent SDK** service when the constraint needs always-on capacity.
See `autonomy-ladder.md` for choosing the rung. Elevation costs OE, so it comes after exploitation and subordination, never before.

### 5. Repeat — and beware inertia
Relieving the constraint moves it elsewhere (a "process of ongoing improvement," POOGI). Two failure modes to warn against:
- **Inertia:** continuing to optimize the old constraint that is no longer binding (the classic trap — you fell in love with the automation you built).
- **Policy constraints:** sometimes the new constraint isn't a step but a rule or habit. Name it.
Queue the likely next constraint so the system keeps improving instead of stalling.

## Worked example

Goal: grow course revenue. Throughput = launches that sell out.
- **Identify:** the user automates email triage and research, but launches stall because the *sales page + offer* never gets finished — that's Herbie. Email was never the constraint.
- **Exploit:** block protected time for the offer; stop polishing research.
- **Subordinate:** point research/agents at feeding the offer (proof, testimonials), not at general productivity.
- **Elevate:** one Goal that drafts and iterates the sales page to a verifiable spec.
- **Repeat:** once the page ships, the next constraint becomes traffic/audience — queue it.

The mistake the skill prevents: spending the weekend on the email-sorting agent (a real local optimum) while the binding constraint, the unfinished offer, goes untouched.
