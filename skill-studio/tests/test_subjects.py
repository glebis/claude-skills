from skill_studio.interview.phases import Phase
from skill_studio.interview.subjects import subjects_for, SUBJECTS, Subject


def test_every_phase_has_subjects():
    for phase in Phase:
        subs = subjects_for(phase)
        assert isinstance(subs, list), f"subjects_for({phase}) must return a list"
        assert len(subs) >= 1, f"phase {phase} has no subjects"


def test_subjects_for_opening():
    subs = subjects_for(Phase.OPENING)
    assert any(s.key == "aspiration" for s in subs)


def test_subjects_for_pain_has_two():
    subs = subjects_for(Phase.PAIN)
    assert len(subs) == 2
    keys = {s.key for s in subs}
    assert "current_pain" in keys
    assert "push" in keys


def test_subjects_for_shape_has_two():
    subs = subjects_for(Phase.SHAPE)
    assert len(subs) == 2


def test_subject_is_frozen():
    sub = subjects_for(Phase.OPENING)[0]
    try:
        sub.key = "mutated"
        assert False, "Should have raised"
    except Exception:
        pass


def test_subject_phase_matches_registry_key():
    for phase, subs in SUBJECTS.items():
        for sub in subs:
            assert sub.phase == phase, f"Subject {sub.key} has wrong phase"


def test_landing_criterion_nonempty():
    for phase, subs in SUBJECTS.items():
        for sub in subs:
            assert sub.landing_criterion.strip(), f"Subject {sub.key} has empty landing_criterion"
