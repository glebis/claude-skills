from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from skill_studio.interview.phases import Phase, next_phase, ARC
from skill_studio.interview.subjects import subjects_for, Subject, SUBJECTS


class MoveKind(str, Enum):
    FOLLOW_UP = "follow_up"
    NEW_SUBJECT = "new_subject"
    ADVANCE_PHASE = "advance_phase"
    CLOSE = "close"


@dataclass
class DirectorState:
    phase: Phase = Phase.OPENING
    current_subject: Subject | None = None
    subjects_landed: set[str] = field(default_factory=set)
    follow_ups_on_current: int = 0
    max_follow_ups: int = 4  # conversational default; each subject gets more probing before moving on
    asked_questions_per_phase: dict[str, list[str]] = field(default_factory=dict)

    def to_schema_state(self):
        """Serialize to InterviewState for persistence in DesignJSON."""
        from skill_studio.schema import InterviewState
        return InterviewState(
            phase=self.phase.value,
            current_subject_key=self.current_subject.key if self.current_subject else None,
            subjects_landed=list(self.subjects_landed),
            follow_ups_on_current=self.follow_ups_on_current,
            max_follow_ups=self.max_follow_ups,
            asked_questions_per_phase={
                k: list(v) for k, v in self.asked_questions_per_phase.items()
            },
        )

    @classmethod
    def from_schema_state(cls, state) -> "DirectorState":
        """Hydrate from a persisted InterviewState schema object."""
        phase = Phase(state.phase)
        # Resolve current subject from key
        current_subject: Subject | None = None
        if state.current_subject_key:
            for subj_list in SUBJECTS.values():
                for s in subj_list:
                    if s.key == state.current_subject_key:
                        current_subject = s
                        break
        return cls(
            phase=phase,
            current_subject=current_subject,
            subjects_landed=set(state.subjects_landed),
            follow_ups_on_current=state.follow_ups_on_current,
            max_follow_ups=state.max_follow_ups,
            asked_questions_per_phase={
                k: list(v) for k, v in state.asked_questions_per_phase.items()
            },
        )


@dataclass
class Move:
    kind: MoveKind
    phase: Phase
    subject: Subject | None
    rationale: str = ""


def next_move(state: DirectorState, last_user_text: str | None = None, llm=None, *, landed: bool | None = None) -> Move:
    """Decide the next move.

    Two call modes:
      - Legacy: next_move(state, last_user_text, llm) — calls _subject_landed internally (2 LLM calls per turn).
      - Fast:   next_move(state, landed=<bool>)        — caller passes pre-computed landed signal
                (used by combined.analyze_turn for 1 LLM call per turn).
    """
    # Initial move: first subject of current phase
    if state.current_subject is None:
        subjects = subjects_for(state.phase)
        if not subjects:
            nxt = next_phase(state.phase)
            return Move(
                MoveKind.ADVANCE_PHASE if nxt else MoveKind.CLOSE,
                nxt or Phase.CLOSE,
                None,
                "no subjects in phase",
            )
        return Move(MoveKind.NEW_SUBJECT, state.phase, subjects[0], "first subject in phase")

    # Resolve landed signal
    if landed is None:
        # Legacy path: call LLM directly
        landed = _subject_landed(state.current_subject, last_user_text or "", llm)

    if not landed and state.follow_ups_on_current < state.max_follow_ups:
        return Move(MoveKind.FOLLOW_UP, state.phase, state.current_subject, "not landed, follow up")

    # Mark landed (or give up after max follow-ups) and find next subject in phase
    remaining = [
        s for s in subjects_for(state.phase)
        if s.key not in state.subjects_landed and s.key != state.current_subject.key
    ]
    if remaining:
        return Move(MoveKind.NEW_SUBJECT, state.phase, remaining[0], "next subject in phase")

    # Phase done — advance
    nxt = next_phase(state.phase)
    if nxt is None:
        return Move(MoveKind.CLOSE, Phase.CLOSE, None, "arc complete")
    return Move(MoveKind.ADVANCE_PHASE, nxt, None, f"advance {state.phase.value} -> {nxt.value}")


def _subject_landed(subject: Subject, last_user_text: str, llm) -> bool:
    """Ask the LLM whether the user's last answer satisfies the landing criterion.

    Legacy helper — kept for callers that use the 2-LLM-call path.
    The hot path now goes through combined.analyze_turn for 1 call per turn.
    """
    if not last_user_text or len(last_user_text.strip()) < 5:
        return False
    prompt = (
        f"Landing criterion: {subject.landing_criterion}\n"
        f"User just said: {last_user_text!r}\n\n"
        f"Does this answer satisfy the landing criterion? Reply with only 'YES' or 'NO'."
    )
    try:
        resp = llm.ask(history=[{"role": "user", "content": prompt}], max_tokens=5)
        return resp.strip().upper().startswith("YES")
    except Exception:
        return False  # conservative
