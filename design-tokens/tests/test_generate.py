import json

from dtokens import brand_summary, generate

TREE = {
    "color": {
        "$type": "color",
        "primary": {"$value": "#BC9AFA"},
        "background": {"$value": "#0C1116"},
    },
    "$extensions": {"community.design-tokens.brand": {
        "mood": ["calm", "precise"],
        "imageryStyle": "flat vector",
        "avoid": ["glows"],
        "negativePrompt": "watermark",
    }},
}
RESOLVED = {
    "color.primary": {"type": "color", "value": "#BC9AFA"},
    "color.background": {"type": "color", "value": "#0C1116"},
}


def _summary():
    return brand_summary.summarize(RESOLVED, brand=brand_summary.extract_brand(TREE))


def test_compose_prompt_is_formulation_c():
    p = generate.compose_prompt(_summary(), "a poster")
    assert p.startswith("A calm, precise image: a poster.")
    assert "flat vector." in p
    assert "primary violet (#BC9AFA)" in p and "background near-black (#0C1116)" in p
    assert p.rstrip().endswith("Strictly avoid: glows, watermark.")


def test_compose_prompt_role_annotated_refs():
    refs = [{"file": "a.png", "take": ["palette", "mood"], "note": "the good one"},
            {"file": "b.png", "take": [], "note": ""}]
    p = generate.compose_prompt(_summary(), "a poster", refs=refs)
    assert "From reference image 1 (a.png) take: palette, mood — the good one." in p
    assert "From reference image 2 (b.png) take: overall style." in p


def test_load_refs_skips_unannotated(tmp_path):
    (tmp_path / "refs.json").write_text(json.dumps({"images": [
        {"file": "a.png", "take": ["style"], "note": ""},
        {"file": "b.png", "take": [], "note": ""},
    ]}))
    refs = generate.load_refs(tmp_path)
    assert [r["file"] for r in refs] == ["a.png"]
    assert refs[0]["path"] == str(tmp_path / "a.png")


def test_build_command_per_target():
    refs = [{"file": "a.png", "path": "/refs/a.png"}]
    gpt = generate.build_command("gpt-image-2", "P", "out.png", refs=refs, draft=True)
    assert "--draft" in gpt and "-y" in gpt and gpt[-2:] == ["P", "out.png"]
    assert gpt[gpt.index("--reference") + 1] == "/refs/a.png"
    nb = generate.build_command("nano-banana", "P", "out.png", draft=False)
    assert ["--model", "pro"] == nb[nb.index("--model"):nb.index("--model") + 2]


def test_generate_invokes_runner_per_target(tmp_path):
    calls = []

    class _Proc:
        returncode = 0

    def runner(cmd):
        calls.append(cmd)
        return _Proc()

    results = generate.generate(TREE, RESOLVED, "Acme", ["gpt-image-2", "nano-banana"],
                                subject="s", out_dir=tmp_path, runner=runner)
    assert len(calls) == 2 and all(rc == 0 for _, _, rc in results)
    assert results[0][1].endswith("acme-gpt-image-2.png")
