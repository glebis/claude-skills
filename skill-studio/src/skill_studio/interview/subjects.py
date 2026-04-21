from __future__ import annotations
from dataclasses import dataclass
from skill_studio.interview.phases import Phase


@dataclass(frozen=True)
class Subject:
    key: str
    label: str
    phase: Phase
    landing_criterion: str  # plain-English description for LLM to judge


SUBJECTS: dict[Phase, list[Subject]] = {
    Phase.OPENING: [
        Subject(
            "aspiration",
            "what you're trying to change",
            Phase.OPENING,
            "user has articulated a clear direction or goal in their own words",
        ),
    ],
    Phase.PAIN: [
        Subject(
            "current_pain",
            "what hurts about the current approach",
            Phase.PAIN,
            "user has named a specific, visceral dissatisfaction with how things are now",
        ),
        Subject(
            "push",
            "what's driving them to look for something new",
            Phase.PAIN,
            "user has explained why now, or why they're seeking change",
        ),
    ],
    Phase.MOMENT: [
        Subject(
            "vivid_scene",
            "a specific recent instance of the problem",
            Phase.MOMENT,
            "user has described a concrete moment with time, place, and what happened",
        ),
    ],
    Phase.COST: [
        Subject(
            "cost_today",
            "what this costs them — time, money, energy, relationships",
            Phase.COST,
            "user has quantified or vividly described the cost",
        ),
    ],
    Phase.AFTER: [
        Subject(
            "good_looks_like",
            "what better would feel or look like",
            Phase.AFTER,
            "user has painted a picture of success, even roughly",
        ),
    ],
    Phase.SHAPE: [
        Subject(
            "trigger",
            "when the tool should kick in",
            Phase.SHAPE,
            "user has specified a clear trigger or invocation pattern",
        ),
        Subject(
            "capabilities",
            "what the tool needs to do",
            Phase.SHAPE,
            "user has named the core actions the tool must perform",
        ),
    ],
    Phase.GUARDRAILS: [
        Subject(
            "must_not",
            "what the tool must never do",
            Phase.GUARDRAILS,
            "user has named at least one boundary or constraint",
        ),
    ],
    Phase.CLOSE: [
        Subject(
            "synthesis",
            "the user sees themselves in the design",
            Phase.CLOSE,
            "user confirms the synthesis resonates",
        ),
    ],
}


def subjects_for(phase: Phase) -> list[Subject]:
    return SUBJECTS.get(phase, [])
