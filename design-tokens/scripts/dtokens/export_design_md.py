"""Emit a Google-Labs DESIGN.md (alpha) from resolved DTCG tokens.

DESIGN.md (https://github.com/google-labs-code/design.md) is a single file with
YAML frontmatter (machine-readable tokens) + a markdown body (human rationale).
It is the agent-facing artifact that Claude Code / Cursor / v0 read.

Mapping from our resolved DTCG tokens ({path: {type, value}}) to DESIGN.md:

| our $type   | our top-level group        | DESIGN.md home | transform                         |
|-------------|----------------------------|----------------|-----------------------------------|
| color       | any                        | colors         | hex string verbatim               |
| typography  | any                        | typography     | fontSize/letterSpacing -> "Npx"   |
| dimension   | space / spacing            | spacing        | "{value}{unit}"                   |
| dimension   | radius / rounded / corner  | rounded        | "{value}{unit}"                   |
| dimension   | (other)                    | spacing        | "{value}{unit}"                   |

Token names are flattened: drop the top-level group segment, join the rest with
"-" (e.g. color.action.primary -> action-primary; type.body -> body).

Other v1 types (duration, number, fontFamily, fontWeight, shadow) have no
frontmatter home in DESIGN.md alpha and are omitted (noted in the Overview).
This naming/bucketing is a skill convention layered on the DESIGN.md schema.
"""

_VERSION = "alpha"
_SPACING_GROUPS = {"space", "spacing"}
_ROUNDED_GROUPS = {"radius", "rounded", "corner", "corners"}


def _flat_name(path):
    """Drop the top-level group, join the rest with '-'."""
    parts = path.split(".")
    return "-".join(parts[1:]) if len(parts) > 1 else path


def _top_group(path):
    return path.split(".")[0]


def _dim_str(value):
    """Render a dimension: {value, unit} -> 'Npx'; number -> 'N'; str -> str."""
    if isinstance(value, dict) and "value" in value and "unit" in value:
        return f"{value['value']}{value['unit']}"
    return str(value)


def _typography(value):
    """Map a DTCG typography composite to DESIGN.md typography keys."""
    out = {}
    if "fontFamily" in value:
        fam = value["fontFamily"]
        out["fontFamily"] = ", ".join(fam) if isinstance(fam, list) else str(fam)
    if "fontSize" in value:
        out["fontSize"] = _dim_str(value["fontSize"])
    if "fontWeight" in value:
        out["fontWeight"] = str(value["fontWeight"])
    if "lineHeight" in value:
        lh = value["lineHeight"]
        out["lineHeight"] = lh if isinstance(lh, (int, float)) else _dim_str(lh)
    if "letterSpacing" in value:
        out["letterSpacing"] = _dim_str(value["letterSpacing"])
    return out


def bucketize(resolved):
    """Split resolved tokens into DESIGN.md frontmatter buckets.

    Returns (colors, typography, rounded, spacing, skipped) where each of the
    first four is a name->value map and skipped is a list of (path, type).
    """
    colors, typography, rounded, spacing, skipped = {}, {}, {}, {}, []
    for path in sorted(resolved):
        entry = resolved[path]
        ttype, value = entry["type"], entry["value"]
        name = _flat_name(path)
        if ttype == "color":
            colors[name] = value
        elif ttype == "typography":
            typography[name] = _typography(value)
        elif ttype == "dimension":
            group = _top_group(path)
            if group in _ROUNDED_GROUPS:
                rounded[name] = _dim_str(value)
            else:
                spacing[name] = _dim_str(value)
        else:
            skipped.append((path, ttype))
    return colors, typography, rounded, spacing, skipped


# --- minimal, dependency-free YAML emission for our known shapes -------------

def _yq(s):
    """Quote a scalar string for YAML (always-quote keeps hex/units safe)."""
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _emit_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _yq(value)


def _frontmatter(name, description, colors, typography, rounded, spacing):
    lines = ["---", f"version: {_VERSION}", f"name: {_yq(name)}"]
    if description:
        lines.append(f"description: {_yq(description)}")
    if colors:
        lines.append("colors:")
        for k in colors:
            lines.append(f"  {k}: {_yq(colors[k])}")
    if typography:
        lines.append("typography:")
        for k in typography:
            lines.append(f"  {k}:")
            for prop, val in typography[k].items():
                lines.append(f"    {prop}: {_emit_scalar(val)}")
    if rounded:
        lines.append("rounded:")
        for k in rounded:
            lines.append(f"  {k}: {_yq(rounded[k])}")
    if spacing:
        lines.append("spacing:")
        for k in spacing:
            lines.append(f"  {k}: {_yq(spacing[k])}")
    lines.append("---")
    return lines


def _body(name, description, colors, typography, rounded, spacing, skipped):
    lines = ["", f"# {name}", "", "## Overview", ""]
    overview = f"{name} design system. Generated from design tokens."
    if description:
        overview = f"{description}"
    if skipped:
        kinds = ", ".join(sorted({t for _, t in skipped}))
        overview += f" (Token types without a DESIGN.md home are omitted from frontmatter: {kinds}.)"
    lines.append(overview)

    if colors:
        lines += ["", "## Colors", ""]
        for k, v in colors.items():
            lines.append(f"- **{k}** (`{v}`)")
    if typography:
        lines += ["", "## Typography", ""]
        for k, v in typography.items():
            fam = v.get("fontFamily", "")
            size = v.get("fontSize", "")
            lh = v.get("lineHeight", "")
            weight = v.get("fontWeight", "")
            lines.append(f"- **{k}** — {fam} {size}/{lh} {weight}".rstrip())
    if spacing:
        lines += ["", "## Layout", ""]
        scale = ", ".join(f"{k} {v}" for k, v in spacing.items())
        lines.append(f"Spacing scale: {scale}.")
    if rounded:
        lines += ["", "## Shapes", ""]
        scale = ", ".join(f"{k} {v}" for k, v in rounded.items())
        lines.append(f"Corner radii: {scale}.")
    return lines


def to_design_md(resolved, name, description=None):
    """Render a complete DESIGN.md string from resolved DTCG tokens."""
    colors, typography, rounded, spacing, skipped = bucketize(resolved)
    lines = _frontmatter(name, description, colors, typography, rounded, spacing)
    lines += _body(name, description, colors, typography, rounded, spacing, skipped)
    return "\n".join(lines) + "\n"
