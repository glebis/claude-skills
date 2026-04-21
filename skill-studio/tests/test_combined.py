"""Finding 2: combined.analyze_turn folds extractor + director landing into one LLM call."""
from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.combined import analyze_turn
from skill_studio.interview.subjects import subjects_for
from skill_studio.interview.phases import Phase


def make_design():
    return DesignJSON(meta=Meta(preset="ai-agent"))


def opening_subject():
    return subjects_for(Phase.OPENING)[0]


def test_happy_path_landed_and_patch():
    """Both landed=True and a non-empty patch are returned and applied."""
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"landed": true, "patch": {"hook": "Weekly review drafter"}}'
    landed, patch = analyze_turn(d, opening_subject(), [], llm)
    assert landed is True
    assert patch == {"hook": "Weekly review drafter"}
    assert d.hook == "Weekly review drafter"


def test_landed_only_empty_patch():
    """landed=True with an empty patch works correctly."""
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"landed": true, "patch": {}}'
    landed, patch = analyze_turn(d, opening_subject(), [], llm)
    assert landed is True
    assert patch == {}
    assert d.hook == ""  # unchanged


def test_not_landed_no_patch():
    """landed=False with empty patch — design unchanged."""
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"landed": false, "patch": {}}'
    landed, patch = analyze_turn(d, opening_subject(), [], llm)
    assert landed is False
    assert patch == {}


def test_malformed_llm_json_defaults():
    """Malformed JSON returns safe defaults (False, {}) without raising."""
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = "I cannot decide right now, sorry."
    landed, patch = analyze_turn(d, opening_subject(), [], llm)
    assert landed is False
    assert patch == {}
    assert d.hook == ""  # design unmodified


def test_llm_error_defaults():
    """LLM exception returns safe defaults."""
    d = make_design()
    llm = MagicMock()
    llm.ask.side_effect = RuntimeError("API timeout")
    landed, patch = analyze_turn(d, opening_subject(), [], llm)
    assert landed is False
    assert patch == {}


def test_single_llm_call_per_turn():
    """analyze_turn makes exactly one LLM call — not two."""
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"landed": false, "patch": {}}'
    analyze_turn(d, opening_subject(), [], llm)
    assert llm.ask.call_count == 1
