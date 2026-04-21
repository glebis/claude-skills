from skill_studio.presets import load_preset, list_presets


def test_list_returns_all_four():
    names = list_presets()
    assert set(names) == {"ai-agent", "life-automation", "knowledge-work", "custom"}


def test_load_ai_agent_has_expected_fields():
    p = load_preset("ai-agent")
    assert p.name == "ai-agent"
    assert p.default_jtbd_frame == "forces"
    assert p.field_weights["trigger"] > p.field_weights["concept_imagery"]["metaphor"]
    assert p.opening_question


def test_load_unknown_raises():
    import pytest
    with pytest.raises(ValueError):
        load_preset("nope")
