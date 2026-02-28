import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import granola

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_load_cache_parses_string_state(monkeypatch):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))
    state = granola.load_cache()
    assert "documents" in state
    assert "abc-123" in state["documents"]
    assert state["documents"]["abc-123"]["title"] == "Test Meeting"


def test_load_cache_parses_object_state(monkeypatch):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_object_state.json"))
    state = granola.load_cache()
    assert "documents" in state
    assert "def-456" in state["documents"]
    assert state["documents"]["def-456"]["title"] == "Another Meeting"
