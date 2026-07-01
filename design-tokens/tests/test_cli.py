import json
import pathlib

from dtokens import cli

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_validate_ok(capsys):
    rc = cli.main(["validate", str(FIXTURES / "global.base.tokens.json")])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_validate_reports_errors(tmp_path, capsys):
    bad = tmp_path / "bad.tokens.json"
    bad.write_text(json.dumps({"a": {"$type": "color", "$value": "{missing}"}}))
    rc = cli.main(["validate", str(bad)])
    assert rc == 1
    assert "missing" in capsys.readouterr().out


def test_merge_then_export_matches_golden(tmp_path):
    merged = tmp_path / "merged.tokens.json"
    cli.main([
        "merge",
        str(FIXTURES / "global.base.tokens.json"),
        str(FIXTURES / "project.override.tokens.json"),
        "-o", str(merged),
    ])
    out_css = tmp_path / "out.css"
    cli.main(["export-css", str(merged), "-o", str(out_css)])
    expected = (FIXTURES / "expected.tokens.css").read_text()
    assert out_css.read_text() == expected


def test_setup_edit_scaffolds_and_validates(tmp_path, capsys):
    dest = tmp_path / "new.tokens.json"
    rc = cli.main(["setup-edit", str(dest)])
    assert rc == 0
    assert dest.exists()
    assert "color" in json.loads(dest.read_text())


def test_setup_edit_refuses_overwrite(tmp_path):
    dest = tmp_path / "exists.tokens.json"
    dest.write_text("{}")
    rc = cli.main(["setup-edit", str(dest)])
    assert rc == 1


def test_setup_edit_from_clones_source_deterministically(tmp_path):
    src = FIXTURES / "global.base.tokens.json"
    a = tmp_path / "a.tokens.json"
    b = tmp_path / "b.tokens.json"
    assert cli.main(["setup-edit", str(a), "--from", str(src)]) == 0
    assert cli.main(["setup-edit", str(b), "--from", str(src)]) == 0
    # same source -> byte-identical output, and content matches the source tree
    assert a.read_text() == b.read_text()
    assert json.loads(a.read_text()) == json.loads(src.read_text())


def test_setup_edit_from_rejects_missing_source(tmp_path, capsys):
    rc = cli.main(["setup-edit", str(tmp_path / "x.tokens.json"), "--from", str(tmp_path / "nope.json")])
    assert rc == 1
    assert "not found" in capsys.readouterr().out


def test_use_writes_css_and_design_md(tmp_path):
    rc = cli.main([
        "use",
        str(FIXTURES / "global.base.tokens.json"),
        "--name", "Base",
        "--out-dir", str(tmp_path),
    ])
    assert rc == 0
    assert (tmp_path / "tokens.css").exists()
    design = (tmp_path / "DESIGN.md").read_text()
    assert design.startswith("---\nversion: alpha")
    assert 'action-primary: "#1A73E8"' in design
    assert "## Colors" in design
    preview = (tmp_path / "preview.html").read_text()
    assert preview.startswith("<!doctype html>")
    assert "background: #1A73E8" in preview


def test_design_md_command_emits_to_stdout(capsys):
    rc = cli.main(["design-md", str(FIXTURES / "design-md-source.tokens.json"), "--name", "Test Brand"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("---\nversion: alpha")
    assert "## Typography" in out
