# Mode: conduct (+ §Audit)

Implement with `scripts/perm_stats.py` (battle-tested; copy into the
project). API: `exact_circ_p(x, y)` — Pearson r with exact circular-shift
permutation over full-calendar series with None gaps (rolls y; pass the
COMPLETE series as y so missingness stays attached to its own series);
`exact_event_diff(indicator, values, step=1)` — SD-unit event contrast,
indicator strictly 0/1 (assert enforced), `step=7` preserves weekday
structure; `break_diff(values, cut_idx, min_side=30)` — level step at a
known date vs ALL non-wrapping placebo cuts; `bh(tests, m)` — BH with
fixed family size.

## Permutation correctness checklist

- Universe size: session sequence n → n−1 shifts → min p = 1/n. If the
  guard returns p=None (universe <12), the test is unpowered — report it
  as such, never substitute a sampled test.
- Daily series: build the CONTIGUOUS calendar from first to last day;
  gaps as None. d+1 must mean the next calendar day, not the next row.
- Break tests: circularly rolled "before/after" indicators wrap around
  the calendar and are invalid cutpoints — enumerate non-wrapping cuts.
- Event studies near weekly-structured events: placebo shifts in
  multiples of 7.
- Residualize-then-permute is a Freedman–Lane approximation
  (anti-conservative). Acceptable when the conclusion is a null
  (a fortiori); for positive claims refit per permutation.
- Sign-flip permutation for paired within-unit contrasts is fine sampled
  (5000) at n≥100; the exactness rule binds at small n.

## Beyond circular shifts (trending/structured series)

- Prewhiten (AR1 residuals) and stationary bootstrap alongside exact
  perm for any cross-series claim; report all three. A claim that dies
  under prewhitening was a shared trend.
- Stratify by group and regime before pooling (Simpson). Run within-kind
  and within-regime; pool only if signs agree.
- Granger/lead-lag on differenced series, not levels.

## Results JSON conventions

`{experiment, hypothesis, method, n_*, tests: [{h, desc, r, p, q, n}],
caveats: [...]}` — statistics only, no raw text. For every effect that
will be DEFENDED (confirmed/lead), include an uncertainty interval
(bootstrap or permutation CI), not just p. Round for display but
keep BH on full precision when families are large. Always include the
caveats list; every known limitation goes in.

## §Audit (re-examining past claims)

1. Build/refresh a findings registry: every test as
   `{exp, family, id, effect, p, q, n, status}` with statuses:
   confirmed / lead / null / descriptive.
2. **Impossible-p detector**: for sampled-permutation session tests,
   reported p < 1/n is unattainable exactly → flag and recompute.
3. Recompute exactly from stored per-unit data where possible; BH with
   the ORIGINAL family size; record status flips with provenance
   (`status_original`, `audited` fields) — never silently edit.
4. When a control collapses an effect, decompose: re-run with each
   control alone, then check r(predictor, killing control). High
   collinearity → "mechanism ambiguous", not "artifact".
5. External recomputation (another model/person, aggregate data only) is
   the strongest audit — it found what three internal reviews missed.
