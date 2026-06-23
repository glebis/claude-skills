import pytest

from dtokens import TokenError
from dtokens import resolve


def test_resolves_direct_values():
    tree = {"color": {"$type": "color", "blue": {"$value": "#00f"}}}
    out = resolve.resolve(tree)
    assert out["color.blue"] == {"type": "color", "value": "#00f"}


def test_resolves_alias_chain_and_inherits_type():
    tree = {
        "color": {"$type": "color", "blue": {"$value": "#00f"}},
        "action": {"primary": {"$value": "{color.blue}"}},
        "button": {"bg": {"$value": "{action.primary}"}},
    }
    out = resolve.resolve(tree)
    assert out["button.bg"] == {"type": "color", "value": "#00f"}


def test_circular_alias_raises():
    tree = {
        "a": {"$type": "color", "$value": "{b}"},
        "b": {"$type": "color", "$value": "{a}"},
    }
    with pytest.raises(TokenError):
        resolve.resolve(tree)


def test_dangling_alias_raises():
    tree = {"a": {"$type": "color", "$value": "{nope}"}}
    with pytest.raises(TokenError):
        resolve.resolve(tree)
