import pytest

from dtokens import export_prompt

RESOLVED = {
    "color.action-primary": {"type": "color", "value": "#1A73E8"},
    "color.ink-900": {"type": "color", "value": "#0B0B0C"},
    "color.surface": {"type": "color", "value": "#FFFFFF"},
    "color.danger": {"type": "color", "value": "#E5484D"},
    "type.body": {"type": "typography", "value": {"fontFamily": "Inter", "fontSize": {"value": 16, "unit": "px"}, "fontWeight": 400}},
    "radius.lg": {"type": "dimension", "value": {"value": 12, "unit": "px"}},
}


def test_brand_clause_uses_roles_hex_fonts_shape():
    summary = export_prompt._bs.summarize(RESOLVED)
    clause = export_prompt.brand_clause(summary)
    assert "primary #1A73E8" in clause
    assert "text #0B0B0C" in clause
    assert "Inter" in clause
    assert "rounded corners" in clause


def test_gpt_image_prompts_use_unique_presets_and_cli():
    out = export_prompt.to_image_prompts(RESOLVED, "Acme", "gpt-image-2")
    assert "scripts/gpt_image_2.py" in out
    assert "--preset bauhaus" in out  # a gpt-image-2 unique preset
    assert "--quality medium" in out
    assert "#1A73E8" in out  # brand hex flows into the subject
    assert "acme-bauhaus.png" in out


def test_nano_prompts_steer_to_text_and_pro_model():
    out = export_prompt.to_image_prompts(RESOLVED, "Acme", "nano-banana")
    assert "scripts/nano_banana.py" in out
    assert "--model pro" in out  # nano-banana's text-fidelity strength
    assert "--reference" in out  # its reference-anchoring strength is mentioned
    # nano-banana has no cost-confirm flag; -y would be invalid there.
    for line in out.splitlines():
        if line.startswith("scripts/nano_banana.py"):
            assert " -y" not in line


def test_gpt_image_keeps_confirm_flag():
    out = export_prompt.to_image_prompts(RESOLVED, "Acme", "gpt-image-2")
    assert any(l.startswith("scripts/gpt_image_2.py") and l.rstrip().endswith("-y \\")
               for l in out.splitlines())


def test_unknown_target_raises():
    with pytest.raises(ValueError):
        export_prompt.to_image_prompts(RESOLVED, "Acme", "midjourney")


def test_custom_presets_and_platform():
    out = export_prompt.to_image_prompts(
        RESOLVED, "Acme", "gpt-image-2", presets=["poster"], platform="story"
    )
    assert "--preset poster" in out and "--preset bauhaus" not in out
    assert "--platform story" in out


def test_tufte_theme_maps_roles_to_variables():
    out = export_prompt.to_tufte_theme(RESOLVED, "Acme")
    assert "--ink: #0B0B0C;" in out          # text role -> --ink (from token)
    assert "--bg: #FFFFFF;" in out            # background role -> --bg
    assert "--spark-primary: #1A73E8;" in out  # primary role
    assert "--status-red: #E5484D;" in out    # danger role
    # role with no token falls back to tufte default, labelled as such
    assert "--status-amber: #c89000;   /* watch-level signal (tufte default) */" in out
    assert "EB Garamond" in out


def test_tufte_theme_falls_back_fully_when_no_roles():
    out = export_prompt.to_tufte_theme({"color.x": {"type": "color", "value": "#123456"}}, "X")
    assert "--ink: #1a1a1a;" in out  # all defaults
    assert "tufte default" in out


BRAND = {
    "mood": ["precise", "calm"],
    "imageryStyle": "flat vector, dot-grid textures",
    "avoid": ["glows", "gradients as decoration"],
    "negativePrompt": "photorealistic, watermark",
}


def test_brand_extensions_flow_into_image_prompts():
    out = export_prompt.to_image_prompts(RESOLVED, "Acme", "gpt-image-2", brand=BRAND)
    assert "mood: precise, calm" in out
    assert "flat vector, dot-grid textures" in out
    assert "# BRAND DON'Ts: glows; gradients as decoration" in out
    assert "Avoid: photorealistic, watermark" in out


def test_no_brand_extensions_is_clean():
    out = export_prompt.to_image_prompts(RESOLVED, "Acme", "gpt-image-2")
    assert "mood:" not in out and "BRAND DON'Ts" not in out and "Avoid:" not in out
