import pathlib

from dtokens import export_design_md, model, resolve

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_bucketize_splits_by_type_and_group():
    resolved = {
        "color.brand": {"type": "color", "value": "#1A73E8"},
        "space.sm": {"type": "dimension", "value": {"value": 8, "unit": "px"}},
        "radius.sm": {"type": "dimension", "value": {"value": 4, "unit": "px"}},
    }
    colors, typography, rounded, spacing, skipped = export_design_md.bucketize(resolved)
    assert colors == {"brand": "#1A73E8"}
    assert spacing == {"sm": "8px"}
    assert rounded == {"sm": "4px"}
    assert typography == {} and skipped == []


def test_flat_name_drops_top_group():
    assert export_design_md._flat_name("color.action.primary") == "action-primary"
    assert export_design_md._flat_name("type.body") == "body"
    assert export_design_md._flat_name("solo") == "solo"


def test_non_design_md_types_are_skipped():
    resolved = {"motion.fast": {"type": "duration", "value": {"value": 200, "unit": "ms"}}}
    colors, typography, rounded, spacing, skipped = export_design_md.bucketize(resolved)
    assert skipped == [("motion.fast", "duration")]
    assert not (colors or typography or rounded or spacing)


def test_colors_are_quoted_in_frontmatter():
    out = export_design_md.to_design_md(
        {"color.brand": {"type": "color", "value": "#1A73E8"}}, name="X"
    )
    assert 'brand: "#1A73E8"' in out  # hex must be quoted (YAML comment otherwise)


def test_golden_design_md_matches_fixture():
    tree = model.load(str(FIXTURES / "design-md-source.tokens.json"))
    resolved = resolve.resolve(tree)
    out = export_design_md.to_design_md(resolved, name="Test Brand")
    expected = (FIXTURES / "expected.DESIGN.md").read_text()
    assert out == expected


def test_color_description_becomes_role_column():
    resolved = {"color.brand": {"type": "color", "value": "#1A73E8",
                                "description": "Primary CTA only"}}
    out = export_design_md.to_design_md(resolved, name="X")
    assert "| brand | `#1A73E8` | `--color-brand` | Primary CTA only |" in out


def test_spacing_and_radius_vars_do_not_collide():
    resolved = {
        "space.sm": {"type": "dimension", "value": {"value": 8, "unit": "px"}},
        "radius.sm": {"type": "dimension", "value": {"value": 4, "unit": "px"}},
    }
    out = export_design_md.to_design_md(resolved, name="X")
    assert "| sm | 8px | `--space-sm` |" in out
    assert "--radius-sm" not in out.split("## Spacing")[1].split("## Border Radius")[0]


def test_rich_mode_renders_brand_sections_and_quick_start():
    resolved = {"color.brand": {"type": "color", "value": "#1A73E8"}}
    brand = {
        "essence": "Bold and blue.",
        "components": [{"name": "Pill Button", "role": "Primary action",
                        "spec": "1px border, 100px radius."}],
        "dos": ["Use blue sparingly."],
        "donts": ["No drop shadows."],
        "surfaces": [{"level": 0, "name": "Canvas", "value": "#fff", "purpose": "Page bg"}],
        "similarBrands": [{"name": "Linear", "note": "dark accent"}],
    }
    out = export_design_md.to_design_md(resolved, name="X", brand=brand, rich=True)
    assert "## Essence" in out and "### Pill Button" in out
    assert "## Do's and Don'ts" in out and "- No drop shadows." in out
    assert "| 0 | Canvas | `#fff` | Page bg |" in out
    assert "## Quick Start" in out and "--color-brand: #1A73E8;" in out
    assert "skill convention" in out  # non-standard marker note


def test_default_output_has_no_rich_sections():
    resolved = {"color.brand": {"type": "color", "value": "#1A73E8"}}
    out = export_design_md.to_design_md(resolved, name="X")
    assert "## Quick Start" not in out and "skill convention" not in out


def test_duration_tokens_render_as_motion_table():
    resolved = {"motion.micro": {"type": "duration",
                                 "value": {"value": 200, "unit": "ms"},
                                 "description": "Hover shifts"}}
    out = export_design_md.to_design_md(resolved, name="X")
    assert "## Motion" in out
    assert "| micro | 200ms | `--motion-micro` | Hover shifts |" in out


def test_rich_animations_render_with_code_fences():
    resolved = {"color.brand": {"type": "color", "value": "#0ae448"}}
    brand = {"animations": [{"name": "Hero Reveal", "role": "Entrance",
                             "spec": "Rise chars.\n\n```js\ngsap.from(x)\n```"}]}
    out = export_design_md.to_design_md(resolved, name="X", brand=brand, rich=True)
    assert "## Animation Recipes" in out and "### Hero Reveal" in out
    assert "```js\ngsap.from(x)\n```" in out


def test_gsap_template_validates_and_exports_rich():
    tree = model.load(str(pathlib.Path(__file__).parents[1] / "templates" / "gsap.tokens.json"))
    from dtokens import brand_summary
    resolved = resolve.resolve(tree)
    out = export_design_md.to_design_md(resolved, name="GSAP",
                                        brand=brand_summary.extract_brand(tree), rich=True)
    assert "--motion-hero" in out and "## Animation Recipes" in out
    assert "| just-black | `#0e100f` | `--color-just-black` |" in out
