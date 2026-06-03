#!/usr/bin/env python3
"""End-to-end eval: confide:anon → confide:red pipeline on a synthetic fixture.

Offline (regex layer only — no models/network). Proves the skills compose:
anonymize removes direct identifiers, and the residual-risk check confirms it
(and correctly flags the UN-redacted control as HIGH risk). Synthetic data only.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "shared"))
sys.path.insert(0, os.path.join(HERE, "..", "skills", "red", "scripts"))
import confide_core as core
import red

CFG = dict(core.DEFAULTS); CFG["layers"] = ["regex"]   # deterministic, offline

FIXTURE = ("Клиент написал на a.k@example.ru и позвонил +7-916-555-21-43. "
           "Профиль: https://example.com/u/marina . Встреча была 05.02.2026.")

def run():
    fails = []
    # 1) anonymize
    out = core.anonymize(FIXTURE, CFG)
    green = out["redacted_text"]
    for leak in ["a.k@example.ru", "+7-916-555-21-43", "https://example.com/u/marina"]:
        if leak in green:
            fails.append(f"anon left a direct identifier in GREEN: {leak[:6]}…")
    if "[EMAIL]" not in green:
        fails.append("anon produced no typed placeholder")

    # 2) red on the GREEN (redacted) output — should find ~no surviving DIRECT identifiers
    so_green = red.singling_out(green, CFG)
    direct = {"EMAIL", "PHONE", "URL", "ID", "PERSON"}
    surviving_direct = sum(v for t, v in so_green["by_type"].items() if t in direct)
    if surviving_direct != 0:
        fails.append(f"red found {surviving_direct} surviving DIRECT identifiers in GREEN (anon leaked)")
    tier_green = red.risk_tier(so_green)
    if tier_green == "HIGH":
        fails.append(f"GREEN risk tier should not be HIGH, got {tier_green}")

    # 3) negative control: red on the ORIGINAL must flag HIGH (the check actually discriminates)
    so_orig = red.singling_out(FIXTURE, CFG)
    tier_orig = red.risk_tier(so_orig)
    if tier_orig != "HIGH":
        fails.append(f"red on un-redacted control should be HIGH, got {tier_orig}")

    print(f"[eval] anon→green: direct identifiers surviving = {surviving_direct} (want 0), tier={tier_green}")
    print(f"[eval] control (raw): tier={tier_orig} (want HIGH), surviving by_type={so_orig['by_type']}")
    if fails:
        print("FAIL:"); [print("  -", f) for f in fails]; return 1
    print("PASS ✓ anon removes direct identifiers; red confirms green is not HIGH and flags raw as HIGH")
    return 0

if __name__ == "__main__":
    sys.exit(run())
