"""Regression tests for two bugs found during the email-triage dogfood run."""
from __future__ import annotations
from skill_studio.schema import DesignJSON, Meta, Scenario


def _fresh() -> DesignJSON:
    return DesignJSON(meta=Meta(id="test", preset="custom"))
from skill_studio.interview.merge import deep_merge
from skill_studio.interview.coverage import score_coverage, next_uncovered_field
from skill_studio.presets import load_preset


def test_before_after_aggregated_into_group_score():
    """Bug: before_after.* sub-fields filled, but preset weight on `before_after`
    (not nested) never credited → coverage stuck and it kept being the next target."""
    design = _fresh()
    design.before_after.before_external = "120 emails, no signal"
    design.before_after.before_internal = "dread"
    design.before_after.after_external = "5 priorities surfaced"
    design.before_after.after_internal = "calm"

    scores = score_coverage(design)
    assert scores["before_after"] == 1.0
    # Individual keys still present for fine-grained inspection
    assert scores["before_after.before_external"] == 1.0


def test_before_after_not_selected_when_filled():
    """With life-automation preset and a filled before_after, `next_uncovered_field`
    must not keep returning before_after.*."""
    design = _fresh()
    design.hook = "x"
    design.problem.what_hurts = "x"
    design.problem.cost_today = "x"
    design.jtbd.situation = "x"
    design.jtbd.motivation = "x"
    design.jtbd.outcome = "x"
    design.before_after.before_external = "x"
    design.before_after.before_internal = "x"
    design.before_after.after_external = "x"
    design.before_after.after_internal = "x"
    preset = load_preset("life-automation")
    nxt = next_uncovered_field(design, preset)
    # before_after is now fully scored — should not be picked
    assert nxt != "before_after"


def test_deep_merge_coerces_scenario_dicts():
    """Bug: LLM returned list[dict] for `scenarios: list[Scenario]`; setattr bypassed
    validation and left raw dicts → pydantic serialization warning."""
    design = _fresh()
    patch = {"scenarios": [{"title": "Monday 7:50am", "vignette": "Briefing ready."}]}
    deep_merge(design, patch)
    assert len(design.scenarios) == 1
    assert isinstance(design.scenarios[0], Scenario)
    assert design.scenarios[0].title == "Monday 7:50am"


def test_deep_merge_skips_invalid_scenario_dict():
    """Malformed scenario dicts (missing required fields) should be dropped, not crash."""
    design = _fresh()
    patch = {"scenarios": [{"title": "ok", "vignette": "v"}, {"bogus": "x"}]}
    deep_merge(design, patch)
    assert len(design.scenarios) == 1
    assert design.scenarios[0].title == "ok"
