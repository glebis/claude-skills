import pathlib

import pytest

from dtokens import brand_summary, export_prompt, model, resolve, validate

TEMPLATES = pathlib.Path(__file__).resolve().parents[1] / "templates"
ALL = sorted(TEMPLATES.glob("*.tokens.json"))


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.name)
def test_template_validates_and_resolves(path):
    tree = model.load(str(path))
    assert validate.validate(tree) == []
    resolved = resolve.resolve(tree)
    assert resolved  # non-empty


def test_monaspace_carries_extracted_values():
    path = TEMPLATES / "monaspace.tokens.json"
    resolved = resolve.resolve(model.load(str(path)))
    # role aliases resolve to the values extracted from the live site
    roles = export_prompt._by_role(brand_summary.summarize(resolved))
    assert roles["primary"] == "#F5B8A5"     # Monaspace Neon
    assert roles["accent"] == "#BC9AFA"      # Monaspace Krypton
    assert roles["background"] == "#0D1117"  # GitHub dark canvas
    assert roles["text"] == "#FFFFFF"
    # the five superfamily faces are all present
    fonts = brand_summary.summarize(resolved)["fonts"]
    for face in ("Monaspace Neon", "Monaspace Argon", "Monaspace Xenon",
                 "Monaspace Radon", "Monaspace Krypton"):
        assert face in fonts
