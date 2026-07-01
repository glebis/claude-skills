from dtokens import validate


def test_valid_tree_returns_no_errors():
    tree = {
        "color": {
            "$type": "color",
            "blue": {"$value": "#00f"},
            "brand": {"$value": "{color.blue}"},
        }
    }
    assert validate.validate(tree) == []


def test_unknown_type_is_reported():
    tree = {"x": {"$type": "banana", "$value": "1"}}
    errors = validate.validate(tree)
    assert any("banana" in e and "x" in e for e in errors)


def test_undeterminable_type_is_reported():
    tree = {"x": {"$value": "whatever"}}
    errors = validate.validate(tree)
    assert any("type" in e.lower() and "x" in e for e in errors)


def test_dangling_alias_is_reported():
    tree = {"a": {"$type": "color", "$value": "{color.missing}"}}
    errors = validate.validate(tree)
    assert any("color.missing" in e for e in errors)


def test_circular_alias_is_reported():
    tree = {
        "a": {"$type": "color", "$value": "{b}"},
        "b": {"$type": "color", "$value": "{a}"},
    }
    errors = validate.validate(tree)
    assert any("circular" in e.lower() for e in errors)
