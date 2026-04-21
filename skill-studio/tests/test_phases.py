from skill_studio.interview.phases import Phase, ARC, OPTIONAL_PHASES, next_phase


def test_arc_starts_with_opening():
    assert ARC[0] == Phase.OPENING


def test_arc_ends_with_close():
    assert ARC[-1] == Phase.CLOSE


def test_arc_has_eight_phases():
    assert len(ARC) == 8


def test_next_phase_returns_next():
    assert next_phase(Phase.OPENING) == Phase.PAIN
    assert next_phase(Phase.PAIN) == Phase.MOMENT
    assert next_phase(Phase.SHAPE) == Phase.GUARDRAILS


def test_next_phase_at_end_returns_none():
    assert next_phase(Phase.CLOSE) is None


def test_guardrails_is_optional():
    assert Phase.GUARDRAILS in OPTIONAL_PHASES


def test_phase_values_are_strings():
    # Phase is str Enum — usable as dict key without .value
    assert Phase.OPENING == "opening"
    assert Phase.CLOSE == "close"
