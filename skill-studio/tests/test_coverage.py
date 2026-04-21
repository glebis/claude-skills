from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.coverage import score_coverage, overall_coverage, next_uncovered_field
from skill_studio.presets import load_preset


def _empty_design(preset="ai-agent"):
    return DesignJSON(meta=Meta(preset=preset))


def test_empty_design_has_zero_coverage():
    design = _empty_design()
    preset = load_preset("ai-agent")
    overall = overall_coverage(design, preset)
    assert overall == 0.0


def test_filled_hook_moves_needle():
    design = _empty_design()
    design.hook = "An agent that drafts weekly reviews"
    preset = load_preset("ai-agent")
    assert overall_coverage(design, preset) > 0.0


def test_next_uncovered_prefers_high_weight_field():
    design = _empty_design()
    preset = load_preset("ai-agent")
    field = next_uncovered_field(design, preset)
    assert field in {"hook", "problem.what_hurts"}


def test_non_empty_string_gets_confidence_1():
    design = _empty_design()
    design.hook = "something"
    scores = score_coverage(design)
    assert scores["hook"] == 1.0
