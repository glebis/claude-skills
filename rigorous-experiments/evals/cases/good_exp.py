"""Demo experiment.

PRE-REGISTERED (m=2): T1 x<->y same day; T2 x->y next day.
Exact circular permutation over the full calendar; BH m=2.
"""
from perm_stats import bh, exact_circ_p

def main(x, y):
    tests = []
    r, p, n = exact_circ_p(x, y)
    tests.append({"h": "T1", "r": r, "p": p, "n": n})
    r, p, n = exact_circ_p(x, y[1:] + [None])
    tests.append({"h": "T2", "r": r, "p": p, "n": n})
    bh(tests, m=2)
    return tests
