import pytest
from skill_studio.interview.frameworks import load_framework, list_frameworks
from skill_studio.interview.phases import Phase


def test_list_frameworks_includes_forces():
    assert "forces" in list_frameworks()


def test_load_forces_returns_dict():
    fw = load_framework("forces")
    assert isinstance(fw, dict)


def test_forces_has_stance():
    fw = load_framework("forces")
    assert "stance" in fw
    assert fw["stance"].strip()


def test_forces_has_all_phases():
    fw = load_framework("forces")
    phases = fw.get("phases", {})
    for phase in Phase:
        assert phase.value in phases, f"forces.yaml missing phase: {phase.value}"


def test_each_phase_has_at_least_one_question():
    fw = load_framework("forces")
    phases = fw.get("phases", {})
    for phase_key, data in phases.items():
        questions = data.get("questions", [])
        assert len(questions) >= 1, f"Phase {phase_key} has no questions"


def test_load_unknown_framework_raises():
    with pytest.raises(ValueError, match="Unknown framework"):
        load_framework("nonexistent")
