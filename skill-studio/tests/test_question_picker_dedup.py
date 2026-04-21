"""Finding 4: per-phase asked-questions dedup via asked_in_phase set."""
from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.director import Move, MoveKind
from skill_studio.interview.phases import Phase
from skill_studio.interview.subjects import subjects_for
from skill_studio.interview.question_picker import pick_question
from skill_studio.interview.loop import run_interview_turn
from skill_studio.presets import load_preset


FRAMEWORK = "forces"


def _opening_move():
    subj = subjects_for(Phase.OPENING)[0]
    return Move(MoveKind.NEW_SUBJECT, Phase.OPENING, subj, "test")


def test_three_distinct_questions_from_opening_pool():
    """Three consecutive calls in OPENING yield 3 distinct questions from the pool."""
    llm = MagicMock()
    llm.ask.return_value = "Tell me more."  # fallback if pool exhausted

    asked: set[str] = set()
    questions = []
    for _ in range(3):
        q = pick_question(_opening_move(), FRAMEWORK, [], llm, asked_in_phase=asked)
        questions.append(q)
        asked.add(q)

    assert len(set(questions)) == 3, f"Expected 3 distinct questions, got: {questions}"


def test_fourth_turn_triggers_llm_fallback():
    """Once the 3-question pool is exhausted, LLM generates the 4th question."""
    llm = MagicMock()
    fallback = "What's drawing you to this right now?"
    llm.ask.return_value = fallback

    # Exhaust the pool
    asked: set[str] = set()
    for _ in range(3):
        q = pick_question(_opening_move(), FRAMEWORK, [], llm, asked_in_phase=asked)
        asked.add(q)

    # 4th call — pool exhausted, LLM must be called
    llm.ask.reset_mock()
    q4 = pick_question(_opening_move(), FRAMEWORK, [], llm, asked_in_phase=asked)
    assert llm.ask.called, "LLM should be called when pool is exhausted"
    assert q4 == fallback


def test_loop_persists_asked_questions_per_phase():
    """run_interview_turn stores asked questions in design.interview_state."""
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    preset = load_preset("ai-agent")
    llm = MagicMock()
    llm.ask.return_value = "NO"

    run_interview_turn(design, preset, llm, user_input=None)

    phase_key = design.interview_state.phase
    asked = design.interview_state.asked_questions_per_phase
    assert phase_key in asked
    assert len(asked[phase_key]) == 1


def test_no_repeated_question_across_restarts():
    """After simulated restart, asked_in_phase set prevents re-asking first question."""
    design = DesignJSON(meta=Meta(preset="ai-agent"))
    preset = load_preset("ai-agent")
    llm = MagicMock()
    llm.ask.return_value = "NO"

    # Turn 0
    run_interview_turn(design, preset, llm, user_input=None)
    first_q = design.transcript[0].text

    # Turn 1 — must not repeat first_q; combined call
    llm.ask.side_effect = ['{"landed": false, "patch": {}}']
    run_interview_turn(design, preset, llm, user_input="I want to fix my review process")
    second_q = design.transcript[-1].text

    assert second_q != first_q, f"Question repeated: {first_q!r}"
