# Goal Contract — <feature name>

> Source of truth. Agents may propose **Goal Amendments**; they may not silently rewrite this.
> Keep it short — caps below. A capped goal stays a goal, not waterfall-in-markdown.
> The **core** section is enough for M features. Fill the **conditional** section only for L, or when a size/risk trigger fires (`references/process-budget.md`).

## Core

### Current state (≤3)
-

### Desired future state (≤3)
-

### Desired outcomes (solution-independent, measurable; ≤5)
-

### Smallest shippable slice   <!-- required -->
<what ships first without building the whole cathedral>

### Stop condition   <!-- required -->
<"if X, stop and ask for human approval / re-scope">

### Success evidence (≤5)
<tests / verify / behavioral / visual — each outcome must map to evidence>

### Risk classification
<R0 none · R1 internal dev-assist · R2 user-facing low-stakes · R3 sensitive data/recommendations/profiling · R4 prohibited/high-risk → STOP>
EU AI Act (or jurisdiction equivalent): Art 5 prohibited use? <no/N/A> · Art 50 labelling? <no/N/A>

### Tracker
<bd | linear | none — the issue tracker for this feature; `none` unless it genuinely decomposes into >1 tracked task. No second ledger.>

## Conditional — fill only for L or when a trigger fires

### Current constraint (Theory of Constraints)
<the one bottleneck this feature attacks>

### Target user / job (JTBD)
<who, and what job they're hiring this for>

### Non-negotiable constraints (≤5)
-

### Visual checkpoints
<only if user-visible UI layout/styling/onboarding/auth/safety changes; else "N/A">

### Rollback note
<revert commit / feature flag / config toggle / N-A — required for L per process-budget>

### Risks (≤5)
-

### Non-goals (≤5)
-

### Release constraints
-

---
**Fail rule:** if a goal can't produce evidence, it's a wish with better formatting — it doesn't pass.
