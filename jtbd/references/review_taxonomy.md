# Review-Mining Taxonomy

How `scripts/mine_reviews.py` clusters reviews and what each cluster means for the downstream JTBD interview.

## Input expectations

- CSV with columns: `text`, optionally `rating`, `date`, `source`, `author`.
- Or JSON array of objects with at least a `text` field.
- Minimum 15 reviews for clustering to be meaningful. Below that, treat as anecdotes, not patterns.

## Three-axis clustering

Every review fragment is tagged on three axes before being placed in a cluster.

### Axis 1 — Pain (what hurts)

Which of these categories fits the review best:

- **time_cost** — "takes forever," "wastes my day"
- **quality_cost** — "gets things wrong," "unreliable"
- **social_cost** — "embarrassing," "my boss yelled"
- **cognitive_cost** — "confusing," "I can't figure out how"
- **money_cost** — "too expensive," "not worth it"
- **trust_cost** — "lost my data," "can't count on it"

### Axis 2 — Outcome (what they wanted instead)

What the reviewer implicitly or explicitly wanted:

- **speed** — shorter time to result
- **accuracy** — fewer errors
- **control** — more configurability / less black box
- **simplicity** — fewer steps, less learning
- **trust** — predictability, no surprises
- **status** — looks good, feels professional

### Axis 3 — Workaround (what they're doing instead)

- **competitor** — named a specific alternative
- **manual** — spreadsheets, docs, humans
- **abandoned** — stopped trying to solve
- **hybrid** — uses your thing + something else to compensate
- **unknown** — not stated

## Pattern convergence threshold

A single review is an anecdote, not a pattern. Before surfacing a cluster as a finding:

- **Minimum 3 reviews** must share the same pain × outcome combination.
- **Cross-source convergence:** if reviews come from multiple platforms (Google Maps, G2, App Store), the finding is stronger.
- **Recency weighting:** recent reviews (last 6 months) outweigh older ones when clusters conflict.

When a cluster has fewer than 3 reviews, mark it as `confidence: low` and flag it as an interview priority, not a conclusion.

## Unique-to-business filter

Generic category praise ("great customer service," "easy to use," "fast delivery") appears in reviews of every business in the category. These are table stakes, not differentiators.

Before including a cluster in the review brief:
- Ask: "Would this exact phrase appear in a competitor's 5-star review?"
- If yes: it's a hygiene factor. Note it but don't feature it.
- If no: it's a potential differentiator. Feature it prominently.

**Filter heuristic:** If 50%+ of businesses in the category would get the same praise, it's generic. Look for phrases that name specific products, people, processes, or experiences unique to this business.

This filter is especially important for review-mining mode — without it, you just get category platitudes dressed up as JTBD insights.

## Cluster labels (output)

Each cluster gets a label of the form:

```
[PAIN] users want [OUTCOME] but currently [WORKAROUND]
```

Examples:

- `time_cost — users want speed but currently manual`
- `trust_cost — users want accuracy but use competitor (Notion)`
- `cognitive_cost — users want simplicity but abandoned`

## Pre-seed output

`templates/review-brief.md` renders clusters as:

```markdown
## Top 3 clusters (ranked by volume)

### 1. [cluster label] — [N reviews, X% of total]
**Representative quotes:**
- "verbatim quote 1"
- "verbatim quote 2"
- "verbatim quote 3"
**Hypothesized job:** When [situation], I want to [motivation], so I can [outcome].
**Confidence:** high | medium | low

### 2. [cluster label]...
### 3. [cluster label]...

## Underserved forces
[List Switch forces that the reviews hint at but don't fully articulate — these become interview priorities.]

## Conflicts
[Cases where clusters contradict each other. These are rich interview territory.]
```

## When to trust clustering vs re-interview

- **Volume ≥ 30 reviews, consistent clusters:** skip Pass 1 questions already answered. Go straight to Switch forces pass + granularity gate.
- **Volume 15–30, mixed signals:** use clusters as hypotheses, run the full interview but skip one or two questions that the reviews already answered.
- **Volume < 15 or wildly inconsistent:** treat as anecdotes. Use for quote-mining only. Run the full interview.

## What reviews won't give you

- **Habit force.** Reviewers talk about their pain, rarely about their muscle memory. Interview this.
- **Anxiety force.** Only unhappy switchers leave reviews — happy stayers are invisible. Interview this.
- **Nuanced `cost_today`.** Reviews give surface symptoms. Dig for business impact in the interview.

## Opinionated default

Review mining is a pre-seed, not a replacement. The interview is still where the good stuff happens. If the user is trying to skip the interview entirely, redirect: "The reviews tell us the pain. They don't tell us who switches and why. Want to do a 10-minute interview with one real user?"
