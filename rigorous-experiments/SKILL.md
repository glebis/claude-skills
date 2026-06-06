---
name: rigorous-experiments
description: This skill should be used when designing, running, validating, or auditing statistical experiments on personal or observational time-series data (health metrics, speech/text corpora, behavioral logs, diaries, n-of-1 self-tracking). It enforces pre-registration, exact permutation tests, FDR discipline, data-validation gates, adversarial code review, and cross-validation with external models. Triggers on "design an experiment", "test this hypothesis on my data", "is this correlation real", "audit these findings", "pre-register", "validate this dataset", or any n-of-1 / quantified-self analysis request.
---

# Rigorous Experiments

Run statistical experiments on observational/personal time-series data that
survive scrutiny. Distilled from a 54-experiment n-of-1 program in which
sampled permutation tests, missing-data artifacts, app-categorization bugs
and collinear mechanisms repeatedly manufactured — and then destroyed —
"findings". Every rule here exists because its absence once produced a
wrong conclusion.

## Modes

Pick the mode matching the request; chain them for a full study.

| Mode | When | Reference |
|------|------|-----------|
| **design** | New hypothesis or study | `references/design.md` |
| **conduct** | Implementing + running the experiment | `references/statistics.md` |
| **validate-data** | Before trusting ANY new data source | `references/data-validation.md` |
| **cross-validate** | Findings worth defending; code review; external model review (e.g. GPT Pro) | `references/cross-validation.md` |
| **audit** | Re-examining past claims, registries of findings | `references/statistics.md` §Audit |

## Non-negotiable core (all modes)

1. **Pre-register before computing.** Hypotheses, exact tests, family size
   m, and the acceptance threshold go in the script docstring BEFORE the
   first run. Post-hoc tests are reported as descriptive, never promoted.
2. **Exact permutation, never sampled, on small n.** A session sequence of
   n=19 has 18 circular shifts: the minimum honest p is ~1/19≈0.05.
   Sampling 2000 shifts with replacement fabricates precision (this killed
   a flagship "q=0.028" finding). Use `scripts/perm_stats.py`.
3. **Permute over the full calendar, not the compressed series.** Shifting
   a gap-compressed series breaks the timeline; keep missingness as NaN
   masks re-applied per shift. Event indicators must be pure 0/1 with no
   gaps — missingness lives only in the outcome series.
4. **BH with FIXED family size m**, declared at design time. Confirmatory
   families small and separate from exploratory sweeps; pooling everything
   into one BH buries true effects, cherry-picking families manufactures
   them. Plain BH assumes independent/positively-dependent tests; for
   strongly dependent lag families use BH-Yekutieli or maxT resampling.
5. **Stationarity check before correlating trending series.** Exact
   circular shift on a trending series is "exactly, reproducibly wrong":
   report prewhitened-r (AR1 residuals) and stationary bootstrap alongside.
6. **Stratify before pooling** (Simpson check): within group (e.g.
   therapy/coaching) and within regime (pre/post known breaks). A pooled
   r=−0.25 once hid therapy −0.64 vs coaching +0.53.
7. **Controls can re-describe a finding, not just kill it.** When a control
   collapses an effect, check collinearity of control and predictor —
   r(self-focus, session-length)=0.79 meant "mechanism ambiguous", not
   "effect fake". Report the decomposition.
8. **Honest statuses**: confirmed (q<0.10 exact) ≠ lead (p<0.06) ≠ null ≠
   descriptive. Status flips are recorded, never silently edited. Nulls
   with adequate power are findings.
9. **Privacy**: raw text/audio never enters output files or external
   uploads — statistics, rates and embedding-derived scores only.
10. **Plain-language reporting**: every statistic carries its practical
    meaning inline; define r/p/q/n once per report; no untranslated jargon
    calques. Narrative first, numbers as support.

## Workflow (full study)

1. `validate-data` gate on any new source (see reference — the checklist
   has caught: zero-vs-missing conflation, dedup semantics, substring
   category bugs, rolling purge windows, timezone conventions).
2. `design`: pre-registered hypotheses + family + power sanity.
3. `conduct`: implement with `scripts/perm_stats.py`; run; write results
   JSON with tests, statuses, and caveats including known limitations.
4. `cross-validate`: adversarial code review (e.g. Codex read-only) BEFORE
   trusting results; fix findings; re-run. For major claims, external
   model review with a privacy-screened archive.
5. Verdicts in honest prose (mixed/rejected allowed); report; registry
   update with status provenance.

## Viewing results

Launch the bundled explorer over any directory of results JSONs:

```bash
python3 scripts/explorer.py <results_dir> [--port 8799] [--pattern "exp*.json"] [--sort newest|oldest]
```

Generates `explorer.html` in the directory, starts (or reuses) a loopback
http server on the port, and opens the browser: experiment list with
confirmed/lead badges, filter, sortable test tables color-coded by
status, verdicts, caveats, raw JSON. The page fetches result files live —
re-running experiments updates the view; re-run the script only when new
result files appear. Serve over localhost, never file:// (CDN fonts) and
never on a non-loopback interface (results may contain personal
statistics).

## Evals

Run `python3 evals/run_evals.py` (from the skill directory) to lint an
experiment script/results pair against the standards (pre-registration
present, fixed m, exact perm usage, caveats, no raw text in outputs).
Eval cases in `evals/cases/` document expected pass/fail examples.
