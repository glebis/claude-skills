import json
import pathlib

from dtokens import cli

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def test_import_writes_valid_dtcg(tmp_path, capsys):
    out = tmp_path / "imported.tokens.json"
    rc = cli.main(["import", str(FIXTURES / "import-source.css"), "-o", str(out)])
    assert rc == 0
    tree = json.loads(out.read_text())
    assert tree["primary"]["$type"] == "color"
    assert tree["radius"]["$value"] == {"value": 0, "unit": "px"}
    # skip report goes to stderr
    assert "skipped" in capsys.readouterr().err


def test_imported_file_round_trips_through_export_css(tmp_path):
    imported = tmp_path / "imported.tokens.json"
    cli.main(["import", str(FIXTURES / "import-source.css"), "-o", str(imported)])
    css_out = tmp_path / "out.css"
    cli.main(["export-css", str(imported), "-o", str(css_out)])
    css = css_out.read_text()
    # source name preserved: --primary in, --primary out (no group prefix)
    assert "--primary: oklch(0.6489 0.2370 26.9728);" in css
