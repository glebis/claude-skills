from unittest.mock import patch, MagicMock
from pathlib import Path
from skill_studio.cli import main
import skill_studio.cli  # noqa: F401  (needed for patch target)


def test_cli_new_creates_session(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    fake_interviewer = MagicMock()
    fake_interviewer.ask.side_effect = [
        "What's the core pain?",
        '{"hook": "X"}',
        "Wrap up?",
    ]
    inputs = iter(["Testing hook\n", "done\n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs).rstrip())
    with patch("skill_studio.cli.get_provider", return_value=fake_interviewer):
        rc = main(["new", "--preset", "ai-agent", "--depth", "sprint"])
    assert rc == 0
    assert any(p.is_dir() for p in tmp_path.iterdir())


def test_cli_list_lists_sessions(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    from skill_studio.storage import SessionStorage
    storage = SessionStorage(root=tmp_path)
    storage.new()
    main(["list"])
    captured = capsys.readouterr()
    assert "preset" in captured.out.lower() or "id" in captured.out.lower()


def test_cli_export_runs_md_svg(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)
    from skill_studio.storage import SessionStorage
    from skill_studio.schema import DesignJSON
    fx = Path(__file__).parent / "fixtures" / "sample_design.json"
    storage = SessionStorage(root=tmp_path)
    design = DesignJSON.model_validate_json(fx.read_text())
    sess_dir = tmp_path / design.meta.id
    sess_dir.mkdir()
    (sess_dir / "design.json").write_text(design.model_dump_json(indent=2))
    (sess_dir / "transcript.md").touch()
    rc = main(["export", design.meta.id, "md-svg"])
    assert rc == 0
    assert (sess_dir / "design.md").exists()
    assert (sess_dir / "design.svg").exists()
