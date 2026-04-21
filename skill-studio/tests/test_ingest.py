"""Tests for ingest.transcript (deterministic) and ingest.proposer (LLM-mocked)."""
from __future__ import annotations
import json
from pathlib import Path

import pytest

from skill_studio.ingest.transcript import Bundle, extract, resolve_session
from skill_studio.ingest.proposer import propose


# --------------------------------------------------------------------------- #
# Deterministic extraction
# --------------------------------------------------------------------------- #

def test_extract_empty_transcript(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("")
    b = extract(p, session_id="x", source="path")
    assert b.models_tried == []
    assert b.total_cost_usd == 0.0
    assert b.iterations == []
    assert b.pain_snippets == []


def test_extract_models_cost_and_pain(tmp_path):
    p = tmp_path / "t.md"
    p.write_text(
        "I tried gpt-4o first, then claude-3-5-sonnet. "
        "Total cost $2.45 so far. "
        "The retrieval is frustratingly slow and keeps failing on long queries. "
        "Changed the retrieval prompt again."
    )
    b = extract(p, session_id="abc", source="path")
    assert "gpt-4o" in b.models_tried
    assert any("claude" in m for m in b.models_tried)
    assert b.total_cost_usd == pytest.approx(2.45)
    assert b.pain_snippets, "expected at least one pain snippet"
    assert any(it["action"] == "prompt_change" for it in b.iterations)
    assert any(it["action"] == "cost_event" for it in b.iterations)


def test_extract_jsonl_claude_code_format(tmp_path):
    p = tmp_path / "session.jsonl"
    lines = [
        json.dumps({"message": {"content": "Trying gpt-4o for retrieval."}}),
        json.dumps({"message": {"content": [{"type": "text", "text": "spent $0.37 on this run"}]}}),
        json.dumps({"message": {"content": "updated the prompt to include context"}}),
    ]
    p.write_text("\n".join(lines))
    b = extract(p, session_id="s1", source="claude-code")
    assert "gpt-4o" in b.models_tried
    assert b.total_cost_usd == pytest.approx(0.37)
    assert any(it["action"] == "prompt_change" for it in b.iterations)


def test_extract_caps_pain_snippets(tmp_path):
    p = tmp_path / "pain.md"
    p.write_text(("This is so slow and frustrating. " * 20))
    b = extract(p, session_id="x", source="path", max_pain_snippets=3)
    assert len(b.pain_snippets) <= 3


def test_extract_ignores_absurd_costs(tmp_path):
    p = tmp_path / "big.md"
    p.write_text("cost: $9999.00")  # above the 100 cap → ignored
    b = extract(p, session_id="x", source="path")
    assert b.total_cost_usd == 0.0


def test_bundle_to_dict_summary(tmp_path):
    p = tmp_path / "t.md"
    p.write_text("tried gpt-4o; cost $0.50; new prompt")
    b = extract(p, session_id="x", source="path")
    d = b.to_dict()
    assert d["summary"]["models_tried"] >= 1
    assert d["summary"]["total_cost_usd"] == pytest.approx(0.50)
    assert d["summary"]["turns"] >= 1


def test_resolve_session_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    with pytest.raises(FileNotFoundError):
        resolve_session("does-not-exist")


# --------------------------------------------------------------------------- #
# Proposer (LLM mocked)
# --------------------------------------------------------------------------- #

class _StubLLM:
    def __init__(self, response: str):
        self._response = response

    def ask(self, history, max_tokens=1200):
        return self._response


def test_propose_returns_patch_and_rationale():
    bundle = Bundle(session_id="x", source="path", models_tried=["gpt-4o"], total_cost_usd=1.20)
    llm = _StubLLM(json.dumps({
        "patch": {"hook": "RAG tuning agent", "problem": {"cost_today": "$1.20 burned"}},
        "rationale": {"hook": "models_tried + cost signal", "problem.cost_today": "total_cost_usd=1.20"},
    }))
    patch, rationale = propose(bundle, llm)
    assert patch["hook"] == "RAG tuning agent"
    assert "problem.cost_today" in rationale


def test_propose_returns_empty_on_bad_json():
    bundle = Bundle(session_id="x", source="path")
    llm = _StubLLM("not json at all")
    patch, rationale = propose(bundle, llm)
    assert patch == {}
    assert rationale == {}


def test_propose_returns_empty_on_llm_exception():
    class _Boom:
        def ask(self, history, max_tokens=1200):
            raise RuntimeError("provider down")
    patch, rationale = propose(Bundle(session_id="x", source="path"), _Boom())
    assert patch == {} and rationale == {}


def test_propose_extracts_embedded_json():
    bundle = Bundle(session_id="x", source="path")
    # LLMs sometimes wrap JSON in prose despite instructions
    wrapped = 'Here is the result:\n{"patch": {"hook": "x"}, "rationale": {}}\nHope that helps.'
    patch, rationale = propose(bundle, _StubLLM(wrapped))
    assert patch == {"hook": "x"}
