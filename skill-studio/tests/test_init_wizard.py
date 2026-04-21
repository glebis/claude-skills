from __future__ import annotations
import os
from pathlib import Path
import pytest

from skill_studio import init_wizard


def test_check_python_passes_on_current_interpreter():
    ok, msg = init_wizard.check_python()
    assert ok is True
    assert "Python" in msg


def test_check_sops_reports_missing(monkeypatch):
    monkeypatch.setattr(init_wizard.shutil, "which", lambda _: None)
    ok, msg = init_wizard.check_sops()
    assert ok is False
    assert "not found" in msg


def test_check_sops_reports_found(monkeypatch):
    monkeypatch.setattr(init_wizard.shutil, "which", lambda _: "/usr/local/bin/sops")
    ok, msg = init_wizard.check_sops()
    assert ok is True
    assert "/usr/local/bin/sops" in msg


def test_check_age_key_from_env(tmp_path, monkeypatch):
    key = tmp_path / "keys.txt"
    key.write_text("AGE-SECRET-KEY-XXX")
    monkeypatch.setenv("SOPS_AGE_KEY_FILE", str(key))
    ok, msg = init_wizard.check_age_key()
    assert ok is True
    assert str(key) in msg


def test_check_age_key_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("SOPS_AGE_KEY_FILE", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    ok, _ = init_wizard.check_age_key()
    assert ok is False


def test_write_plaintext_env_has_600_perms(tmp_path):
    path = tmp_path / "subdir" / ".env"
    init_wizard._write_plaintext_env(path, {"FOO": "bar", "BAZ": "qux"})
    assert path.read_text() == "FOO=bar\nBAZ=qux\n"
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600


def test_run_init_wizard_full_flow_plaintext(tmp_path, monkeypatch, capsys):
    """End-to-end test: user picks defaults, plaintext mode, skips provider keys."""
    home = tmp_path / ".skill-studio"
    env = tmp_path / ".env.skill-studio"

    # Force plaintext path (pretend sops is missing)
    monkeypatch.setattr(init_wizard, "check_sops", lambda: (False, "sops: mocked missing"))
    monkeypatch.setattr(init_wizard, "check_age_key", lambda: (False, "age: mocked missing"))
    monkeypatch.setattr(init_wizard, "_smoke_test", lambda: True)

    answers = iter([
        str(home),   # data home
        str(env),    # env file
        "skip",      # provider
        "n",         # voice
        "n",         # smoke test
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(init_wizard.getpass, "getpass", lambda prompt="": "")

    rc = init_wizard.run_init_wizard()
    assert rc == 0
    assert home.is_dir()
    assert (home / "sessions").is_dir()
    # No keys captured → env file should NOT be written
    assert not env.exists()

    out = capsys.readouterr().out
    assert "first-run setup wizard" in out
    assert str(home) in out


def test_run_init_wizard_writes_plaintext_env_with_keys(tmp_path, monkeypatch):
    home = tmp_path / ".skill-studio"
    env = tmp_path / ".env.skill-studio"

    monkeypatch.setattr(init_wizard, "check_sops", lambda: (False, ""))
    monkeypatch.setattr(init_wizard, "check_age_key", lambda: (False, ""))
    monkeypatch.setattr(init_wizard, "_smoke_test", lambda: True)

    answers = iter([
        str(home),
        str(env),
        "openrouter",
        "anthropic/claude-opus-4",  # model default confirmed
        "n",  # voice
        "n",  # smoke test
    ])
    secrets = iter(["or-key-xyz"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(init_wizard.getpass, "getpass", lambda prompt="": next(secrets))

    rc = init_wizard.run_init_wizard()
    assert rc == 0
    assert env.exists()
    body = env.read_text()
    assert "OPENROUTER_API_KEY=or-key-xyz" in body
    assert "LLM_PROVIDER=openrouter" in body
    assert "OPENROUTER_MODEL=anthropic/claude-opus-4" in body
