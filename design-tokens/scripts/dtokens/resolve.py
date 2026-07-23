"""Flatten a token tree to concrete values, resolving aliases after merge."""

from . import TokenError
from . import model


def resolve(tree):
    """Return {path: {'type': str, 'value': concrete}} with aliases resolved."""
    idx = model.index(tree)
    resolved = {}
    resolving = set()

    def resolve_one(path):
        if path in resolved:
            return resolved[path]
        if path in resolving:
            raise TokenError(f"circular alias at {path}")
        if path not in idx:
            raise TokenError(f"unknown token {path}")
        resolving.add(path)
        node = idx[path]["node"]
        value = node["$value"]
        if model.is_alias(value):
            target = model.alias_target(value)
            target_resolved = resolve_one(target)
            concrete = target_resolved["value"]
            ttype = node.get("$type") or idx[path]["inherited_type"] or target_resolved["type"]
        else:
            concrete = value
            ttype = model.resolve_type(path, idx[path], idx)
            if ttype is None:
                raise TokenError(f"cannot determine $type for {path}")
        resolving.discard(path)
        resolved[path] = {"type": ttype, "value": concrete}
        # Carry the token's own $description (not the alias target's) so
        # exporters can surface usage notes; key absent when undocumented.
        desc = node.get("$description")
        if desc:
            resolved[path]["description"] = desc
        return resolved[path]

    for path in idx:
        resolve_one(path)
    return resolved
