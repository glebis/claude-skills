# Job Map — 8 Universal Steps (from ODI)

Tony Ulwick's observation: every functional job follows the same 8-step sequence. Use the job map to decompose a vague job into concrete outcome statements.

## When to use

- The user says "what should I build first?" and has a defined job but no prioritized outcomes.
- ODI scoring mode is active and you need candidate outcome statements.
- The user's job statement is too broad — the map forces decomposition.

## The 8 steps

| Step | What happens | Example (launch-readiness doc) |
|------|-------------|-------------------------------|
| **1. Define** | Determine what needs to be accomplished | Decide which features/milestones to include in the readiness review |
| **2. Locate** | Find inputs and items needed | Find the PRs, tickets, Slack decisions, and stakeholder sign-offs |
| **3. Prepare** | Set up the environment / organize inputs | Open the template, pull up source systems, clear the calendar |
| **4. Confirm** | Verify readiness before executing | Check that all inputs are current (not 24h stale), confirm who's attending |
| **5. Execute** | Perform the core task | Write the readiness doc: populate sections, summarize risks, flag gaps |
| **6. Monitor** | Track whether execution is on track | Spot-check claims against source of truth, verify nothing was missed |
| **7. Modify** | Make adjustments as needed | Update doc when a last-minute PR lands or a blocker gets resolved |
| **8. Conclude** | Finish and wrap up | Share the doc, file it, confirm all reviewers have access |

## How to generate outcomes from the map

For each step, ask: "What could go wrong here? What takes too long? What requires too much effort?"

Each answer becomes a candidate outcome statement:

```
[Direction] the [metric] it takes to [action from this step] when [situation]
```

A typical job produces 5-15 outcomes per step, 50-150 total. For a CLI interview, pick the 3-5 steps where the user reports the most pain and generate 3-5 outcomes per step. Don't try to cover all 8 exhaustively.

## Steps most often skipped (but shouldn't be)

- **Confirm** — people assume inputs are ready. This is where stale data kills quality.
- **Monitor** — "I'll check it later" means nobody checks. This is where errors compound.
- **Conclude** — the handoff step. Dropped handoffs = the next person starts from scratch.

## Connecting to Switch forces

The job map tells you WHERE in the process the pain lives. Switch forces tell you WHY the user hasn't solved it yet. Together:

- Job Map step with high pain + strong Push = your core feature
- Job Map step with high pain + strong Habit = needs a migration path, not just a feature
- Job Map step with low pain across all users = don't build here
