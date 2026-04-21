"""Finding 3: multi-turn integration test verifying the director progresses through the arc.

Uses a mocked LLM that alternates between landing and not-landing signals
with mixed schema patches, then asserts structural arc properties.
"""
from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.loop import run_interview_turn, _load_state
from skill_studio.presets import load_preset


def _make_design():
    return DesignJSON(meta=Meta(preset="ai-agent"))


def _combined(landed: bool, patch: dict | None = None) -> str:
    import json
    return json.dumps({"landed": landed, "patch": patch or {}})


def test_ten_turn_interview_progresses_phases():
    """Simulate a scripted 10-turn interview with varying answer quality,
    assert phases advance, no follow-up cap violated, no repeated question,
    final phase is in {SHAPE, GUARDRAILS, CLOSE}.
    """
    design = _make_design()
    preset = load_preset("ai-agent")
    llm = MagicMock()

    # Script: turn index -> (landed, patch)
    # Alternate landing to drive arc progression without being trivial
    scripts = [
        # Turn 1: opening — aspiration lands
        _combined(True,  {"hook": "Weekly review drafter"}),
        # Turn 2: pain.current_pain — doesn't land, follow-up
        _combined(False, {}),
        # Turn 3: pain.current_pain — now lands
        _combined(True,  {"problem": {"what_hurts": "takes 90 min every Sunday"}}),
        # Turn 4: pain.push — lands
        _combined(True,  {"problem": {"cost_today": "90 min/wk"}}),
        # Turn 5: moment — doesn't land, follow-up
        _combined(False, {}),
        # Turn 6: moment — lands
        _combined(True,  {"before_after": {"before_internal": "stressed every Sunday"}}),
        # Turn 7: cost — lands
        _combined(True,  {"problem": {"cost_today": "3h incl recovery"}}),
        # Turn 8: after — lands
        _combined(True,  {"before_after": {"after_external": "done in 10 min"}}),
        # Turn 9: shape.trigger — lands
        _combined(True,  {"trigger": {"detail": "every Sunday 18:00"}}),
        # Turn 10: shape.capabilities — lands
        _combined(True,  {"capabilities": ["pull notes", "draft review"]}),
    ]

    llm.ask.side_effect = scripts

    # Turn 0: opening question (no LLM call)
    run_interview_turn(design, preset, llm, user_input=None)
    phase_history = [design.interview_state.phase]
    asked_questions = {design.transcript[-1].text}

    # Turns 1-10
    user_answers = [
        "I want to stop spending every Sunday on writing my weekly review",
        "The process of collecting notes, structuring, writing takes ages",
        "I gather notes from Obsidian manually and it's incredibly tedious",
        "I've been doing this for months, the Sunday dread is real",
        "Last Sunday I sat down at 5pm and it was 8pm before I had a draft",
        "I was exhausted and hadn't done anything else meaningful all day",
        "It costs me roughly 3 hours including the mental drain before and after",
        "I'd have my Sunday back — feel lighter, more rested, start fresh",
        "Automatically on Sunday at 6pm when I sit down to do the review",
        "Pull Obsidian notes for the week, draft the review, send to email",
    ]

    for i, answer in enumerate(user_answers):
        run_interview_turn(design, preset, llm, user_input=answer)
        current_phase = design.interview_state.phase
        phase_history.append(current_phase)
        last_q = design.transcript[-1].text
        assert last_q not in asked_questions, (
            f"Question repeated at turn {i+2}: {last_q!r}"
        )
        asked_questions.add(last_q)

    # Structural assertions
    unique_phases = list(dict.fromkeys(phase_history))  # order-preserving dedup
    assert len(unique_phases) >= 3, (
        f"Expected at least 3 distinct phases, got {unique_phases}"
    )

    # No subject had more than max_follow_ups follow-ups (default 2)
    # We can verify indirectly: follow_ups_on_current never persisted > 2
    # (it resets on each NEW_SUBJECT). Check the final value directly.
    final_state = _load_state(design)
    assert final_state.follow_ups_on_current <= final_state.max_follow_ups, (
        f"follow_ups exceeded max: {final_state.follow_ups_on_current} > {final_state.max_follow_ups}"
    )

    # Final phase should be in the later arc (we drove 10 turns of mostly landings)
    late_phases = {"shape", "guardrails", "close"}
    assert design.interview_state.phase in late_phases, (
        f"Expected late-arc phase, got {design.interview_state.phase!r}. "
        f"Full phase history: {phase_history}"
    )

    # Transcript should have 11 assistant turns (turn 0 + 10 follow-ups)
    assistant_turns = [t for t in design.transcript if t.role == "assistant"]
    assert len(assistant_turns) == 11, (
        f"Expected 11 assistant turns, got {len(assistant_turns)}"
    )
