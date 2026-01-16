"""Tests for configuration management."""
import pytest
from pathlib import Path
import yaml

from telegram_telethon.core.config import (
    Config,
    DaemonConfig,
    TriggerConfig,
    ClaudeConfig,
    ConfigError,
    DEFAULT_CONFIG_DIR,
)


class TestConfig:
    """Tests for main Config class."""

    def test_default_config_dir(self):
        """Default config dir is ~/.config/telegram-telethon/"""
        assert DEFAULT_CONFIG_DIR == Path.home() / ".config" / "telegram-telethon"

    def test_load_nonexistent_returns_empty(self, temp_config_dir):
        """Loading from nonexistent path returns empty config."""
        config = Config.load(temp_config_dir / "nonexistent.yaml")
        assert config.api_id is None
        assert config.api_hash is None
        assert not config.is_configured()

    def test_save_and_load_roundtrip(self, temp_config_dir, sample_config):
        """Config saves and loads correctly."""
        config_path = temp_config_dir / "config.yaml"

        config = Config(**sample_config)
        config.save(config_path)

        loaded = Config.load(config_path)
        assert loaded.api_id == sample_config["api_id"]
        assert loaded.api_hash == sample_config["api_hash"]
        assert loaded.phone == sample_config["phone"]

    def test_is_configured_requires_api_credentials(self, sample_config):
        """is_configured returns True only with api_id and api_hash."""
        config = Config()
        assert not config.is_configured()

        config.api_id = sample_config["api_id"]
        assert not config.is_configured()

        config.api_hash = sample_config["api_hash"]
        assert config.is_configured()

    def test_session_path_derived_from_config_dir(self, temp_config_dir):
        """Session file path is in config directory."""
        config = Config(config_dir=temp_config_dir)
        assert config.session_path == temp_config_dir / "session.session"

    def test_config_file_permissions(self, temp_config_dir, sample_config):
        """Config file is created with restricted permissions (0600)."""
        config_path = temp_config_dir / "config.yaml"
        config = Config(**sample_config)
        config.save(config_path)

        # Check file permissions (Unix only)
        import os
        mode = os.stat(config_path).st_mode & 0o777
        assert mode == 0o600, f"Expected 0600, got {oct(mode)}"

    def test_api_hash_not_logged(self, sample_config):
        """api_hash should not appear in string representation."""
        config = Config(**sample_config)
        str_repr = str(config)
        assert sample_config["api_hash"] not in str_repr
        assert "***" in str_repr or "REDACTED" in str_repr


class TestDaemonConfig:
    """Tests for daemon configuration."""

    def test_load_daemon_config(self, temp_config_dir, sample_daemon_config):
        """Daemon config loads from YAML."""
        config_path = temp_config_dir / "daemon.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_daemon_config, f)

        config = DaemonConfig.load(config_path)
        assert len(config.triggers) == 2
        assert config.claude.max_turns == 10
        assert config.queue_max_concurrent == 1

    def test_default_daemon_config(self):
        """Default daemon config has sensible defaults."""
        config = DaemonConfig()
        assert config.triggers == []
        assert config.claude.max_turns == 10
        assert config.claude.timeout == 300
        assert config.queue_max_concurrent == 1

    def test_trigger_pattern_compilation(self, sample_daemon_config):
        """Trigger patterns compile to regex."""
        trigger = TriggerConfig(**sample_daemon_config["triggers"][0])
        assert trigger.compiled_pattern is not None
        assert trigger.compiled_pattern.match("/claude test prompt")
        assert not trigger.compiled_pattern.match("random text")

    def test_invalid_regex_raises_error(self):
        """Invalid regex pattern raises ConfigError."""
        with pytest.raises(ConfigError, match="Invalid regex"):
            TriggerConfig(
                chat="test",
                pattern="[invalid(",
                action="claude",
            )


class TestTriggerConfig:
    """Tests for trigger configuration."""

    def test_trigger_matches_chat(self):
        """Trigger matches specific chat."""
        trigger = TriggerConfig(chat="Test Chat", pattern=".*", action="claude")
        assert trigger.matches_chat("Test Chat")
        assert not trigger.matches_chat("Other Chat")

    def test_trigger_wildcard_matches_all(self):
        """Wildcard '*' matches any chat."""
        trigger = TriggerConfig(chat="*", pattern=".*", action="claude")
        assert trigger.matches_chat("Any Chat")
        assert trigger.matches_chat("Another Chat")

    def test_trigger_extracts_capture_group(self):
        """Pattern capture groups are extracted."""
        trigger = TriggerConfig(
            chat="*",
            pattern=r"^/claude (.+)$",
            action="claude",
        )
        match = trigger.match_message("/claude do something")
        assert match is not None
        assert match.group(1) == "do something"

    def test_reply_mode_default_inline(self):
        """Default reply mode is inline."""
        trigger = TriggerConfig(chat="*", pattern=".*", action="claude")
        assert trigger.reply_mode == "inline"

    def test_reply_mode_options(self):
        """Reply mode can be inline or new."""
        trigger_inline = TriggerConfig(
            chat="*", pattern=".*", action="claude", reply_mode="inline"
        )
        trigger_new = TriggerConfig(
            chat="*", pattern=".*", action="claude", reply_mode="new"
        )
        assert trigger_inline.reply_mode == "inline"
        assert trigger_new.reply_mode == "new"


class TestClaudeConfig:
    """Tests for Claude integration config."""

    def test_default_values(self):
        """Default Claude config values."""
        config = ClaudeConfig()
        assert config.allowed_tools == []
        assert config.max_turns == 10
        assert config.timeout == 300

    def test_build_cli_args(self):
        """Builds correct CLI arguments."""
        config = ClaudeConfig(
            allowed_tools=["Read", "Edit"],
            max_turns=5,
        )
        args = config.build_cli_args()
        assert "--allowedTools" in args
        assert "Read,Edit" in args
        assert "--max-turns" in args
        assert "5" in args

    def test_empty_tools_omits_flag(self):
        """Empty allowed_tools doesn't add --allowedTools."""
        config = ClaudeConfig(allowed_tools=[])
        args = config.build_cli_args()
        assert "--allowedTools" not in args
