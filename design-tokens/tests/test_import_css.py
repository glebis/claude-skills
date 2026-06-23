import pathlib

from dtokens import import_css, resolve, validate

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_parse_css_vars_reads_root_only_and_strips_comments():
    css = FIXTURES.joinpath("import-source.css").read_text()
    vars_ = import_css.parse_css_vars(css)
    assert vars_["primary"] == "oklch(0.6489 0.2370 26.9728)"
    assert vars_["background"] == "#ffffff"  # :root value, not .dark's #000000
    assert "/*" not in vars_["primary"]


def test_infer_types():
    assert import_css.infer("primary", "oklch(0.6 0.2 27)")[0] == "color"
    assert import_css.infer("bg", "#fff")[0] == "color"
    assert import_css.infer("radius", "0px") == ("dimension", {"value": 0, "unit": "px"})
    assert import_css.infer("space", "0.25rem") == ("dimension", {"value": 0.25, "unit": "rem"})
    assert import_css.infer("fast", "200ms") == ("duration", {"value": 200, "unit": "ms"})
    assert import_css.infer("opacity", "1") == ("number", 1)
    assert import_css.infer("font-sans", "DM Sans, sans-serif") == ("fontFamily", "DM Sans, sans-serif")


def test_gradient_is_skipped_with_reason():
    _type, reason = import_css.infer("hero-gradient", "linear-gradient(90deg, #fff, #000)")
    assert _type is None
    assert isinstance(reason, str)


def test_to_tokens_preserves_names_and_skips_unsupported():
    css = FIXTURES.joinpath("import-source.css").read_text()
    tree, skipped = import_css.to_tokens(css)
    assert tree["primary"] == {"$type": "color", "$value": "oklch(0.6489 0.2370 26.9728)"}
    assert tree["font-sans"]["$type"] == "fontFamily"
    assert "hero-gradient" not in tree
    assert any(name == "hero-gradient" for name, _v, _r in skipped)


def test_imported_tree_is_valid_and_resolvable():
    css = FIXTURES.joinpath("import-source.css").read_text()
    tree, _ = import_css.to_tokens(css)
    assert validate.validate(tree) == []
    resolved = resolve.resolve(tree)
    assert resolved["primary"]["type"] == "color"
