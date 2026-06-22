"""Import a CSS file's :root custom properties into a DTCG token tree.

v1 scope: infers `color`, `dimension`, `duration`, `fontFamily`, and `number`
from CSS custom property values. Composite values (box-shadow, gradients,
multi-part typography) are NOT parsed — they are skipped and reported, so the
import is honest about what it covered.

Tokens are emitted flat, preserving the exact CSS variable name (minus `--`) as
the token name with an explicit `$type`. This means `--primary` round-trips back
to `--primary` via export-css, so existing projects adopt without renaming.
"""

import re

_VAR_RE = re.compile(r"--([A-Za-z0-9_-]+)\s*:\s*([^;]+);")
_ROOT_RE = re.compile(r":root\s*\{(.*?)\}", re.DOTALL)
_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_DIM_RE = re.compile(r"^(-?\d*\.?\d+)(px|rem|em)$")
_DUR_RE = re.compile(r"^(-?\d*\.?\d+)(ms|s)$")
_NUM_RE = re.compile(r"^-?\d*\.?\d+$")
_COLOR_FUNCS = (
    "rgb", "rgba", "hsl", "hsla", "hwb", "lab", "lch",
    "oklab", "oklch", "color", "color-mix",
)


def parse_css_vars(css_text):
    """Return {var-name: value} for declarations inside :root (comments stripped)."""
    text = _COMMENT_RE.sub("", css_text)
    out = {}
    for block in _ROOT_RE.findall(text):
        for name, value in _VAR_RE.findall(block):
            out[name] = value.strip()
    return out


def _num(s):
    return int(s) if "." not in s else float(s)


def _is_color(value):
    if value.startswith("#"):
        return True
    head = value.split("(", 1)[0].strip().lower()
    return "(" in value and head in _COLOR_FUNCS


def infer(name, value):
    """Return (type, dtcg_value) or (None, reason) if not importable in v1."""
    if _is_color(value):
        return "color", value
    m = _DIM_RE.match(value)
    if m:
        return "dimension", {"value": _num(m.group(1)), "unit": m.group(2)}
    m = _DUR_RE.match(value)
    if m:
        return "duration", {"value": _num(m.group(1)), "unit": m.group(2)}
    if _NUM_RE.match(value):
        return "number", _num(value)
    # font stack: name signals font, value is comma-list of identifiers, no parens
    if "font" in name.lower() and "(" not in value:
        return "fontFamily", value
    return None, "unrecognized value (composite or unsupported in v1)"


def to_tokens(css_text):
    """Return (tree, skipped) where skipped is a list of (name, value, reason)."""
    tree = {}
    skipped = []
    for name, value in parse_css_vars(css_text).items():
        ttype, payload = infer(name, value)
        if ttype is None:
            skipped.append((name, value, payload))
            continue
        tree[name] = {"$type": ttype, "$value": payload}
    return tree, skipped
