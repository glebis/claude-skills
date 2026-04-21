from unittest.mock import MagicMock
from skill_studio.interview.phases import Phase
from skill_studio.interview.subjects import subjects_for
from skill_studio.interview.director import (
    DirectorState,
    Move,
    MoveKind,
    next_move,
    _subject_landed,
)


def make_llm(response: str = "NO") -> MagicMock:
    llm = MagicMock()
    llm.ask.return_value = response
    return llm


# ---------------------------------------------------------------------------
# _subject_landed
# ---------------------------------------------------------------------------

def test_subject_landed_yes():
    subject = subjects_for(Phase.OPENING)[0]
    llm = make_llm("YES")
    assert _subject_landed(subject, "I want to automate my weekly review", llm) is True


def test_subject_landed_no():
    subject = subjects_for(Phase.OPENING)[0]
    llm = make_llm("NO")
    assert _subject_landed(subject, "I dunno", llm) is False


def test_subject_landed_short_text_returns_false():
    subject = subjects_for(Phase.OPENING)[0]
    llm = make_llm("YES")
    assert _subject_landed(subject, "ok", llm) is False
    llm.ask.assert_not_called()


def test_subject_landed_llm_error_returns_false():
    subject = subjects_for(Phase.OPENING)[0]
    llm = MagicMock()
    llm.ask.side_effect = RuntimeError("oops")
    assert _subject_landed(subject, "I want to change everything", llm) is False


# ---------------------------------------------------------------------------
# next_move — initial state
# ---------------------------------------------------------------------------

def test_first_move_is_new_subject_in_opening():
    state = DirectorState()
    llm = make_llm()
    move = next_move(state, "", llm)
    assert move.kind == MoveKind.NEW_SUBJECT
    assert move.phase == Phase.OPENING
    assert move.subject is not None
    assert move.subject.key == "aspiration"


# ---------------------------------------------------------------------------
# next_move — follow-up logic
# ---------------------------------------------------------------------------

def test_follow_up_when_not_landed_and_budget_remains():
    state = DirectorState()
    state.current_subject = subjects_for(Phase.OPENING)[0]
    state.follow_ups_on_current = 0
    llm = make_llm("NO")
    move = next_move(state, "I'm not sure what I want", llm)
    assert move.kind == MoveKind.FOLLOW_UP


def test_advance_subject_when_landed():
    state = DirectorState()
    state.phase = Phase.PAIN
    state.current_subject = subjects_for(Phase.PAIN)[0]  # current_pain
    state.follow_ups_on_current = 0
    llm = make_llm("YES")
    move = next_move(state, "The current process takes forever and I hate it", llm)
    # There is another subject (push) in PAIN phase
    assert move.kind == MoveKind.NEW_SUBJECT
    assert move.subject.key == "push"


def test_advance_phase_when_all_subjects_landed():
    state = DirectorState()
    pain_subjects = subjects_for(Phase.PAIN)
    state.phase = Phase.PAIN
    state.current_subject = pain_subjects[-1]  # last subject in PAIN
    # mark all but current as landed
    for s in pain_subjects[:-1]:
        state.subjects_landed.add(s.key)
    state.follow_ups_on_current = 0
    llm = make_llm("YES")
    move = next_move(state, "I've been using this broken process for years", llm)
    assert move.kind == MoveKind.ADVANCE_PHASE
    assert move.phase == Phase.MOMENT


def test_close_when_at_last_phase():
    state = DirectorState()
    state.phase = Phase.CLOSE
    close_subjects = subjects_for(Phase.CLOSE)
    state.current_subject = close_subjects[0]
    # Mark as landed
    llm = make_llm("YES")
    move = next_move(state, "Yes, this is exactly me", llm)
    assert move.kind == MoveKind.CLOSE


def test_max_follow_ups_forces_advance():
    state = DirectorState(max_follow_ups=2)
    state.phase = Phase.OPENING
    state.current_subject = subjects_for(Phase.OPENING)[0]
    state.follow_ups_on_current = 2  # at max
    llm = make_llm("NO")  # still not landed — but budget exhausted
    move = next_move(state, "I'm vague", llm)
    # Should advance phase since no more subjects in OPENING
    assert move.kind == MoveKind.ADVANCE_PHASE
    assert move.phase == Phase.PAIN
