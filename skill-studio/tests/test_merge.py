"""Test that merge.py exposes deep_merge and behaves correctly."""
from skill_studio.interview.merge import deep_merge
from skill_studio.schema import DesignJSON, Meta


def make_design():
    return DesignJSON(meta=Meta(preset="ai-agent"))


def test_merge_module_exposes_deep_merge():
    """The canonical function lives in merge.py and is importable."""
    assert callable(deep_merge)


def test_deep_merge_top_level_string():
    d = make_design()
    deep_merge(d, {"hook": "Draft reviews"})
    assert d.hook == "Draft reviews"


def test_deep_merge_submodel_dict():
    d = make_design()
    deep_merge(d, {"problem": {"what_hurts": "too slow"}})
    assert d.problem.what_hurts == "too slow"


def test_deep_merge_list_replaces():
    d = make_design()
    deep_merge(d, {"capabilities": ["summarise", "tag"]})
    assert d.capabilities == ["summarise", "tag"]


def test_deep_merge_ignores_unknown_keys():
    d = make_design()
    deep_merge(d, {"no_such_field": "boom"})
    assert not hasattr(d, "no_such_field")
