# Mode: design

Produce a pre-registered experiment plan BEFORE any data contact beyond
coverage checks.

## Output of this mode

A docstring-ready block containing:

1. **Hypothesis** — directional, mechanism-flavored, falsifiable. State
   what a positive AND a null would mean (if a null teaches nothing,
   redesign).
2. **Tests** — exact list, each with: predictor, outcome, lag structure,
   test statistic, permutation scheme. 5–10 tests max per family.
3. **Family size m** — fixed now. Confirmatory family (1–5 tests, things
   to be believed) separate from exploratory family (the sweep).
4. **Thresholds** — confirmatory: exact q<0.10; lead: exact p<0.06.
5. **Power sanity** — n available; smallest detectable r at 80% power
   (~0.21 at n=180, ~0.15 at n=365 for daily series — iid two-sided
   α=0.05 approximations; autocorrelation, missingness and multiplicity
   all reduce effective power below these). For session sequences of
   n≈20–30 only |r|>0.5 is detectable and permutation resolution is 1/n
   — say so.
6. **Positive control where possible** — one test that MUST fire if the
   instrument works (e.g. "apartment-browsing share must change around a
   documented move"). If the positive control fails, nulls are
   uninterpretable.
7. **Negative controls / placebo outcomes** — one outcome the predictor
   must NOT move (and/or placebo dates). A predictor that "works" on the
   negative control is measuring confounding or instrumentation, not the
   mechanism.

## Design heuristics (earned the hard way)

- **Three methods beat one**: session-level correlation, within-unit
  event study, and multivariate prediction answer different questions and
  fail differently. An event study over thousands of within-unit events
  has real power when n_sessions=20 does not.
- **Lagged designs**: pair adjacent-by-date units; record gap length as a
  covariate. "t → t+1" over irregular spacing weakens interpretation.
- **Name the collider up front**: volume/usage of a channel usually
  correlates with workload and with the markers computed from it.
- **Anticipation matters for life events**: plannable events (moves, job
  changes) show preparation signatures months before the date — design
  windows around the *preparation period*, not just the event date.
- **Prospective protocols**: one primary predictor, one primary outcome,
  test ONCE at a pre-committed n; include a kill/decision rule and an
  adherence criterion for interventions. Randomize from a recorded seed
  and paste the literal generated schedule into the protocol.
- **Audience/register strata**: text markers differ by who the text is
  for (AI vs humans vs self). If the corpus mixes registers, plan a
  stratified or within-day paired contrast.
