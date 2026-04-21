"""Centralized path resolution with environment-variable overrides.

All user-facing paths are resolved here so the tool is portable and contains
no hard-coded, user-specific locations. Override any of these via env vars:

- SKILL_STUDIO_HOME       — data root (default: ~/.skill-studio)
- SKILL_STUDIO_ENV_FILE   — encrypted dotenv (default: $HOME/.env.skill-studio or $SKILL_STUDIO_HOME/.env)
- SKILL_STUDIO_PIPECAT_ENV — voice-mode secrets (default: $HOME/.env.pipecat)
- SKILL_STUDIO_IMPORT_ENV — optional dotenv to import OPENROUTER_API_KEY from during setup
- SKILL_STUDIO_GROUNDWORK_ROOT — optional groundwork integration; feature disabled if unset
"""
from __future__ import annotations
import os
from pathlib import Path


def _env_path(name: str, default: Path | None) -> Path | None:
    val = os.environ.get(name)
    if val:
        return Path(val).expanduser()
    return default


def home() -> Path:
    """Root directory for session data, cache, etc."""
    default = Path.home() / ".skill-studio"
    return _env_path("SKILL_STUDIO_HOME", default)  # type: ignore[return-value]


def session_root() -> Path:
    return home() / "sessions"


def env_file() -> Path:
    """Encrypted .env (sops) holding LLM + voice provider keys."""
    default = Path.home() / ".env.skill-studio"
    return _env_path("SKILL_STUDIO_ENV_FILE", default)  # type: ignore[return-value]


def pipecat_env_file() -> Path:
    default = Path.home() / ".env.pipecat"
    return _env_path("SKILL_STUDIO_PIPECAT_ENV", default)  # type: ignore[return-value]


def import_env_file() -> Path | None:
    """Optional dotenv to import OPENROUTER_API_KEY from during first-run setup."""
    return _env_path("SKILL_STUDIO_IMPORT_ENV", None)


def groundwork_root() -> Path | None:
    """Optional groundwork integration root. If unset, groundwork feed is disabled."""
    val = os.environ.get("SKILL_STUDIO_GROUNDWORK_ROOT")
    if val:
        return Path(val).expanduser()
    return None
