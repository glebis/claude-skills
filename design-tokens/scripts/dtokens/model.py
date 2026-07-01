"""Loading, indexing and type-resolution over a DTCG token tree.

A *token* is a dict containing the key ``$value``. A *group* is a dict without it.
Keys beginning with ``$`` are metadata, never children.
"""

import json
import re

from . import TokenError

_ALIAS_RE = re.compile(r"^\{([^}]+)\}$")


def load(path):
    """Parse a token file. Raise TokenError on missing file or invalid JSON."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise TokenError(f"token file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise TokenError(f"invalid JSON in {path}: {exc}") from exc


def is_alias(value):
    """True if value is a whole-value alias string like ``{group.token}``."""
    return isinstance(value, str) and _ALIAS_RE.match(value) is not None


def alias_target(value):
    """Return the dotted path inside a ``{...}`` alias string."""
    m = _ALIAS_RE.match(value)
    if not m:
        raise TokenError(f"not an alias: {value!r}")
    return m.group(1)


def index(tree):
    """Map dotted path -> {'node': token_dict, 'inherited_type': str|None}."""
    out = {}

    def walk(node, prefix, inherited_type):
        local_type = node.get("$type", inherited_type)
        for key, child in node.items():
            if key.startswith("$"):
                continue
            if not isinstance(child, dict):
                continue
            path = f"{prefix}.{key}" if prefix else key
            if "$value" in child:
                out[path] = {"node": child, "inherited_type": inherited_type}
            else:
                walk(child, path, child.get("$type", local_type))

    walk(tree, "", None)
    return out


def resolve_type(path, entry, idx, _seen=None):
    """Resolve a token's $type: declared -> inherited -> alias target's type."""
    node = entry["node"]
    if "$type" in node:
        return node["$type"]
    if entry["inherited_type"] is not None:
        return entry["inherited_type"]
    value = node.get("$value")
    if is_alias(value):
        seen = _seen or set()
        if path in seen:
            return None
        seen.add(path)
        target = alias_target(value)
        if target in idx:
            return resolve_type(target, idx[target], idx, seen)
    return None
