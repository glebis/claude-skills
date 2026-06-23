import copy

from dtokens import merge


def test_override_replaces_whole_token():
    base = {"color": {"brand": {"$type": "color", "$value": "#000", "$description": "old"}}}
    override = {"color": {"brand": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert out["color"]["brand"] == {"$type": "color", "$value": "#fff"}


def test_different_paths_merge():
    base = {"color": {"a": {"$type": "color", "$value": "#000"}}}
    override = {"color": {"b": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert set(out["color"]) == {"a", "b"}


def test_base_token_survives_when_not_overridden():
    base = {"space": {"sm": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}}}}
    override = {"color": {"x": {"$type": "color", "$value": "#fff"}}}
    out = merge.merge(base, override)
    assert out["space"]["sm"]["$value"] == {"value": 8, "unit": "px"}


def test_inputs_not_mutated():
    base = {"color": {"a": {"$type": "color", "$value": "#000"}}}
    override = {"color": {"a": {"$type": "color", "$value": "#fff"}}}
    base_snapshot = copy.deepcopy(base)
    merge.merge(base, override)
    assert base == base_snapshot
