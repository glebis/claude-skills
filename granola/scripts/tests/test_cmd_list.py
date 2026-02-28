import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import granola

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_cmd_list_json_output(monkeypatch, capsys):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    class Args:
        format = "json"

    granola.cmd_list(Args())
    output = json.loads(capsys.readouterr().out)

    assert len(output["meetings"]) == 1
    m = output["meetings"][0]
    assert m["id"] == "abc-123"
    assert m["title"] == "Test Meeting"
    assert m["has_local_transcript"] is True
    assert m["transcript_utterances"] == 2


def test_cmd_list_text_output(monkeypatch, capsys):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    class Args:
        format = "text"

    granola.cmd_list(Args())
    out = capsys.readouterr().out

    assert "Test Meeting" in out
    assert "1 meetings" in out
