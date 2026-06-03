"""Offline-deterministic tests for confide_core (no network/models needed)."""
import os, sys, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C


def test_config_defaults_no_file():
    cfg = C.load_config("/nonexistent/confide/config.json")
    assert cfg["engine"] == "ollama"
    assert cfg["anon_model"] == "qwen2.5:3b"
    assert cfg["privacy"]["local_only"] is True
    assert "regex" in cfg["layers"]


def test_config_merge_over_defaults():
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"anon_model": "qwen2.5:14b", "privacy": {"cloud_apis": True}}, f)
        p = f.name
    cfg = C.load_config(p)
    assert cfg["anon_model"] == "qwen2.5:14b"        # overridden
    assert cfg["privacy"]["cloud_apis"] is True       # nested override
    assert cfg["privacy"]["local_only"] is True       # default preserved
    assert cfg["engine"] == "ollama"                  # default preserved
    os.unlink(p)


def test_write_then_load_roundtrip():
    p = os.path.join(tempfile.mkdtemp(), "config.json")
    C.write_config(C.DEFAULTS, p)
    assert C.load_config(p)["anon_model"] == "qwen2.5:3b"


def test_regex_detects_email_phone_url_date():
    t = "Email alina.k@example.ru, call +7-916-555-21-43, see https://x.io on 15.01.2026."
    types = {s.type for s in C.detect_regex(t)}
    assert {"EMAIL", "PHONE", "URL", "DATE"} <= types


def test_regex_relative_date():
    assert any(s.type == "DATE" for s in C.detect_regex("we met last Tuesday"))
    assert any(s.type == "DATE" for s in C.detect_regex("встретились 3 февраля"))


def test_phone_needs_enough_digits():
    # "12-34" is too short to be a phone
    assert not any(s.type == "PHONE" for s in C.detect_regex("room 12-34"))


def test_merge_overlapping_spans():
    spans = [C.Span(0, 5, "a", "PERSON", "x"), C.Span(3, 9, "b", "EMAIL", "y"), C.Span(20, 25, "c", "DATE", "z")]
    merged = C.merge_spans(spans)
    assert len(merged) == 2
    assert merged[0].start == 0 and merged[0].end == 9  # merged 0-5 + 3-9
    assert merged[0].type == "EMAIL"                    # longest contributor wins


def test_redact_typed_placeholder():
    t = "Имя marina@example.ru тут"
    spans = C.detect_regex(t)
    out = C.redact(t, spans, "typed_placeholder")
    assert "[EMAIL]" in out
    assert "marina@example.ru" not in out


def test_redact_generic_style():
    t = "x https://leak.io y"
    out = C.redact(t, C.detect_regex(t), "generic")
    assert "[REDACTED]" in out and "leak.io" not in out


def test_anonymize_regex_only_no_leakage():
    cfg = dict(C.DEFAULTS); cfg["layers"] = ["regex"]   # offline, deterministic
    t = "Client a.k@example.ru phoned +7-916-555-21-43 on 05.02.2026."
    r = C.anonymize(t, cfg)
    # every planted direct identifier removed
    for leak in ["a.k@example.ru", "+7-916-555-21-43", "05.02.2026"]:
        assert leak not in r["redacted_text"]
    # stats are COUNTS only — no PII values anywhere in stats
    blob = json.dumps(r["stats"])
    for leak in ["a.k@example.ru", "555-21-43"]:
        assert leak not in blob
    assert r["stats"]["by_type"].get("EMAIL", 0) >= 1
    assert 0.0 < r["stats"]["redaction_rate"] <= 1.0
