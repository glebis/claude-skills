from __future__ import annotations
from skill_studio.schema import DesignJSON, TranscriptTurn
from skill_studio.presets import Preset
from skill_studio.interview.director import DirectorState, Move, MoveKind, next_move
from skill_studio.interview.question_picker import pick_question
from skill_studio.interview.extractor import extract_and_apply
from skill_studio.interview.combined import analyze_turn
from skill_studio.interview.modes import STYLE_SYSTEM_PROMPTS
from skill_studio.interview.phases import Phase
from skill_studio.interview.subjects import subjects_for


def _preferred_framework(preset_name: str) -> str:
    return {
        "ai-agent": "forces",
        "life-automation": "forces",
        "knowledge-work": "forces",
        "custom": "forces",
    }.get(preset_name, "forces")


def _load_state(design: DesignJSON) -> DirectorState:
    """Hydrate DirectorState from design.interview_state (survives restarts)."""
    return DirectorState.from_schema_state(design.interview_state)


def _save_state(design: DesignJSON, state: DirectorState) -> None:
    """Persist DirectorState back into design so storage can flush it."""
    design.interview_state = state.to_schema_state()


def run_interview_turn(design: DesignJSON, preset: Preset, llm, user_input: str | None) -> str:
    """Run one turn of the narrative-arc interview.

    Call with user_input=None on the first turn to receive the opening question.
    On subsequent turns pass the user's text; the function appends both sides to
    the transcript and returns the next interviewer question.

    Signature is identical to the legacy loop — voice/ and cli.py are unaffected.
    """
    state = _load_state(design)
    framework = _preferred_framework(design.meta.preset)
    style_prompt = STYLE_SYSTEM_PROMPTS.get(design.meta.interview_mode.style, "")

    if user_input is not None:
        design.transcript.append(TranscriptTurn(role="user", text=user_input))
        # Single LLM call: extract schema fields AND decide if subject landed.
        # Falls back to (False, {}) on any error, which is conservative but safe.
        tail = [{"role": t.role, "text": t.text} for t in design.transcript[-8:]]
        landed, _patch = analyze_turn(design, state.current_subject, tail, llm)

        # Decide next move using the pre-computed landed signal (no extra LLM call)
        move = next_move(state, landed=landed)
    else:
        # First turn — start at the opening of the arc
        move = Move(MoveKind.NEW_SUBJECT, Phase.OPENING, None, "start")

    # Apply state transitions from the move
    if move.kind == MoveKind.FOLLOW_UP:
        state.follow_ups_on_current += 1

    elif move.kind == MoveKind.NEW_SUBJECT:
        if state.current_subject is not None:
            state.subjects_landed.add(state.current_subject.key)
        state.current_subject = move.subject
        state.follow_ups_on_current = 0

    elif move.kind == MoveKind.ADVANCE_PHASE:
        if state.current_subject is not None:
            state.subjects_landed.add(state.current_subject.key)
        state.phase = move.phase
        state.current_subject = None
        state.follow_ups_on_current = 0
        # Lookahead: enter the first subject of the new phase immediately
        first = subjects_for(state.phase)
        if first:
            state.current_subject = first[0]
            move = Move(MoveKind.NEW_SUBJECT, state.phase, first[0], "phase entry")

    elif move.kind == MoveKind.CLOSE:
        state.phase = Phase.CLOSE
        state.current_subject = None

    # Pick and return a question
    tail = [{"role": t.role, "text": t.text} for t in design.transcript[-6:]]
    asked_in_phase = set(state.asked_questions_per_phase.get(state.phase.value, []))
    question = pick_question(move, framework, tail, llm, style_prompt, asked_in_phase=asked_in_phase)

    # Record the asked question for per-phase dedup (Finding 4)
    phase_key = state.phase.value
    if phase_key not in state.asked_questions_per_phase:
        state.asked_questions_per_phase[phase_key] = []
    if question not in state.asked_questions_per_phase[phase_key]:
        state.asked_questions_per_phase[phase_key].append(question)

    design.transcript.append(TranscriptTurn(role="assistant", text=question))

    # Persist director state into design (survives restarts via storage)
    _save_state(design, state)

    return question
