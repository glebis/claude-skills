# Mode: validate-data

Gate every new data source through this checklist BEFORE designing
against it. Each item is a bug class that actually occurred and silently
corrupted results until caught.

## The checklist

1. **Zero vs missing.** A day with zero marker hits is a real 0.0 rate,
   not a missing day. Dict comprehensions over hit-counters silently drop
   zero-keys (n collapsed from 234 to 35 once). Initialize all expected
   keys explicitly.
1b. **Degenerate units / leverage points.** A unit with a near-zero
   denominator (empty/failed transcript, 1-token session) makes every
   per-1k or ratio read exactly 0 — and then sits at a corner of every
   scatter as a maximum-leverage point that can carry a whole
   correlation. One n_tokens=1 session inflated a headline lag from
   r=−0.32 (n.s.) to r=−0.64 (p=0.03); removing it collapsed the
   "central finding." Filter units below a sane size threshold BEFORE any
   per-unit analysis, and eyeball the scatter for single points pinned to
   an axis. Also: a "size" variable that does not vary in reality (e.g.
   transcript length when all sessions are a fixed 60 min — it measures
   recording completeness, not dose) must NOT be used as a covariate or
   alternative mechanism. Confirm a variable is real before controlling
   for it.
2. **Dedup semantics.** Know what one row means. A UNIQUE(url, device)
   constraint makes "visits/day" actually "NEW unique URLs/day" —
   revisits invisible. Rename the measure accordingly.
3. **Category matching.** Substring rules over identifiers are
   booby-trapped: `"code"` matched `ru.keepcoder.Telegram` and silently
   reclassified 1,094 human messages as coding (audience analysis ran on
   n=8 until a review caught it). Match on specific tokens; order rules
   by specificity; verify per-category counts against raw counts.
4. **Timezone & day boundaries.** Establish the storage convention
   (UTC? local-at-write? offset column with JS sign convention
   local=utc−offset?) and the DST behavior of fallbacks before computing
   hour-of-day or day-boundary features.
5. **Retention windows.** Check how long the source keeps data (a
   dictation app kept audio only ~2 weeks — rolling purge). If data
   expires, build the harvester FIRST, analysis later.
6. **Coverage map per field.** Fields appear/disappear with app versions
   (speechDuration on 102/379 days; corrections on 49). Print per-field
   monthly coverage before designing tests on them.
7. **Format/granularity strata.** Mixed export formats (merged turns vs
   utterance-level) make raw counts incomparable — z-score within format
   or analyze within stratum.
8. **Cache invalidation.** Caches keyed by age go stale wrong; key them
   by source mtime + schema version + date window. Thread `--refresh`
   through every consumer.
9. **Silent exclusions.** Count and report every dropped row by reason
   (bad timestamp, empty text, short clip). "Processed 0 entries" looked
   like success in a sync log for six months.
10. **Instrumentation breaks vs life breaks.** Before interpreting a
    regime change, check for device non-wear, app switches, schema
    changes, sync outages at the same date. A channel whose "break"
    coincides with an instrumentation change is flagged, not interpreted.
11. **Identifier drift.** Hostnames, spellings of names, app bundle ids
    drift over time (mDNS rename broke a sync silently; a coach's name
    had three spellings). Match leniently, log what matched.
12. **Missingness mechanism.** Test whether missingness itself tracks
    time, outcomes or predictors (missing-not-at-random): correlate the
    observed/missing indicator with the key series. If days are missing
    *because* of the state being studied (e.g. no dictation on bad days),
    complete-case correlations are biased — report the sensitivity.
13. **Positive control.** Find one event the source MUST see (a
    documented move, a vacation). If it can't detect that, its nulls are
    void.

## Validation output

A short validation memo: rows, window, per-field coverage, dedup
semantics, timezone convention, retention, known strata, exclusion
counts, positive-control result, and the list of measures that are SAFE
to design against.
