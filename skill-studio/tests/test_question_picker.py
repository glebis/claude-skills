from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta, TranscriptTurn
from skill_studio.presets import load_preset
from skill_studio.interview.question_picker import pick_next_question


def test_initial_question_is_preset_opening():
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    preset = load_preset("ai-agent")
    llm = MagicMock()
    q = pick_next_question(design, preset, llm=llm)
    assert q == preset.opening_question
    llm.ask.assert_not_called()


def test_mid_interview_asks_llm_targeting_uncovered_field():
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    design.hook = "agent that drafts reviews"
    # Seed transcript so we're past first turn
    design.transcript.append(TranscriptTurn(role="assistant", text="opening"))
    design.transcript.append(TranscriptTurn(role="user", text="agent that drafts reviews"))
    preset = load_preset("ai-agent")
    llm = MagicMock()
    llm.ask.return_value = "What does Sunday afternoon usually look like for you?"
    q = pick_next_question(design, preset, llm=llm)
    assert q == "What does Sunday afternoon usually look like for you?"
    call = llm.ask.call_args
    history = call.kwargs.get("history") or call.args[0]
    msg_text = history[-1]["content"]
    assert "TARGET FIELD" in msg_text
