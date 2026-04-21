from __future__ import annotations
from enum import Enum


class Phase(str, Enum):
    OPENING = "opening"
    PAIN = "pain"
    MOMENT = "moment"
    COST = "cost"
    AFTER = "after"
    SHAPE = "shape"
    GUARDRAILS = "guardrails"
    CLOSE = "close"


ARC = [
    Phase.OPENING,
    Phase.PAIN,
    Phase.MOMENT,
    Phase.COST,
    Phase.AFTER,
    Phase.SHAPE,
    Phase.GUARDRAILS,
    Phase.CLOSE,
]

# Phases that can be skipped if depth-mode says so
OPTIONAL_PHASES = {Phase.GUARDRAILS}


def next_phase(current: Phase) -> Phase | None:
    idx = ARC.index(current)
    if idx + 1 >= len(ARC):
        return None
    return ARC[idx + 1]
