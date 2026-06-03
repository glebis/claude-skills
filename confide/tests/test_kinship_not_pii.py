"""Precision guard: bare kinship/relationship terms are NOT PII and must be PRESERVED.

Redacting "мама/папа/брат/сестра" adds zero privacy (a role identifies no one) and
destroys the clinical utility of a therapy transcript. PII is the NAME/AGE/etc. that
ATTACHES to the role, not the role word. These are negative cases for the regex layer
and over-redaction guards for the pipeline. Synthetic data only.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

KIN_RU = ["мама", "мать", "папа", "отец", "брат", "сестра", "бабушка", "дедушка",
          "сын", "дочь", "жена", "муж", "родители", "тётя", "дядя"]
KIN_EN = ["mother", "mom", "father", "dad", "brother", "sister", "grandmother",
          "son", "daughter", "wife", "husband", "parents"]

def _types(t):
    return {s.type for s in C.detect_regex(t)}

def test_bare_kinship_ru_not_detected_as_pii():
    for w in KIN_RU:
        assert "PERSON" not in _types(f"я говорил про {w} вчера")
        assert _types(f"я говорил про {w} вчера") == set() or "AGE" not in _types(f"про {w}")

def test_bare_kinship_en_not_detected_as_pii():
    for w in KIN_EN:
        assert "PERSON" not in _types(f"I talked about my {w} yesterday")

def test_kinship_anchoring_a_name_keeps_role_redacts_nothing_in_regex():
    # regex layer doesn't do names; the role stays, no false AGE/DATE on "сестра Маша"
    t = "моя сестра Маша приехала"
    assert "AGE" not in _types(t) and "DATE" not in _types(t)

def test_age_on_relative_is_still_pii():
    # the ROLE is fine, but an age ATTACHED to it is PII and must be caught
    assert "AGE" in _types("маме 67 лет")
