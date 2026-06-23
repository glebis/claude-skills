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
