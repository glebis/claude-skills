from dtokens import brand_summary


def test_infers_color_roles_from_names():
    resolved = {
        "color.action-primary": {"type": "color", "value": "#1A73E8"},
        "color.ink-900": {"type": "color", "value": "#0B0B0C"},
        "color.surface": {"type": "color", "value": "#FFFFFF"},
        "color.danger": {"type": "color", "value": "#E5484D"},
    }
    s = brand_summary.summarize(resolved)
    roles = {c["name"]: c["role"] for c in s["colors"]}
    assert roles["action-primary"] == "primary"
    assert roles["ink-900"] == "text"
    assert roles["surface"] == "background"
    assert roles["danger"] == "danger"


def test_collects_fonts_from_typography_and_fontfamily():
    resolved = {
        "type.body": {"type": "typography", "value": {"fontFamily": "Inter", "fontSize": {"value": 16, "unit": "px"}, "fontWeight": 400}},
        "font.display": {"type": "fontFamily", "value": ["Fraunces", "Georgia"]},
    }
    s = brand_summary.summarize(resolved)
    # Order is by sorted token path: font.display before type.body.
    assert s["fonts"] == ["Fraunces", "Georgia", "Inter"]
    assert s["type"][0]["family"] == "Inter"
    assert s["type"][0]["size"] == "16px"


def test_shape_language_from_radius():
    assert brand_summary._shape_language(["0px"]) == "sharp"
    assert brand_summary._shape_language(["4px"]) == "soft"
    assert brand_summary._shape_language(["12px"]) == "rounded"
    assert brand_summary._shape_language(["999px"]) == "pill"
    assert brand_summary._shape_language([]) is None


def test_spacing_vs_radii_split_by_group():
    resolved = {
        "space.md": {"type": "dimension", "value": {"value": 16, "unit": "px"}},
        "radius.lg": {"type": "dimension", "value": {"value": 12, "unit": "px"}},
    }
    s = brand_summary.summarize(resolved)
    assert s["spacing"] == ["16px"]
    assert s["radii"] == ["12px"]
    assert s["shape"] == "rounded"
