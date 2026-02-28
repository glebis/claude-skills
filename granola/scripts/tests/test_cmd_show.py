import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import granola

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_cmd_show_finds_by_id_prefix(monkeypatch, capsys):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    class Args:
        meeting_id = "abc"

    granola.cmd_show(Args())
    output = json.loads(capsys.readouterr().out)

    assert output["id"] == "abc-123"
    assert output["title"] == "Test Meeting"
    assert output["summary"] == "Test summary"


def test_cmd_show_finds_by_title_substring(monkeypatch, capsys):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    class Args:
        meeting_id = "test meeting"

    granola.cmd_show(Args())
    output = json.loads(capsys.readouterr().out)
    assert output["id"] == "abc-123"


def test_cmd_show_exits_on_not_found(monkeypatch):
    monkeypatch.setattr(granola, "CACHE_PATH",
                        os.path.join(FIXTURES, "cache_string_state.json"))

    class Args:
        meeting_id = "nonexistent"

    with pytest.raises(SystemExit):
        granola.cmd_show(Args())
