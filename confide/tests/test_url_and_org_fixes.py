"""TDD: (1) URL regex must catch bare domains (no scheme); (2) NER scaffolding filter
must drop transcript-structure false positives like 'Speaker 1\\n\\nToday' from ORG."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

def _urls(t):
    return [s.text for s in C.detect_regex(t) if s.type == "URL"]

def test_bare_domain_url():
    assert any("example.ru" in u for u in _urls("профиль example.ru тут"))
    assert any("t.me" in u for u in _urls("пиши в t.me/handle"))

def test_scheme_url_still_works():
    assert any("https://x.io" in u for u in _urls("see https://x.io/page now"))

def test_bare_domain_not_false_on_russian_abbrev():
    # Cyrillic abbreviations like "т.е." / "и т.д." must NOT be URLs
    assert _urls("ну т.е. и т.д. понятно") == []

def test_bare_domain_not_false_on_decimal():
    assert _urls("это 2.5 метра") == []

def test_ner_scaffolding_filter_drops_newline_spans():
    spans = [
        C.Span(0, 18, "Speaker 1\n\nToday", "ORG", "natasha"),
        C.Span(40, 46, "Берлин", "LOCATION", "natasha"),
        C.Span(50, 56, "user\n\n", "ORG", "natasha"),
    ]
    kept = C.filter_ner_scaffolding(spans)
    texts = {s.text for s in kept}
    assert "Берлин" in texts
    assert not any("\n" in s.text for s in kept)          # newline spans dropped
    assert not any(s.text.strip().lower() in {"user", "speaker 1"} for s in kept)
