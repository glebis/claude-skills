import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import granola

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_cmd_export_generates_fathom_compatible_markdown(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    output_file = tmp_path / "test-export.md"

    class Args:
        meeting_id = "abc"
        vault = str(tmp_path)
        output = str(output_file)
        local_only = True

    granola.cmd_export(Args())

    # Check JSON output
    result = json.loads(capsys.readouterr().out)
    assert result["title"] == "Test Meeting"
    assert result["utterances"] == 2
    assert "Gleb Kalinin" in result["participants"]

    # Check generated markdown
    content = output_file.read_text()

    # Frontmatter
    assert "granola_id: abc-123" in content
    assert 'title: "Test Meeting"' in content
    assert "source: granola" in content
    assert "date: 2026-02-28" in content

    # Transcript with speaker attribution
    assert "**Gleb Kalinin**: Hello everyone" in content
    assert "**Other**: Hi there" in content

    # Summary
    assert "Test summary" in content
