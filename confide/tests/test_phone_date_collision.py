"""TDD: numeric dates (15.01.2026) must classify as DATE, not PHONE. The phone regex's
char class includes '.', so it also matches dotted dates; PHONE must yield to DATE."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

def _types(t):
    return [s.type for s in C.detect_regex(t)]

def test_numeric_date_is_date_not_phone():
    for d in ["15.01.2026", "05.02.2026", "1.2.26", "31.12.2025"]:
        ts = _types(d)
        assert "DATE" in ts, f"{d}: expected DATE, got {ts}"
        assert "PHONE" not in ts, f"{d}: should not be PHONE, got {ts}"

def test_merged_date_label_wins():
    # after merge, the single span for a numeric date is typed DATE
    spans = C.merge_spans(C.detect_regex("встреча 05.02.2026 в офисе"))
    date_spans = [s for s in spans if "05.02.2026" in s.text]
    assert date_spans and date_spans[0].type == "DATE"

def test_real_phone_still_phone():
    assert "PHONE" in _types("звони +7-916-555-21-43")
    assert "PHONE" in _types("тел 8 (916) 555 21 43")

def test_slash_date_also_date():
    assert "DATE" in _types("15/01/2026") and "PHONE" not in _types("15/01/2026")
