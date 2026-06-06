#!/usr/bin/env python3
"""Evals for the rigorous-experiments skill.

Two uses:
  python3 evals/run_evals.py                      # run bundled eval cases
  python3 evals/run_evals.py <script.py> <results.json>   # lint real files

The linter checks the standards the skill enforces:
  L1 pre-registration present in the script docstring
  L2 BH called with an explicit fixed family size (m=...)
  L3 exact permutation used; sampled-permutation patterns flagged
  L4 results JSON has non-empty caveats
  L5 results tests carry p and n fields
  L6 privacy: no sentence-length quoted data outside prose keys
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

PROSE_KEYS = {"hypothesis", "method", "caveats", "desc", "description",
              "interpretation", "goal", "note", "verdict", "label",
              "approaches", "status"}


def lint_script(path):
    src = open(path, encoding="utf-8").read()
    findings = []
    try:
        tree = ast.parse(src)
        doc = ast.get_docstring(tree) or ""
    except SyntaxError as e:
        return [("L0", f"script does not parse: {e}")]
    prereg = re.search(r"pre-?registered", doc, re.I)
    if not prereg or re.search(r"not\s+pre-?registered", doc, re.I):
        findings.append(("L1", "no pre-registration block in module "
                               "docstring (write hypotheses/tests/m BEFORE "
                               "running)"))
    elif not re.search(r"\bm\s*=\s*\d|\bfamily\b", doc, re.I):
        findings.append(("L1b", "pre-registration block lacks a declared "
                                "family size (m=N)"))
    # L2: bh() must receive a CONSTANT m (AST), not len(tests)/variables
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and \
                getattr(node.func, "id", getattr(node.func, "attr", "")) \
                == "bh":
            mkw = next((k for k in node.keywords if k.arg == "m"), None)
            marg = (mkw.value if mkw else
                    node.args[1] if len(node.args) > 1 else None)
            if marg is None:
                findings.append(("L2", "bh() called without family size"))
            elif not isinstance(marg, ast.Constant):
                findings.append(("L2", "bh() family size is computed, not "
                                       "a declared constant (m=len(tests) "
                                       "defeats pre-registration)"))
    sampled = re.search(
        r"for\s+_?\w*\s+in\s+range\s*\(\s*(reps|2000|5000|1000)\b"
        r"[\s\S]{0,200}?np\.roll", src)
    if sampled:
        findings.append(("L3", "sampled circular-shift permutation "
                               "detected (range(reps)+np.roll): use exact "
                               "all-shifts enumeration"))
    if not re.search(r"exact_circ_p|exact_event_diff|break_diff"
                     r"|all\s+n-1 shifts|for\s+k\s+in\s+range\s*\(\s*1?\s*,"
                     r"\s*len", src):
        findings.append(("L3b", "no exact permutation machinery found "
                                "(import perm_stats or enumerate shifts)"))
    return findings


def _walk_strings(obj, keypath=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, keypath + (str(k).lower(),))
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v, keypath)
    elif isinstance(obj, str):
        yield keypath, obj


def lint_results(path):
    findings = []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [("R0", f"results JSON unreadable: {e}")]
    if not d.get("caveats"):
        findings.append(("L4", "results JSON has no caveats — every "
                               "experiment has known limitations; list "
                               "them"))
    tests = d.get("tests") or []
    if not tests and not d.get("descriptive_only"):
        findings.append(("L5", "no tests in results (set "
                               "descriptive_only: true if intentional)"))
    elif tests and not all("p" in t and "n" in t for t in tests):
        findings.append(("L5", "tests missing p/n fields"))
    for keypath, s in _walk_strings(d):
        if len(s) > 240 and s.count(" ") > 25 \
                and not (set(keypath) & PROSE_KEYS):
            findings.append(("L6", f"sentence-length string outside prose "
                                   f"keys at {'/'.join(keypath)}: possible "
                                   f"raw-text leak"))
            break
    return findings


def lint(script, results):
    return lint_script(script) + lint_results(results)


def run_cases():
    here = os.path.dirname(os.path.abspath(__file__))
    cases = json.load(open(os.path.join(here, "cases", "cases.json"),
                           encoding="utf-8"))
    failures = 0
    for c in cases:
        f = lint(os.path.join(here, "cases", c["script"]),
                 os.path.join(here, "cases", c["results"]))
        got = sorted({code for code, _ in f})
        want = sorted(c["expect_codes"])
        ok = got == want
        print(f"  {'PASS' if ok else 'FAIL'} {c['name']}: "
              f"expected {want}, got {got}")
        if not ok:
            failures += 1
    print(f"{len(cases) - failures}/{len(cases)} eval cases pass")
    return failures


if __name__ == "__main__":
    if len(sys.argv) == 3:
        fs = lint(sys.argv[1], sys.argv[2])
        for code, msg in fs:
            print(f"  {code}: {msg}")
        print("CLEAN" if not fs else f"{len(fs)} findings")
        sys.exit(1 if fs else 0)
    sys.exit(1 if run_cases() else 0)
