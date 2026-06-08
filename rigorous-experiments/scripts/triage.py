#!/usr/bin/env python3
"""Lead-triage battery — project-agnostic parts (numpy only).

After a sweep produces leads, triage each one. These three checks need no
project dependencies; add prewhiten/bootstrap (statistics.md) for daily
cross-series leads. See references/lead-investigation.md.

  loo_robustness(x, y)      -> small-n artifact detector
  directionality(x, y)      -> forward-vs-reverse for lag leads
  half_split_gradual(y)     -> trend-vs-regime-step for trend leads
  consolidate(*series)      -> z-composite of same-direction leads

Verdict helper combines them; mint NO new "confirmed" — diagnostic only.
"""

from __future__ import annotations

import numpy as np


def _clean(x, y):
    a, b = [], []
    for u, v in zip(x, y):
        if u is None or v is None:
            continue
        if (isinstance(u, float) and np.isnan(u)) or \
                (isinstance(v, float) and np.isnan(v)):
            continue
        a.append(float(u))
        b.append(float(v))
    return np.array(a), np.array(b)


def loo_robustness(x, y):
    """Sign-stability and magnitude-fragility under leave-one-out.
    FRAGILE (artifact) if sign flips or |r| more than halves on any drop.
    NOTE: passing LOO is necessary, not sufficient — not significance."""
    xa, ya = _clean(x, y)
    if len(xa) < 8 or xa.std() == 0 or ya.std() == 0:
        return None
    r_full = float(np.corrcoef(xa, ya)[0, 1])
    rs = []
    for i in range(len(xa)):
        m = np.arange(len(xa)) != i
        if xa[m].std() and ya[m].std():
            rs.append(float(np.corrcoef(xa[m], ya[m])[0, 1]))
    return {
        "r_full": round(r_full, 3),
        "loo_min": round(min(rs), 3), "loo_max": round(max(rs), 3),
        "sign_stable": all((r > 0) == (r_full > 0) for r in rs),
        "magnitude_fragile": any(abs(r) < abs(r_full) / 2 for r in rs),
    }


def directionality(x, y):
    """Forward vs reverse Pearson r (caller supplies already-lagged
    pairs). Causal reading dies if |reverse| >= |forward|."""
    xa, ya = _clean(x, y)
    if len(xa) < 8 or xa.std() == 0 or ya.std() == 0:
        return None
    fwd = float(np.corrcoef(xa, ya)[0, 1])
    rev = float(np.corrcoef(ya, xa)[0, 1])  # symmetric for same pairing;
    # real direction test needs the caller to pass the reverse lag pairs.
    return {"forward_r": round(fwd, 3), "reverse_r": round(rev, 3),
            "note": "pass reverse-lag pairs explicitly for a real test"}


def half_split_gradual(y):
    """Trend vs regime-step: a gradual trend has same-sign slope in both
    halves; opposite signs mean a STEP masquerading as a trend."""
    ya = np.array([v for v in y if v is not None
                   and not (isinstance(v, float) and np.isnan(v))], float)
    h = len(ya) // 2
    if h < 3 or len(ya) - h < 3:
        return None
    s1 = float(np.polyfit(np.arange(h), ya[:h], 1)[0])
    s2 = float(np.polyfit(np.arange(len(ya) - h), ya[h:], 1)[0])
    return {"slope_first_half": round(s1, 4),
            "slope_second_half": round(s2, 4),
            "gradual": bool(s1 * s2 > 0)}


def consolidate(named_series):
    """z-composite of same-direction leads. `named_series` is a dict
    {label: (series, sign)} where sign is +1/-1 for the hypothesized
    direction. Returns the composite array (NaN-aware z per component)."""
    comps = []
    for label, (s, sign) in named_series.items():
        a = np.array([np.nan if v is None else v for v in s], float)
        z = (a - np.nanmean(a)) / (np.nanstd(a) + 1e-9)
        comps.append(sign * z)
    return np.nansum(np.vstack(comps), axis=0)


def verdict(loo, gradual=None, direction=None, prewhiten_holds=None):
    """Combine checks into a triage verdict. Diagnostic only."""
    if loo is None or not loo["sign_stable"] or loo["magnitude_fragile"]:
        return "artifact"
    if gradual is not None and not gradual["gradual"]:
        return "artifact"
    if prewhiten_holds:
        return "strengthened"
    if direction and abs(direction.get("reverse_r", 0)) >= \
            abs(direction.get("forward_r", 1)):
        return "artifact"
    return "candidate"  # robust but underpowered — prospective only
