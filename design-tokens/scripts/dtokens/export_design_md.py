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


def _descriptions(resolved):
    """Map flat name -> $description for color tokens that carry one."""
    out = {}
    for path, entry in resolved.items():
        if entry["type"] == "color" and entry.get("description"):
            out[_flat_name(path)] = entry["description"]
    return out


def _var_names(resolved):
    """Per-bucket maps flat name -> CSS custom-property name (matches export_css).

    Buckets are keyed separately because flat names can collide across
    top-level groups (space.sm and radius.sm both flatten to 'sm').
    """
    color_vars, spacing_vars = {}, {}
    for path, entry in resolved.items():
        var = "--" + path.replace(".", "-")
        if entry["type"] == "color":
            color_vars[_flat_name(path)] = var
        elif entry["type"] == "dimension" and _top_group(path) not in _ROUNDED_GROUPS:
            spacing_vars[_flat_name(path)] = var
    return color_vars, spacing_vars


def _md_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def _table(header, rows):
    lines = ["| " + " | ".join(header) + " |",
             "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(
            "—" if c is None or c == "" else _md_cell(c) for c in row) + " |")
    return lines


def _body(name, description, colors, typography, rounded, spacing, skipped,
          descs=None, color_vars=None, spacing_vars=None):
    descs = descs or {}
    color_vars = color_vars or {}
    spacing_vars = spacing_vars or {}
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
        lines += _table(
            ["Name", "Value", "Token", "Role"],
            [(k, f"`{v}`", f"`{color_vars.get(k, '')}`" if color_vars.get(k) else "",
              descs.get(k, "")) for k, v in colors.items()],
        )
    if typography:
        lines += ["", "## Typography", ""]
        lines += _table(
            ["Role", "Family", "Size", "Weight", "Line Height", "Letter Spacing"],
            [(k, v.get("fontFamily", ""), v.get("fontSize", ""),
              v.get("fontWeight", ""), v.get("lineHeight", ""),
              v.get("letterSpacing", "")) for k, v in typography.items()],
        )
    if spacing:
        lines += ["", "## Spacing", ""]
        lines += _table(
            ["Name", "Value", "Token"],
            [(k, v, f"`{spacing_vars.get(k, '')}`" if spacing_vars.get(k) else "")
             for k, v in spacing.items()],
        )
    if rounded:
        lines += ["", "## Border Radius", ""]
        lines += _table(["Name", "Value"], list(rounded.items()))
    return lines


def _motion_table(resolved):
    """Rows for duration tokens: (name, value, token, description)."""
    rows = []
    for path in sorted(resolved):
        entry = resolved[path]
        if entry["type"] != "duration":
            continue
        rows.append((_flat_name(path), _dim_str(entry["value"]),
                     f"`--{path.replace('.', '-')}`",
                     entry.get("description", "")))
    return rows


# --- rich body (SKILL CONVENTION, opt-in) ------------------------------------
# Rendered from optional keys in the $extensions brand block:
#   essence (prose), components [{name, role, spec}],
#   animations [{name, role, spec}] (spec may embed code fences), dos [str], donts [str],
#   surfaces [{level, name, value, purpose}], elevation {label: note},
#   imagery (prose; falls back to imageryStyle), layout (prose),
#   similarBrands [{name, note} | str].
# These sections are NOT part of the Google-Labs DESIGN.md alpha format.

_RICH_NOTE = ("> Note: sections below the token tables extend the Google-Labs "
              "DESIGN.md alpha format (skill convention). The YAML frontmatter "
              "above remains standard.")


def _rich_sections(brand, resolved):
    lines = ["", _RICH_NOTE]
    if brand.get("essence"):
        lines += ["", "## Essence", "", str(brand["essence"])]
    comps = brand.get("components") or []
    if comps:
        lines += ["", "## Components"]
        for c in comps:
            lines += ["", f"### {c.get('name', 'Component')}"]
            if c.get("role"):
                lines.append(f"**Role:** {c['role']}")
            if c.get("spec"):
                lines += ["", str(c["spec"])]
    anims = brand.get("animations") or []
    if anims:
        lines += ["", "## Animation Recipes"]
        for a in anims:
            lines += ["", f"### {a.get('name', 'Animation')}"]
            if a.get("role"):
                lines.append(f"**Role:** {a['role']}")
            if a.get("spec"):
                lines += ["", str(a["spec"])]
    dos, donts = brand.get("dos") or [], brand.get("donts") or []
    if dos or donts:
        lines += ["", "## Do's and Don'ts"]
        if dos:
            lines += ["", "### Do", ""] + [f"- {d}" for d in dos]
        if donts:
            lines += ["", "### Don't", ""] + [f"- {d}" for d in donts]
    surfaces = brand.get("surfaces") or []
    if surfaces:
        lines += ["", "## Surfaces", ""]
        lines += _table(
            ["Level", "Name", "Value", "Purpose"],
            [(s.get("level", ""), s.get("name", ""),
              f"`{s.get('value', '')}`" if s.get("value") else "",
              s.get("purpose", "")) for s in surfaces],
        )
    elevation = brand.get("elevation") or {}
    if elevation:
        lines += ["", "## Elevation", ""]
        lines += [f"- **{k}:** `{v}`" for k, v in elevation.items()]
    imagery = brand.get("imagery") or brand.get("imageryStyle")
    if imagery:
        lines += ["", "## Imagery", "", str(imagery)]
    if brand.get("layout"):
        lines += ["", "## Layout", "", str(brand["layout"])]
    similar = brand.get("similarBrands") or []
    if similar:
        lines += ["", "## Similar Brands", ""]
        for s in similar:
            if isinstance(s, dict):
                lines.append(f"- **{s.get('name', '')}** — {s.get('note', '')}".rstrip(" —"))
            else:
                lines.append(f"- {s}")
    # Quick Start: the same :root block export-css emits, inlined for agents.
    from . import export_css as _css
    lines += ["", "## Quick Start", "", "### CSS Custom Properties", "",
              "```css", _css.export_css(resolved).rstrip("\n"), "```"]
    return lines


def to_design_md(resolved, name, description=None, brand=None, rich=False):
    """Render a complete DESIGN.md string from resolved DTCG tokens.

    With rich=True, append skill-convention sections (components, do's/don'ts,
    surfaces, imagery, layout, similar brands, Quick Start CSS) sourced from
    the $extensions brand block — the result is no longer plain Labs alpha.
    """
    colors, typography, rounded, spacing, skipped = bucketize(resolved)
    lines = _frontmatter(name, description, colors, typography, rounded, spacing)
    color_vars, spacing_vars = _var_names(resolved)
    lines += _body(name, description, colors, typography, rounded, spacing, skipped,
                   descs=_descriptions(resolved),
                   color_vars=color_vars, spacing_vars=spacing_vars)
    # Motion: duration tokens have no frontmatter home in DESIGN.md alpha, but
    # the free-form body can carry them as a table (with $description as Role).
    motion = _motion_table(resolved)
    if motion:
        lines += ["", "## Motion", ""]
        lines += _table(["Name", "Value", "Token", "Role"], motion)
    if rich:
        lines += _rich_sections(brand or {}, resolved)
    return "\n".join(lines) + "\n"
