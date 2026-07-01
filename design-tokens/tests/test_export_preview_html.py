import pathlib

from dtokens import export_preview_html, model, resolve

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def _resolved():
    tree = model.load(str(FIXTURES / "design-md-source.tokens.json"))
    return resolve.resolve(tree)


def test_preview_is_standalone_html():
    out = export_preview_html.to_preview_html(_resolved(), "Test Brand")
    assert out.startswith("<!doctype html>")
    assert out.rstrip().endswith("</body></html>")
    assert "Test Brand" in out
    # The only permitted external reference is the Google Fonts @import (so the
    # brand typefaces actually render); no external CSS/JS files or <img>.
    assert "<script src" not in out and '<link rel="stylesheet"' not in out
    assert "<img" not in out
    for url in [u for u in out.split("'") if u.startswith(("http://", "https://"))]:
        assert url.startswith("https://fonts.googleapis.com/css2?"), url


def test_preview_imports_brand_fonts_deterministically():
    out = export_preview_html.to_preview_html(_resolved(), "X")
    # families + weights sorted -> byte-stable URL; fixture uses Inter 400
    assert "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap')" in out


def test_full_preview_is_landing_page_driven_by_tokens():
    out = export_preview_html.to_full_preview_html(_resolved(), "Acme — Bold Futures", "A tagline.")
    assert out.startswith("<!doctype html>")
    assert 'class="hero"' in out and 'class="quote"' in out
    # colors come from the :root custom properties, not hardcoded
    assert "var(--color-primary" in out and "var(--color-background" in out
    # name splits on the dash: wordmark + display title
    assert ">Acme<" in out and ">Bold Futures<" in out
    assert "A tagline." in out


def test_full_preview_only_external_ref_is_fonts():
    out = export_preview_html.to_full_preview_html(_resolved(), "X")
    assert "<img" not in out and "<script src" not in out
    for url in [u for u in out.split("'") if u.startswith(("http://", "https://"))]:
        assert url.startswith("https://fonts.googleapis.com/css2?"), url


def test_full_preview_is_deterministic():
    a = export_preview_html.to_full_preview_html(_resolved(), "X", "d")
    b = export_preview_html.to_full_preview_html(_resolved(), "X", "d")
    assert a == b


def test_preview_renders_color_chip_with_value():
    out = export_preview_html.to_preview_html(_resolved(), "X")
    assert "<h2>Colors</h2>" in out
    assert "background: #1A73E8" in out


def test_preview_renders_type_specimen_with_inline_font():
    out = export_preview_html.to_preview_html(_resolved(), "X")
    assert "<h2>Typography</h2>" in out
    assert "font-size: 16px" in out
    # generic fallback appended so specimens don't drop to serif
    assert "font-family: Inter, sans-serif" in out


def test_preview_mono_family_gets_monospace_fallback():
    resolved = {
        "type.code": {
            "type": "typography",
            "value": {"fontFamily": "Space Mono", "fontSize": {"value": 14, "unit": "px"}},
        }
    }
    out = export_preview_html.to_preview_html(resolved, "X")
    assert "font-family: Space Mono, monospace" in out


def test_preview_renders_spacing_and_rounded():
    out = export_preview_html.to_preview_html(_resolved(), "X")
    assert "<h2>Spacing</h2>" in out
    assert "width: 8px" in out
    assert "<h2>Rounded</h2>" in out
    assert "border-radius: 4px" in out


def test_preview_escapes_name():
    out = export_preview_html.to_preview_html({}, "<script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
