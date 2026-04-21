import subprocess
from unittest.mock import MagicMock
from pathlib import Path
from skill_studio.sops_helper import encrypt_dotenv, decrypt_dotenv


def test_encrypt_calls_sops(tmp_path, monkeypatch):
    plain = tmp_path / ".env.skill-studio"
    plain.write_text("GEMINI_API_KEY=abc\n")
    called = {}

    def fake_run(cmd, cwd=None, check=False, capture_output=False, text=False):
        called["cmd"] = cmd
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    encrypt_dotenv(plain)
    assert called["cmd"][0] == "sops"
    assert "--encrypt" in called["cmd"]


def test_decrypt_returns_mapping(tmp_path, monkeypatch):
    encrypted = tmp_path / ".env.skill-studio"
    encrypted.write_text("ciphertext")

    def fake_run(cmd, cwd=None, check=False, capture_output=False, text=False):
        return MagicMock(returncode=0, stdout="GEMINI_API_KEY=abc\nANTHROPIC_API_KEY=xyz\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    env = decrypt_dotenv(encrypted)
    assert env["GEMINI_API_KEY"] == "abc"
    assert env["ANTHROPIC_API_KEY"] == "xyz"
