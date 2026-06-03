"""Offline-deterministic tests for confide:red residual re-identification RISK CHECK.

singling-out and linkability are deterministic (regex/Natasha on the REDACTED text).
The LLM inference probe is NOT exercised here (network/model) — it is mocked/skipped.
All fixtures are SYNTHETIC. No real PII. No re-identification recipe is produced.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "red", "scripts"))
import red as R  # noqa: E402


# ---- fixtures (synthetic) -------------------------------------------------
UNDER_REDACTED = (
    "Session with [PERSON]. Reach me at contact@example.org or call "
    "+7-916-555-21-43 to reschedule [DATE]."
)
WELL_REDACTED = (
    "Session with [PERSON] in [LOCATION]. Contact [EMAIL] or [PHONE]; "
    "next meeting [DATE]. Works as [PROFESSION]."
)


# ---- singling-out (surviving direct identifiers => HIGH) ------------------
def test_singling_out_flags_surviving_email_and_phone():
    findings = R.singling_out(UNDER_REDACTED, R.cfg())
    by_type = findings["by_type"]
    assert by_type.get("EMAIL", 0) >= 1
    assert by_type.get("PHONE", 0) >= 1
    assert R.risk_tier(findings) == "HIGH"


def test_well_redacted_has_zero_surviving_identifiers():
    findings = R.singling_out(WELL_REDACTED, R.cfg())
    assert findings["total"] == 0
    assert R.risk_tier(findings) == "LOW"


# ---- risk-tier rule -------------------------------------------------------
def test_risk_tier_direct_is_high():
    assert R.risk_tier({"by_type": {"EMAIL": 1}, "total": 1}) == "HIGH"


def test_risk_tier_quasi_only_is_medium():
    assert R.risk_tier({"by_type": {"DATE": 2, "LOCATION": 1}, "total": 3}) == "MEDIUM"


def test_risk_tier_none_is_low():
    assert R.risk_tier({"by_type": {}, "total": 0}) == "LOW"


def test_risk_tier_direct_beats_quasi():
    assert R.risk_tier({"by_type": {"PHONE": 1, "DATE": 5}, "total": 6}) == "HIGH"


# ---- linkability (shared surviving quasi-identifier => linkable pair) -----
def test_linkability_flags_shared_quasi_identifier():
    a = "Met [PERSON] on 15.01.2026 in the clinic."   # surviving DATE 15.01.2026
    b = "[PERSON] returned, follow-up booked 15.01.2026."  # same surviving DATE
    pairs = R.linkability({"a.md": a, "b.md": b})
    assert len(pairs) == 1
    assert {"a.md", "b.md"} == set(pairs[0]["files"])


def test_linkability_no_shared_identifier_no_pairs():
    a = "Met [PERSON] on 15.01.2026."
    b = "Email leak2@example.org survived here."
    pairs = R.linkability({"a.md": a, "b.md": b})
    assert pairs == []


# ---- report shape: categories/counts only, with caveat -------------------
def test_report_is_counts_and_categories_only():
    rep = R.assess_text(UNDER_REDACTED, R.cfg(), inference=False)
    assert rep["risk_tier"] == "HIGH"
    assert rep["surviving"]["by_type"].get("EMAIL", 0) >= 1
    # caveat present: absence of a finding is not a safety guarantee
    assert "caveat" in rep and "not" in rep["caveat"].lower()
    # no inference recipe / no raw attribute VALUES when probe disabled
    assert rep["inference"]["ran"] is False
