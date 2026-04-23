# ODI — Outcome-Driven Innovation Scoring

Tony Ulwick's quantitative cousin to JTBD. Converts outcome statements into a prioritized list via two 1–10 ratings: **importance** and **current satisfaction**.

## When to add ODI

- The user has **3+ candidate outcomes** they're choosing between.
- The user is doing roadmap, scope, or positioning work.
- The user explicitly asks "what should I build first?"

Skip ODI when:
- There's only one outcome on the table.
- The project is pre-product (no baseline satisfaction to measure).
- The user is doing messaging, not prioritization — use Switch forces instead.

## Outcome statement format

ODI outcomes follow a strict template. Do not deviate — the strictness is the value.

```
[Direction] the [metric] it takes to [action] when [situation]
```

- **Direction:** Minimize | Increase | Maintain
- **Metric:** time, likelihood, amount, number of errors, frequency, cost
- **Action:** what the user is trying to do
- **Situation:** the triggering context

**Good:**
- `Minimize the time it takes to prepare launch-readiness docs when shipping a new feature`
- `Minimize the likelihood of missing a customer commitment when the CRM is stale`
- `Increase the number of qualified leads generated when hosting a live workshop`

**Bad:**
- `Better launch prep` (no direction, metric, or situation)
- `Feature that auto-generates docs` (describes solution, not outcome)
- `Users should feel more confident` (feeling, not measurable outcome)

## Scoring

Ask the user two questions per outcome:

1. **Importance:** "On a scale of 1–10, how important is this outcome to the user right now?"
2. **Satisfaction:** "On the same scale, how well does the current solution address it?"

For user-facing research, use actual respondents. For founder-solo work (no users yet), mark the outcome as `importance_source: founder_estimate` and `satisfaction_source: founder_estimate` — still useful but flag lower confidence.

## Opportunity score formula

```
opportunity_score = importance + max(0, importance - satisfaction)
```

- Max score: 20 (importance 10, satisfaction 0 — highly important, totally unmet).
- "Under-served" threshold: ≥ 12.
- "Well-served" threshold: ≤ 8 (don't build here).

Use `scripts/odi_score.py` to compute scores across an outcome list.

## Interpretation cheatsheet

| Importance | Satisfaction | Score | Action |
|---|---|---|---|
| 9 | 3 | 15 | 🎯 prioritize — big gap |
| 9 | 8 | 10 | ⚠️ maintain — already served |
| 4 | 2 | 6 | 🛑 skip — not important |
| 7 | 5 | 9 | 🔶 marginal — investigate |
| 8 | 2 | 14 | 🎯 prioritize |

## Output block

```json
{
  "odi": {
    "outcomes": [
      {
        "statement": "Minimize the time it takes to prepare launch-readiness docs when shipping a new feature",
        "importance": 8.5,
        "satisfaction": 3.2,
        "opportunity_score": 13.8,
        "importance_source": "user_interview | founder_estimate | survey",
        "satisfaction_source": "user_interview | founder_estimate | survey"
      }
    ]
  }
}
```

Include only top 3 outcomes in the output. Sort by `opportunity_score` descending.

## ODI and Switch forces together

ODI tells you **what to build**. Switch forces tell you **how to get people to use it**. Keep them both. The best founder briefs include both: the prioritized outcome, then the Push/Pull/Habit/Anxiety specific to that outcome.
