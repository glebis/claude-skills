"""Tests for state-only CLI subcommands: new-session, apply-patch, next-target, coverage, done."""
from __future__ import annotations
import json
import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from skill_studio.cli import main
from skill_studio.storage import SessionStorage


# ---------------------------------------------------------------------------
# new-session
# ---------------------------------------------------------------------------

def test_new_session_prints_session_id_and_opening(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    rc = main(["new-session", "--preset", "ai-agent", "--depth", "sprint"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "session_id:" in out
    assert "opening:" in out


def test_new_session_creates_design_json(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    rc = main(["new-session", "--preset", "ai-agent", "--depth", "standard", "--style", "socratic"])
    assert rc == 0
    # Find the session dir
    dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
    assert len(dirs) == 1
    assert (dirs[0] / "design.json").exists()


def test_new_session_meta_stored(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    rc = main(["new-session", "--preset", "ai-agent", "--depth", "deep", "--style", "form"])
    assert rc == 0
    out = capsys.readouterr().out
    # Parse session_id from output
    for line in out.splitlines():
        if line.startswith("session_id:"):
            sid = line.split(":", 1)[1].strip()
            break
    storage = SessionStorage(tmp_path)
    design = storage.load(sid)
    assert design.meta.preset == "ai-agent"
    assert design.meta.interview_mode.depth == "deep"
    assert design.meta.interview_mode.style == "form"


def test_new_session_all_presets(tmp_path, monkeypatch):
    for preset in ["ai-agent", "life-automation", "knowledge-work", "custom"]:
        sub = tmp_path / preset
        sub.mkdir()
        monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", sub)
        rc = main(["new-session", "--preset", preset])
        assert rc == 0


# ---------------------------------------------------------------------------
# apply-patch
# ---------------------------------------------------------------------------

def _create_session(tmp_path: Path, preset: str = "ai-agent") -> str:
    """Helper: create a session and return its id."""
    storage = SessionStorage(tmp_path)
    from skill_studio.presets import load_preset
    preset_obj = load_preset(preset)
    design = storage.new()
    design.meta.preset = preset
    storage.save(design)
    return design.meta.id


def test_apply_patch_updates_design(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)

    patch_json = json.dumps({"hook": "My automation hook"})
    monkeypatch.setattr("sys.stdin", io.StringIO(patch_json))
    rc = main(["apply-patch", sid])
    assert rc == 0

    storage = SessionStorage(tmp_path)
    design = storage.load(sid)
    assert design.hook == "My automation hook"

    out = capsys.readouterr().out
    assert "coverage:" in out
    assert "next_target:" in out


def test_apply_patch_empty_patch_no_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("{}"))
    rc = main(["apply-patch", sid])
    assert rc == 0


def test_apply_patch_nested_fields(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    patch_json = json.dumps({"problem": {"what_hurts": "too much manual work", "cost_today": "2h/day"}})
    monkeypatch.setattr("sys.stdin", io.StringIO(patch_json))
    rc = main(["apply-patch", sid])
    assert rc == 0

    storage = SessionStorage(tmp_path)
    design = storage.load(sid)
    assert design.problem.what_hurts == "too much manual work"
    assert design.problem.cost_today == "2h/day"


def test_apply_patch_invalid_json_returns_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not-valid-json"))
    rc = main(["apply-patch", sid])
    assert rc == 1


# ---------------------------------------------------------------------------
# next-target
# ---------------------------------------------------------------------------

def test_next_target_prints_field(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    rc = main(["next-target", sid])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    # Should print a field path like "hook" or "DONE"
    assert len(out) > 0


def test_next_target_done_when_no_uncovered_fields(tmp_path, monkeypatch, capsys):
    """next-target returns DONE when next_uncovered_field() returns None.
    We mock the underlying function to isolate the CLI subcommand logic."""
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)

    import skill_studio.cli as cli_mod
    monkeypatch.setattr(cli_mod, "next_uncovered_field", lambda design, preset: None)

    rc = main(["next-target", sid])
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out == "DONE"


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------

def test_coverage_prints_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    rc = main(["coverage", sid])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "overall" in data
    assert "fields" in data
    assert 0.0 <= data["overall"] <= 1.0


# ---------------------------------------------------------------------------
# done
# ---------------------------------------------------------------------------

def test_done_exports_md_and_svg(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    sid = _create_session(tmp_path)
    rc = main(["done", sid])
    assert rc == 0
    out = capsys.readouterr().out
    assert "wrote" in out
    assert (tmp_path / sid / "design.md").exists()
    assert (tmp_path / sid / "design.svg").exists()
