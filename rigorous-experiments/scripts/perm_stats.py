#!/usr/bin/env python3
"""Shared exact permutation statistics for time-series experiments.

Calendar-aligned series with None gaps; EXACT circular-shift permutation
(all N-1 shifts of the full calendar, joint missingness mask re-applied
per shift) — two hard-won lessons: sampled permutation under-estimates
p on small n, and shifting a gap-compressed series breaks the timeline.
"""

from __future__ import annotations

import numpy as np


def masked_r(x, y):
    """Pearson r over jointly observed entries of two float arrays w/ NaN."""
    m = ~(np.isnan(x) | np.isnan(y))
    n = int(m.sum())
    if n < 8:
        return None, n
    xs, ys = x[m], y[m]
    if xs.std() == 0 or ys.std() == 0:
        return None, n
    return float(np.corrcoef(xs, ys)[0, 1]), n


def to_arr(series):
    return np.array([np.nan if v is None else v for v in series], float)


def exact_circ_p(x, y):
    """r + exact circular-shift permutation p over full calendar series."""
    x, y = to_arr(x), to_arr(y)
    r_obs, n = masked_r(x, y)
    if r_obs is None:
        return None, None, n
    count, total = 0, 0
    for k in range(1, len(y)):
        r, _ = masked_r(x, np.roll(y, k))
        if r is None:
            continue
        total += 1
        if abs(r) >= abs(r_obs) - 1e-12:
            count += 1
    # guard: a tiny shift universe cannot produce a meaningful p.
    # 12 keeps short session sequences (n=13..20, resolution 1/13..1/20)
    # testable while refusing degenerate universes; prior results with
    # universes >=20 are unaffected.
    if total < 12:
        return r_obs, None, n
    return r_obs, (count + 1) / (total + 1), n


def exact_event_diff(indicator, values, step=1):
    """Mean(values | indicator==1) - mean(values | indicator==0), in SD
    units, with exact circular-shift permutation of the indicator.

    indicator must be a PURE 0/1 list over the full calendar (no None) —
    missingness lives only in `values`, so shifting the indicator moves
    event labels without changing the observation sample (audit fix:
    None-carrying indicators leaked missingness into placebo samples).
    step=7 restricts placebo shifts to weekday-preserving offsets.
    """
    ind = np.asarray(indicator, float)
    assert not np.isnan(ind).any(), "indicator must be 0/1 with no gaps"
    val = to_arr(values)
    obs_mask = ~np.isnan(val)

    def diff(i):
        a = val[obs_mask & (i == 1)]
        b = val[obs_mask & (i == 0)]
        if len(a) < 5 or len(b) < 5:
            return None, len(a)
        sd = val[obs_mask].std() or 1.0
        return float((a.mean() - b.mean()) / sd), len(a)

    d_obs, n1 = diff(ind)
    if d_obs is None:
        return None, None, n1
    count, total = 0, 0
    for k in range(step, len(ind), step):
        d, _ = diff(np.roll(ind, k))
        if d is None:
            continue
        total += 1
        if abs(d) >= abs(d_obs) - 1e-12:
            count += 1
    if total < 20:
        return d_obs, None, n1
    return d_obs, (count + 1) / (total + 1), n1


def break_diff(values, cut_idx, min_side=30):
    """Mean(after cut) - mean(before cut) in SD units, with placebo
    distribution from ALL non-wrapping cut points having >= min_side
    observed days on each side (audit fix: circularly rolled break
    indicators wrap around the calendar and are not valid cutpoints)."""
    val = to_arr(values)
    obs = ~np.isnan(val)
    sd = val[obs].std() or 1.0

    def diff(c):
        a = val[:c][obs[:c]]
        b = val[c:][obs[c:]]
        if len(a) < min_side or len(b) < min_side:
            return None
        return float((b.mean() - a.mean()) / sd)

    d_obs = diff(cut_idx)
    if d_obs is None:
        return None, None, 0
    placebo = [diff(c) for c in range(len(val))]
    placebo = [d for d in placebo if d is not None]
    if len(placebo) < 20:
        return d_obs, None, len(placebo)
    count = sum(1 for d in placebo if abs(d) >= abs(d_obs) - 1e-12)
    return d_obs, count / len(placebo), len(placebo)


def bh(tests, m):
    """Benjamini-Hochberg with fixed family size m; adds 'q' in place.

    q is stored at FULL precision (round only for display). m must be at
    least the number of valid tests — a smaller m is anti-conservative.
    Note: plain BH controls FDR under independence/PRDS; for strongly
    dependent families use BH-Yekutieli or a maxT resampling scheme.
    """
    valid = [t for t in tests if t.get("p") is not None]
    if m < len(valid):
        raise ValueError(f"family size m={m} < {len(valid)} valid tests "
                         "(anti-conservative); declare the true family")
    qs = {}
    for rank, t in enumerate(sorted(valid, key=lambda t: t["p"]), 1):
        qs[id(t)] = min(1.0, t["p"] * m / rank)
    prev = 1.0
    for t in sorted(valid, key=lambda t: -t["p"]):
        prev = min(prev, qs[id(t)])
        t["q"] = prev
