"""Tests for skill_studio.synthesis — LLM recap + groundwork session log."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from skill_studio.schema import DesignJSON, Meta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _design(hook: str = "test hook") -> DesignJSON:
    d = DesignJSON(meta=Meta(preset="ai-agent"))
    d.hook = hook
    return d


def _mock_llm(response: str = "foo") -> MagicMock:
    llm = MagicMock()
    llm.ask.return_value = response
    return llm


def _raising_llm() -> MagicMock:
    llm = MagicMock()
    llm.ask.side_effect = RuntimeError("boom")
    return llm


# ---------------------------------------------------------------------------
# synthesize_session
# ---------------------------------------------------------------------------

def test_synthesize_session_returns_llm_output():
    from skill_studio.synthesis import synthesize_session
    turns = [{"role": "assistant", "text": "What hurts?"}, {"role": "user", "text": "Everything."}]
    result = synthesize_session(turns, _mock_llm("foo"))
    assert result == "foo"


def test_synthesize_empty_transcript_returns_empty():
    from skill_studio.synthesis import synthesize_session
    assert synthesize_session([], _mock_llm()) == ""


def test_synthesize_llm_error_returns_empty():
    from skill_studio.synthesis import synthesize_session
    turns = [{"role": "user", "text": "hello"}]
    result = synthesize_session(turns, _raising_llm())
    assert result == ""


# ---------------------------------------------------------------------------
# write_groundwork_session
# ---------------------------------------------------------------------------

def test_write_groundwork_session_skips_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.synthesis.GROUNDWORK_ROOT", tmp_path / ".groundwork")
    from skill_studio.synthesis import write_groundwork_session
    d = _design()
    result = write_groundwork_session(d, "summary text", tmp_path / "session")
    assert result is None


def test_write_groundwork_session_writes_file(tmp_path, monkeypatch):
    gw_root = tmp_path / ".groundwork"
    sessions_dir = gw_root / "sessions"
    sessions_dir.mkdir(parents=True)
    monkeypatch.setattr("skill_studio.synthesis.GROUNDWORK_ROOT", gw_root)

    from skill_studio.synthesis import write_groundwork_session
    d = _design("my cool hook")
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    out = write_groundwork_session(d, "great insight", session_dir)
    assert out is not None
    assert out.exists()
    content = out.read_text()
    # Check frontmatter keys
    assert "source: skill-studio" in content
    assert f"session_id: {d.meta.id}" in content
    assert "preset: ai-agent" in content
    assert "type: interview" in content
    # Check body
    assert "# my cool hook" in content
    assert "great insight" in content
    assert "design.md" in content


# ---------------------------------------------------------------------------
# write_session_summary
# ---------------------------------------------------------------------------

def test_write_session_summary_writes_local_and_groundwork(tmp_path, monkeypatch):
    gw_root = tmp_path / ".groundwork"
    sessions_dir = gw_root / "sessions"
    sessions_dir.mkdir(parents=True)
    monkeypatch.setattr("skill_studio.synthesis.GROUNDWORK_ROOT", gw_root)

    from skill_studio.synthesis import write_session_summary
    d = _design("cool hook")
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    turns = [{"role": "user", "text": "hello"}]

    results = write_session_summary(d, turns, _mock_llm("great summary"), session_dir)
    assert "local" in results
    assert results["local"].exists()
    assert "great summary" in results["local"].read_text()
    assert "groundwork" in results
    assert results["groundwork"].exists()


def test_write_session_summary_never_raises(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.synthesis.GROUNDWORK_ROOT", tmp_path / ".groundwork")
    from skill_studio.synthesis import write_session_summary
    # session_dir does NOT exist — write will fail without mkdir
    d = _design()
    session_dir = tmp_path / "nonexistent" / "session"
    turns = [{"role": "user", "text": "hi"}]
    # Should not raise even with a raising llm and missing session_dir
    result = write_session_summary(d, turns, _raising_llm(), session_dir)
    assert isinstance(result, dict)
