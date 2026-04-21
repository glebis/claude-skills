from unittest.mock import patch, MagicMock
from pathlib import Path
from skill_studio.setup import run_setup


def test_run_setup_writes_and_encrypts(tmp_path, monkeypatch):
    env_path = tmp_path / ".env.skill-studio"
    pipecat_env = tmp_path / ".env.pipecat"
    pipecat_env.write_text("DAILY_API_KEY=d\nGROQ_API_KEY=g\nDEEPGRAM_API_KEY=dg\n")

    # No agency-rag env — will prompt for OpenRouter key via getpass
    agency_rag_env = tmp_path / ".env.agency-rag"  # does not exist

    # input() is called for:
    #   1. Anthropic: "Reuse from $ANTHROPIC_API_KEY? [y/N]" → "y"
    #   2. Pipecat: "Found .env.pipecat — reuse? [Y/n]" → "y"
    inputs = iter(["y",   # Anthropic: reuse from env
                   "y",   # Pipecat: reuse
                   ])
    # getpass is called for: gemini, openrouter
    getpass_responses = iter(["fake-gemini-key", "or-key-123"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(getpass_responses))
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "existing-anthropic")

    with patch("skill_studio.setup.encrypt_dotenv") as enc:
        run_setup(
            env_path=env_path,
            pipecat_env=pipecat_env,
            agency_rag_env=agency_rag_env,
            validate_gemini=lambda k: True,
        )
        enc.assert_called_once_with(env_path)

    content = env_path.read_text()
    assert "GEMINI_API_KEY=fake-gemini-key" in content
    assert "OPENROUTER_API_KEY=or-key-123" in content
    assert "ANTHROPIC_API_KEY=existing-anthropic" in content
    assert "DAILY_API_KEY=d" in content


def test_run_setup_imports_openrouter_from_agency_rag(tmp_path, monkeypatch):
    """OpenRouter key imported from .env.agency-rag via sops_helper mock."""
    env_path = tmp_path / ".env.skill-studio"
    pipecat_env = tmp_path / ".env.pipecat"
    agency_rag_env = tmp_path / ".env.agency-rag"
    # File must exist for the branch to trigger
    agency_rag_env.write_text("placeholder")

    inputs = iter(["y",  # import OpenRouter from agency-rag
                   "n",  # Anthropic: skip
                   "n",  # Pipecat: skip
                   ])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Mock sops_helper to return a dict with the key
    fake_sops = MagicMock()
    fake_sops.decrypt_dotenv.return_value = {"OPENROUTER_API_KEY": "or-key-from-rag"}

    with patch("skill_studio.setup.encrypt_dotenv") as enc:
        run_setup(
            env_path=env_path,
            pipecat_env=pipecat_env,
            agency_rag_env=agency_rag_env,
            validate_gemini=lambda k: True,
            sops_helper=fake_sops,
        )
        enc.assert_called_once_with(env_path)

    content = env_path.read_text()
    assert "OPENROUTER_API_KEY=or-key-from-rag" in content
    assert "LLM_PROVIDER=openrouter" in content
    assert "OPENROUTER_MODEL=anthropic/claude-opus-4" in content


def test_run_setup_openrouter_key_not_in_agency_rag(tmp_path, monkeypatch):
    """If agency-rag exists but lacks OPENROUTER_API_KEY, setup still succeeds (key empty)."""
    env_path = tmp_path / ".env.skill-studio"
    pipecat_env = tmp_path / ".env.pipecat"
    agency_rag_env = tmp_path / ".env.agency-rag"
    agency_rag_env.write_text("placeholder")

    inputs = iter(["y",  # try to import from agency-rag
                   "n",  # Anthropic: skip
                   "n",  # Pipecat: skip
                   ])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "")
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    fake_sops = MagicMock()
    fake_sops.decrypt_dotenv.return_value = {}  # key absent

    with patch("skill_studio.setup.encrypt_dotenv"):
        run_setup(
            env_path=env_path,
            pipecat_env=pipecat_env,
            agency_rag_env=agency_rag_env,
            validate_gemini=lambda k: True,
            sops_helper=fake_sops,
        )

    content = env_path.read_text()
    assert "OPENROUTER_API_KEY" not in content
