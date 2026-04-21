from unittest.mock import MagicMock, patch
from pathlib import Path
from skill_studio.cli import main


def test_full_text_interview_writes_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr("skill_studio.cli.SESSION_ROOT", tmp_path)

    inputs = iter([
        "An agent that drafts my weekly review from my Obsidian vault",
        "It takes me 90 minutes every Sunday to write one from scratch",
        "done",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    fake_llm = MagicMock()
    # Combined call returns {"landed": bool, "patch": {...}} per user turn.
    # question_picker may also call LLM if pool exhausted (it won't here — YAML pool covers sprint depth).
    fake_llm.ask.side_effect = [
        '{"landed": false, "patch": {"hook": "Weekly review drafter", "problem": {"what_hurts": "takes 90 min every Sunday"}}}',
        '{"landed": false, "patch": {"problem": {"cost_today": "90 min/wk"}}}',
    ]

    with patch("skill_studio.cli.get_provider", return_value=fake_llm):
        rc = main(["new", "--preset", "ai-agent", "--depth", "sprint"])

    assert rc == 0
    session_dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
    assert len(session_dirs) == 1
    session = session_dirs[0]
    assert (session / "design.json").exists()
    assert (session / "design.md").exists()
    assert (session / "design.svg").exists()
    design_text = (session / "design.md").read_text()
    assert "Weekly review drafter" in design_text
    assert "90" in design_text
