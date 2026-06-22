"""Collect validation errors over a DTCG token tree (v1 subset)."""

from . import model

ALLOWED_TYPES = {
    "color",
    "dimension",
    "duration",
    "fontFamily",
    "fontWeight",
    "number",
    "typography",
    "shadow",
}


def _detect_cycles(idx):
    errors = []
    for path, entry in idx.items():
        seen = []
        cur = path
        while True:
            node = idx[cur]["node"]
            value = node.get("$value")
            if not model.is_alias(value):
                break
            target = model.alias_target(value)
            if target not in idx:
                break  # dangling alias reported elsewhere
            if target in seen or target == path:
                errors.append(f"circular alias chain starting at {path}")
                break
            seen.append(target)
            cur = target
    return errors


def validate(tree):
    """Return a list of error strings; empty means the tree is valid."""
    idx = model.index(tree)
    errors = []

    for path, entry in idx.items():
        node = entry["node"]
        value = node.get("$value")

        if model.is_alias(value):
            target = model.alias_target(value)
            if target not in idx:
                errors.append(f"{path}: alias target {target} does not exist")

        ttype = model.resolve_type(path, entry, idx)
        if ttype is None:
            errors.append(f"{path}: cannot determine $type")
        elif ttype not in ALLOWED_TYPES:
            errors.append(f"{path}: $type {ttype!r} is not allowed in v1")

    errors.extend(_detect_cycles(idx))
    return errors
