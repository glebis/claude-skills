"""Tests for the narrative-arc interview loop.

v1.6 rewrite: loop now uses director + YAML question banks instead of
schema-field targeting. Tests verify the structural behavior (turn ordering,
transcript appending, extraction, arc progression) — not exact question text.
"""
from unittest.mock import MagicMock, patch
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.loop import run_interview_turn
from skill_studio.presets import load_preset


def make_fresh_design() -> DesignJSON:
    # Each DesignJSON gets a fresh UUID so interview_state starts clean
    return DesignJSON(meta=Meta(preset="ai-agent"))


def test_first_turn_returns_a_question():
    """First turn (user_input=None) must return a non-empty string."""
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    question = run_interview_turn(design, preset, llm, user_input=None)
    assert isinstance(question, str)
    assert question.strip()


def test_first_turn_does_not_call_llm_for_question():
    """Opening question comes from YAML — LLM should not be called for the question itself."""
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    run_interview_turn(design, preset, llm, user_input=None)
    # LLM may be called 0 times (YAML pool hit). It must NOT be called for pick_question.
    # The first YAML question is returned without LLM.
    # (Extraction is not called on the first turn either.)
    llm.ask.assert_not_called()


def test_first_turn_appends_assistant_turn():
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    run_interview_turn(design, preset, llm, user_input=None)
    assert len(design.transcript) == 1
    assert design.transcript[-1].role == "assistant"


def test_second_turn_appends_user_then_assistant():
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    # First turn
    run_interview_turn(design, preset, llm, user_input=None)
    # Second turn: combined call returns landed=false, empty patch
    llm.ask.side_effect = [
        '{"landed": false, "patch": {}}',  # analyze_turn combined call
    ]
    run_interview_turn(design, preset, llm, user_input="I want to draft reviews")
    assert design.transcript[-2].role == "user"
    assert design.transcript[-1].role == "assistant"


def test_second_turn_extraction_updates_design():
    """Extraction runs after each user turn and merges patches into the design."""
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    run_interview_turn(design, preset, llm, user_input=None)
    # Combined call now returns {"landed": bool, "patch": {...}} in one response
    llm.ask.side_effect = [
        '{"landed": false, "patch": {"hook": "Draft reviews"}}',  # analyze_turn
    ]
    run_interview_turn(design, preset, llm, user_input="I want to draft reviews")
    assert design.hook == "Draft reviews"


def test_multiple_turns_transcript_grows():
    design = make_fresh_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()
    # Combined call returns {"landed": false, "patch": {}} — one call per user turn
    llm.ask.return_value = '{"landed": false, "patch": {}}'
    run_interview_turn(design, preset, llm, user_input=None)
    run_interview_turn(design, preset, llm, user_input="turn 1")
    run_interview_turn(design, preset, llm, user_input="turn 2")
    # 1 assistant + (user + assistant) * 2 = 5 turns
    assert len(design.transcript) == 5
