"""Distil resolved DTCG tokens into a tool-agnostic brand summary.

This is the shared front half of the prompt door: it turns the resolved
{path: {type, value}} map into a structured, human-legible description of the
brand (palette with inferred roles, font families, type specimens, shape
language). Each downstream target (gpt-image-2, nano-banana, tufte-report)
then phrases that summary in its own idiom.

NOTE: role inference and the whole notion of "brand summary" are a SKILL
CONVENTION layered on top of DTCG — DTCG itself assigns no semantic roles to
colors. Roles are guessed from token names purely as a generation aid.
"""

# Role inference: ordered (first match wins) keyword -> role. Names are matched
# case-insensitively against the flattened token path. This is a heuristic to
# help phrase prompts; it is never presented as DTCG semantics.
_ROLE_RULES = [
    ("background", ("background", "bg", "surface", "canvas", "base")),
    ("text", ("ink", "text", "foreground", "fg", "body", "content")),
    ("primary", ("primary", "brand", "action", "accent-1", "main")),
    ("accent", ("accent", "secondary", "highlight", "pop")),
    ("success", ("success", "positive", "ok", "green")),
    ("warning", ("warning", "caution", "warn", "amber", "yellow")),
    ("danger", ("danger", "error", "negative", "destructive", "red")),
    ("muted", ("muted", "subtle", "neutral", "gray", "grey", "slate")),
]


# SKILL CONVENTION: optional brand-style block under $extensions at file root.
# Unknown keys are carried through untouched (DTCG requires tools to preserve
# extensions they don't understand); consumers pick the keys they know.
BRAND_EXT_KEY = "community.design-tokens.brand"


def extract_brand(tree):
    """Return the brand-style extension block from a raw token tree, or {}."""
    ext = tree.get("$extensions")
    if isinstance(ext, dict):
        brand = ext.get(BRAND_EXT_KEY)
        if isinstance(brand, dict):
            return brand
    return {}


def _infer_role(name):
    low = name.lower()
    # "on-accent"/"on-primary" etc. are contrast counterparts (ink placed ON a
    # fill), not the fill's role itself — never promote them to that role.
    if low.startswith("on-") or low.startswith("on_"):
        return None
    for role, needles in _ROLE_RULES:
        if any(n in low for n in needles):
            return role
    return None


def _flat_name(path):
    parts = path.split(".")
    return "-".join(parts[1:]) if len(parts) > 1 else path


def _dim_str(value):
    if isinstance(value, dict) and "value" in value and "unit" in value:
        return f"{value['value']}{value['unit']}"
    return str(value)


def summarize(resolved, brand=None):
    """Return a dict describing the brand for prompt synthesis.

    Keys:
      name_hint  -> None (caller supplies a name)
      colors     -> [{name, hex, role}]  (role may be None)
      fonts      -> [str]                 (unique family names, in first-seen order)
      type       -> [{name, family, size, weight, line_height}]
      radii      -> [str]                 (e.g. "4px", "8px")
      spacing    -> [str]
      shape      -> "sharp" | "soft" | "rounded" | "pill" | None  (from max radius)
      brand      -> $extensions brand-style block (mood, imageryStyle, voice,
                    subjects, avoid, negativePrompt), {} if absent
    """
    colors, fonts, type_styles, radii, spacing = [], [], [], [], []
    seen_fonts = set()

    for path in sorted(resolved):
        entry = resolved[path]
        ttype, value = entry["type"], entry["value"]
        name = _flat_name(path)
        if ttype == "color":
            colors.append({"name": name, "hex": value, "role": _infer_role(name)})
        elif ttype == "fontFamily":
            fams = value if isinstance(value, list) else [value]
            for fam in fams:
                if fam not in seen_fonts:
                    seen_fonts.add(fam)
                    fonts.append(fam)
        elif ttype == "typography":
            fam = value.get("fontFamily")
            if isinstance(fam, list):
                fam = fam[0] if fam else None
            if fam and fam not in seen_fonts:
                seen_fonts.add(fam)
                fonts.append(fam)
            type_styles.append({
                "name": name,
                "family": fam,
                "size": _dim_str(value["fontSize"]) if "fontSize" in value else None,
                "weight": value.get("fontWeight"),
                "line_height": value.get("lineHeight"),
            })
        elif ttype == "dimension":
            group = path.split(".")[0].lower()
            if group in ("radius", "rounded", "corner", "corners"):
                radii.append(_dim_str(value))
            else:
                spacing.append(_dim_str(value))

    return {
        "name_hint": None,
        "colors": colors,
        "fonts": fonts,
        "type": type_styles,
        "radii": radii,
        "spacing": spacing,
        "shape": _shape_language(radii),
        "brand": brand or {},
    }


def _shape_language(radii):
    """Map the largest corner radius (in px) to a coarse shape descriptor."""
    pxs = []
    for r in radii:
        try:
            pxs.append(float(str(r).rstrip("pxremem%").strip() or 0))
        except ValueError:
            continue
    if not pxs:
        return None
    m = max(pxs)
    if m == 0:
        return "sharp"
    if m <= 6:
        return "soft"
    if m <= 16:
        return "rounded"
    return "pill"
