import pytest

from dtokens import TokenError
from dtokens import export_css


def test_var_name():
    assert export_css.css_var_name("color.brand.primary") == "--color-brand-primary"
    assert export_css.css_var_name("type.body", "font-size") == "--type-body-font-size"


def test_serialize_scalar_types():
    assert export_css.serialize_value("color", "#00f") == "#00f"
    assert export_css.serialize_value("dimension", {"value": 8, "unit": "px"}) == "8px"
    assert export_css.serialize_value("duration", {"value": 200, "unit": "ms"}) == "200ms"
    assert export_css.serialize_value("fontFamily", ["Inter", "sans-serif"]) == "Inter, sans-serif"
    assert export_css.serialize_value("fontWeight", 600) == "600"


def test_serialize_typography_expands():
    out = export_css.serialize_value(
        "typography",
        {
            "fontFamily": "Inter",
            "fontSize": {"value": 16, "unit": "px"},
            "fontWeight": 400,
            "lineHeight": 1.5,
        },
    )
    assert out == {
        "font-family": "Inter",
        "font-size": "16px",
        "font-weight": "400",
        "line-height": "1.5",
    }


def test_serialize_shadow():
    out = export_css.serialize_value(
        "shadow",
        {
            "offsetX": {"value": 0, "unit": "px"},
            "offsetY": {"value": 2, "unit": "px"},
            "blur": {"value": 4, "unit": "px"},
            "spread": {"value": 0, "unit": "px"},
            "color": "#0003",
        },
    )
    assert out == "0px 2px 4px 0px #0003"


def test_structured_color_object_raises():
    with pytest.raises(TokenError):
        export_css.serialize_value("color", {"colorSpace": "srgb", "components": [0, 0, 1]})


def test_export_css_full_block():
    resolved = {
        "color.brand": {"type": "color", "value": "#00f"},
        "type.body": {
            "type": "typography",
            "value": {
                "fontFamily": "Inter",
                "fontSize": {"value": 16, "unit": "px"},
                "fontWeight": 400,
                "lineHeight": 1.5,
            },
        },
    }
    css = export_css.export_css(resolved)
    assert ":root {" in css
    assert "  --color-brand: #00f;" in css
    assert "  --type-body-font-size: 16px;" in css
    assert "  --type-body-line-height: 1.5;" in css
    assert css.rstrip().endswith("}")
