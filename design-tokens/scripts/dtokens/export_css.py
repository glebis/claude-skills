"""Serialize resolved tokens to CSS custom properties (v1 type rules)."""

from . import TokenError

_TYPO_KEYS = [
    ("fontFamily", "font-family"),
    ("fontSize", "font-size"),
    ("fontWeight", "font-weight"),
    ("lineHeight", "line-height"),
]


def css_var_name(path, suffix=""):
    base = "--" + path.replace(".", "-")
    return f"{base}-{suffix}" if suffix else base


def _dimension(value):
    if not (isinstance(value, dict) and "value" in value and "unit" in value):
        raise TokenError(f"expected {{value, unit}} dimension, got {value!r}")
    return f"{value['value']}{value['unit']}"


def serialize_value(ttype, value):
    if ttype == "color":
        if not isinstance(value, str):
            raise TokenError(f"v1 supports string colors only, got {value!r}")
        return value
    if ttype in ("dimension", "duration"):
        return _dimension(value)
    if ttype == "fontFamily":
        return ", ".join(value) if isinstance(value, list) else str(value)
    if ttype in ("fontWeight", "number"):
        return str(value)
    if ttype == "typography":
        out = {}
        for key, css_key in _TYPO_KEYS:
            if key not in value:
                continue
            sub = value[key]
            if key == "fontSize":
                out[css_key] = _dimension(sub)
            elif key == "fontFamily":
                out[css_key] = ", ".join(sub) if isinstance(sub, list) else str(sub)
            else:
                out[css_key] = str(sub)
        return out
    if ttype == "shadow":
        parts = [
            _dimension(value["offsetX"]),
            _dimension(value["offsetY"]),
            _dimension(value["blur"]),
            _dimension(value["spread"]),
            value["color"],
        ]
        return " ".join(parts)
    raise TokenError(f"unsupported $type for CSS export: {ttype}")


def export_css(resolved, selector=":root"):
    lines = [f"{selector} {{"]
    for path in sorted(resolved):
        entry = resolved[path]
        serialized = serialize_value(entry["type"], entry["value"])
        if isinstance(serialized, dict):
            for css_key, css_val in serialized.items():
                lines.append(f"  {css_var_name(path, css_key)}: {css_val};")
        else:
            lines.append(f"  {css_var_name(path)}: {serialized};")
    lines.append("}")
    return "\n".join(lines) + "\n"
