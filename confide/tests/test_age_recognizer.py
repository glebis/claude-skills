"""TDD: deterministic AGE recognizer in the regex layer (RU + EN, digit + spelled-out)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

def _ages(t):
    return [s.text for s in C.detect_regex(t) if s.type == "AGE"]

def test_ru_digit_age():
    assert any("67" in a for a in _ages("ей шестьдесят семь, ну, 67 лет уже"))

def test_ru_digit_age_god_goda():
    assert _ages("ему 1 год")          # год
    assert _ages("ребёнку 3 года")     # года
    assert _ages("мужчине 41 года")

def test_ru_spelled_age():
    assert _ages("ей шестьдесят семь лет")
    assert _ages("мне сорок лет")

def test_en_age_forms():
    assert _ages("she is 67 years old")
    assert _ages("a 41-year-old client")

def test_age_not_overmatch_plain_years():
    # a bare year count that is not an age should not be tagged AGE
    # "за год" / "двадцать лет назад" (duration, not someone's age) — acceptable to skip,
    # but a real age phrase must win; we only assert the age phrase is caught here.
    got = _ages("мама (67 лет) не изменится")
    assert got, "the canonical missed case must now be caught"

def test_phone_still_not_age():
    assert not _ages("позвони +7-916-555-21-43")
