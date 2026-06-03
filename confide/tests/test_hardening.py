"""Codex-review hardening tests — all OFFLINE / deterministic.

Cover the reserved-sentinel placeholder grammar and its safety properties:
- collision: a source already containing the sentinel is not corrupted by anon,
- over-match negatives: ordinary prose ("Person 1", "patient 1", "section 2") is
  never touched by rehydrate,
- cross-number: [CONFIDE_PERSON_0010] is not eaten by the _0001 placeholder,
- idempotency: rehydrate(rehydrate(x)) == rehydrate(x),
- map mismatch: --verify-green with a wrong green hash warns; malformed map handled,
- RU inflection: inflected forms get DISTINCT placeholders and round-trip exactly
  (proving exact-value matching, NOT a lemmatized merge).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "anon", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "rehydrate", "scripts"))
import confide_core as C  # noqa: E402
import anon  # noqa: E402
import rehydrate  # noqa: E402

P = C.make_placeholder
CFG = {"layers": ["regex"]}


def _spans(text, vals_types):
    sp = []
    for v, t in vals_types:
        i = text.find(v)
        while i != -1:
            sp.append(C.Span(i, i + len(v), v, t, "x"))
            i = text.find(v, i + 1)
    return sp


# ----------------------------------------------------------------- 1. collision
def test_source_containing_sentinel_is_not_corrupted(tmp_path):
    """A (wildly unlikely) source that literally contains a sentinel token before
    anon must not corrupt an unrelated real value. We plant a literal PERSON sentinel
    in the prose and redact a real EMAIL: they have different types/indices, so the
    EMAIL round-trips exactly and the literal PERSON token is reported as an unmatched
    (it was never in the map) — no corruption, no crash."""
    src = "Note: literal [CONFIDE_PERSON_0001] in prose. Email a@b.io please."
    green, m = C.redact_reversible(src, _spans(src, [("a@b.io", "EMAIL")]))
    flat = C.map_lookup(m)
    assert "a@b.io" not in green
    assert "[CONFIDE_EMAIL_0001]" in green       # the real email is masked
    assert "[CONFIDE_PERSON_0001]" in green       # the literal survives verbatim
    back, stats = C.rehydrate(green, m)
    assert "a@b.io" in back                        # real value round-trips exactly
    # the planted literal is NOT in the map -> reported unmatched, left in place
    assert "[CONFIDE_PERSON_0001]" in back
    assert stats["unmatched"] == 1


def test_collision_through_anon_script(tmp_path):
    """End-to-end through the anon script: a file containing the sentinel literal is
    de-identified without raising, green written, map is the structured schema."""
    body = "Pre-existing [CONFIDE_EMAIL_0001] then real a@b.io here."
    src = tmp_path / "s.md"
    src.write_text(body, encoding="utf-8")
    res = anon.process_file(str(src), CFG)
    assert res["green"] and res["map_path"]
    mapping = json.loads((tmp_path / "s.map.json").read_text(encoding="utf-8"))
    assert mapping["schema_version"] == C.MAP_SCHEMA_VERSION
    gtext = (tmp_path / "s.green.md").read_text(encoding="utf-8")
    assert "a@b.io" not in gtext


# ------------------------------------------------------ 2. over-match negatives
def test_rehydrate_does_not_touch_ordinary_prose():
    """Naked prose lacking the CONFIDE prefix must be left exactly as-is."""
    m = {P("PERSON", 1): "Marina", P("ID", 2): "555-01"}
    prose = ("Person 1 met patient 1 in section 2; the person 1 note and PERSON_1 "
             "shorthand are ordinary text, not sentinels.")
    back, stats = C.rehydrate(prose, m)
    assert back == prose                      # untouched
    assert stats["restored"] == 0
    assert "Marina" not in back


# ------------------------------------------------------ 3. cross-number
def test_cross_number_not_eaten():
    m = {P("PERSON", 1): "Ann", P("PERSON", 10): "Bob"}
    text = f"{P('PERSON', 10)} and {P('PERSON', 1)} and again {P('PERSON', 10)}."
    back, _ = C.rehydrate(text, m)
    assert back == "Bob and Ann and again Bob."   # _0001 never eats _0010


def test_placeholder_in_token_distinct():
    """[CONFIDE_PERSON_0010] and [CONFIDE_PERSON_0001] map to different originals."""
    m = {P("PERSON", 1): "Ann", P("PERSON", 10): "Bob"}
    a = C.map_lookup(m)
    assert a[P("PERSON", 1)] == "Ann" and a[P("PERSON", 10)] == "Bob"
    assert P("PERSON", 1) != P("PERSON", 10)


# ------------------------------------------------------ 4. idempotency
def test_rehydrate_is_idempotent():
    m = {P("PERSON", 1): "Marina", P("DATE", 1): "15 January"}
    text = f"{P('PERSON', 1)} talked about {P('DATE', 1)} with {P('PERSON', 1)}."
    once, _ = C.rehydrate(text, m)
    twice, stats2 = C.rehydrate(once, m)        # originals contain no sentinels
    assert twice == once
    assert stats2["restored"] == 0


# ------------------------------------------------------ 5. map mismatch / malformed
def test_verify_green_warns_on_wrong_hash(tmp_path):
    body = "Client a@b.io called."
    src = tmp_path / "session.md"
    src.write_text(body, encoding="utf-8")
    anon.process_file(str(src), CFG)
    green = tmp_path / "session.green.md"
    map_path = tmp_path / "session.map.json"

    # a DIFFERENT green file (wrong document) -> mismatch warning
    wrong = tmp_path / "other.green.md"
    wrong.write_text("totally different green text", encoding="utf-8")
    out = rehydrate.process(str(green), map_path=str(map_path),
                            verify_green=str(wrong), quiet=True)
    assert out["verify_ok"] is False
    assert "MISMATCH" in (out["verify_warning"] or "")

    # the CORRECT green file -> verify ok, no warning
    out2 = rehydrate.process(str(green), map_path=str(map_path),
                             verify_green=str(green), quiet=True,
                             out=str(tmp_path / "ok.restored.md"))
    assert out2["verify_ok"] is True
    assert out2["verify_warning"] is None


def test_verify_green_on_legacy_flat_map(tmp_path):
    """A legacy flat map has no green_sha256 -> verify cannot confirm; warns, no crash."""
    analysis = tmp_path / "a.md"
    analysis.write_text(f"{P('PERSON', 1)} here", encoding="utf-8")
    flat_map = tmp_path / "a.map.json"
    flat_map.write_text(json.dumps({P("PERSON", 1): "Marina"}), encoding="utf-8")
    green = tmp_path / "g.green.md"
    green.write_text("anything", encoding="utf-8")
    out = rehydrate.process(str(analysis), map_path=str(flat_map),
                            verify_green=str(green), quiet=True)
    assert out["verify_ok"] is None
    assert "no green_sha256" in (out["verify_warning"] or "")
    # still rehydrated despite legacy map
    assert out["restored"] == 1


def test_malformed_map_handled(tmp_path):
    analysis = tmp_path / "a.md"
    analysis.write_text("hello", encoding="utf-8")
    bad = tmp_path / "a.map.json"
    bad.write_text("{ this is : not json", encoding="utf-8")
    import pytest
    with pytest.raises(SystemExit):
        rehydrate.process(str(analysis), map_path=str(bad), quiet=True)


# ------------------------------------------------------ 6. RU inflection (no merge)
def test_ru_inflection_distinct_placeholders_roundtrip():
    """Inflected RU forms are SEPARATE surface values -> DISTINCT placeholders, and
    each round-trips exactly. Proves exact-value matching, NOT a lemmatized merge."""
    text = "Марина пришла. Я говорил с Мариной вчера."
    spans = _spans(text, [("Марина", "PERSON"), ("Мариной", "PERSON")])
    green, m = C.redact_reversible(text, spans)
    flat = C.map_lookup(m)
    # two DISTINCT placeholders for the two inflected forms (no merge)
    phs = sorted(flat.keys())
    assert len(phs) == 2
    assert set(flat.values()) == {"Марина", "Мариной"}
    assert "Марина" not in green and "Мариной" not in green
    # exact round-trip
    back, stats = C.rehydrate(green, m)
    assert back == text
    assert stats["restored"] == 2 and stats["unmatched"] == 0
