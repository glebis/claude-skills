from unittest.mock import MagicMock
from skill_studio.schema import DesignJSON, Meta
from skill_studio.interview.extractor import extract_and_apply, _deep_merge


# ---------------------------------------------------------------------------
# _deep_merge tests (mirrors updater behaviour — must stay compatible)
# ---------------------------------------------------------------------------

def make_design():
    return DesignJSON(meta=Meta(preset="ai-agent"))


def test_deep_merge_sets_top_level_string():
    d = make_design()
    _deep_merge(d, {"hook": "Draft reviews"})
    assert d.hook == "Draft reviews"


def test_deep_merge_sets_submodel_dict():
    d = make_design()
    _deep_merge(d, {"problem": {"what_hurts": "too slow", "cost_today": "1h/day"}})
    assert d.problem.what_hurts == "too slow"
    assert d.problem.cost_today == "1h/day"


def test_deep_merge_string_for_submodel_maps_to_candidate():
    d = make_design()
    _deep_merge(d, {"problem": "it all takes too long"})
    assert d.problem.what_hurts == "it all takes too long"


def test_deep_merge_list_replaces():
    d = make_design()
    _deep_merge(d, {"capabilities": ["summarise", "tag"]})
    assert d.capabilities == ["summarise", "tag"]


def test_deep_merge_ignores_unknown_keys():
    d = make_design()
    _deep_merge(d, {"nonexistent_key": "boom"})
    # no error, no attribute created
    assert not hasattr(d, "nonexistent_key")


def test_deep_merge_trigger_string_maps_to_detail():
    d = make_design()
    _deep_merge(d, {"trigger": "every morning at 9"})
    assert d.trigger.detail == "every morning at 9"


# ---------------------------------------------------------------------------
# extract_and_apply tests
# ---------------------------------------------------------------------------

def test_extract_applies_patch_to_design():
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"hook": "Weekly review drafter"}'
    tail = [{"role": "user", "text": "I want to write weekly reviews automatically"}]
    patch = extract_and_apply(d, tail, llm)
    assert patch == {"hook": "Weekly review drafter"}
    assert d.hook == "Weekly review drafter"


def test_extract_returns_empty_on_no_json():
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = "Sorry, I cannot extract anything."
    patch = extract_and_apply(d, [], llm)
    assert patch == {}


def test_extract_returns_empty_on_llm_error():
    d = make_design()
    llm = MagicMock()
    llm.ask.side_effect = RuntimeError("API error")
    patch = extract_and_apply(d, [], llm)
    assert patch == {}


def test_extract_returns_empty_on_bad_json():
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = '{"hook": broken json}'
    patch = extract_and_apply(d, [], llm)
    assert patch == {}


def test_extract_uses_last_six_turns():
    d = make_design()
    llm = MagicMock()
    llm.ask.return_value = "{}"
    tail = [{"role": "user", "text": f"msg {i}"} for i in range(10)]
    extract_and_apply(d, tail, llm)
    call_kwargs = llm.ask.call_args
    history = call_kwargs.kwargs.get("history") or call_kwargs.args[0]
    content = history[-1]["content"]
    # Only last 6 turns should appear
    assert "msg 9" in content
    assert "msg 3" not in content  # tail[-6:] starts at index 4 (msgs 4-9)
