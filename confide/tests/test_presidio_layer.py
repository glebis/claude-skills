"""Presidio optional ensemble layer: off by default, graceful when absent, wired in."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
import confide_core as C

def test_presidio_off_by_default():
    assert "presidio" not in C.DEFAULTS["layers"]

def test_presidio_graceful_when_unavailable(monkeypatch):
    # simulate presidio not installed -> layer returns [] (never hard-fails)
    import builtins
    real = builtins.__import__
    def boom(name, *a, **k):
        if name.startswith("presidio"): raise ImportError("no presidio")
        return real(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", boom)
    C._PRESIDIO_ENGINE.clear()
    assert C.detect_presidio("Меня зовут Марина", dict(C.DEFAULTS)) == []

def test_presidio_layer_wired_into_anonymize():
    # enabling the layer must not crash even if the engine can't load
    cfg = dict(C.DEFAULTS); cfg["layers"] = ["regex", "presidio"]
    out = C.anonymize("позвони +7-916-555-21-43", cfg)
    assert "redacted_text" in out and "+7-916-555-21-43" not in out["redacted_text"]

def test_presidio_maps_entity_types():
    assert C._PRESIDIO_MAP["EMAIL_ADDRESS"] == "EMAIL"
    assert C._PRESIDIO_MAP["PHONE_NUMBER"] == "PHONE"
    assert C._PRESIDIO_MAP["GPE"] == "LOCATION"
