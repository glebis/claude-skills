import json

import pytest

from dtokens import TokenError
from dtokens import model


def test_load_parses_json(tmp_path):
    p = tmp_path / "x.tokens.json"
    p.write_text(json.dumps({"color": {"blue": {"$type": "color", "$value": "#00f"}}}))
    assert model.load(str(p)) == {"color": {"blue": {"$type": "color", "$value": "#00f"}}}


def test_load_raises_on_bad_json(tmp_path):
    p = tmp_path / "bad.tokens.json"
    p.write_text("{ not json ")
    with pytest.raises(TokenError):
        model.load(str(p))


def test_load_raises_on_missing_file(tmp_path):
    with pytest.raises(TokenError):
        model.load(str(tmp_path / "nope.tokens.json"))


def test_index_finds_leaf_tokens_and_inherits_group_type():
    tree = {
        "color": {
            "$type": "color",
            "blue": {"$value": "#00f"},
            "brand": {"primary": {"$value": "{color.blue}"}},
        },
        "space": {"sm": {"$type": "dimension", "$value": {"value": 8, "unit": "px"}}},
    }
    idx = model.index(tree)
    assert set(idx) == {"color.blue", "color.brand.primary", "space.sm"}
    assert idx["color.blue"]["inherited_type"] == "color"
    assert idx["color.brand.primary"]["inherited_type"] == "color"
    assert idx["space.sm"]["inherited_type"] is None


def test_is_alias_and_target():
    assert model.is_alias("{color.blue}") is True
    assert model.is_alias("#00f") is False
    assert model.is_alias({"value": 8, "unit": "px"}) is False
    assert model.alias_target("{color.brand.primary}") == "color.brand.primary"


def test_resolve_type_direct_inherited_and_via_alias():
    tree = {
        "color": {"$type": "color", "blue": {"$value": "#00f"}},
        "bg": {"main": {"$value": "{color.blue}"}},
    }
    idx = model.index(tree)
    assert model.resolve_type("color.blue", idx["color.blue"], idx) == "color"
    assert model.resolve_type("bg.main", idx["bg.main"], idx) == "color"
