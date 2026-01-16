"""Configuration management for telegram-telethon.

Handles loading, saving, and validating configuration from YAML files.
Supports both core API config and daemon trigger config.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Any

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "telegram-telethon"


class ConfigError(Exception):
    """Configuration error."""
    pass


@dataclass
class Config:
    """Core Telegram API configuration."""

    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    phone: Optional[str] = None
    allowed_send_groups: List[str] = field(default_factory=list)
    config_dir: Path = field(default_factory=lambda: DEFAULT_CONFIG_DIR)

    def is_configured(self) -> bool:
        """Check if API credentials are set."""
        return self.api_id is not None and self.api_hash is not None

    @property
    def session_path(self) -> Path:
        """Path to session file."""
        return self.config_dir / "session.session"

    @property
    def config_path(self) -> Path:
        """Path to config file."""
        return self.config_dir / "config.yaml"

    def save(self, path: Optional[Path] = None) -> None:
        """Save config to YAML file with restricted permissions."""
        path = path or self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "phone": self.phone,
            "allowed_send_groups": self.allowed_send_groups,
        }

        # Write with restricted permissions (owner read/write only)
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        os.chmod(path, 0o600)

    @classmethod
    def load(cls, path: Path) -> Config:
        """Load config from YAML file."""
        if not path.exists():
            return cls(config_dir=path.parent)

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            api_id=data.get("api_id"),
            api_hash=data.get("api_hash"),
            phone=data.get("phone"),
            allowed_send_groups=data.get("allowed_send_groups", []),
            config_dir=path.parent,
        )

    def __str__(self) -> str:
        """String representation with redacted api_hash."""
        hash_display = "***REDACTED***" if self.api_hash else None
        return (
            f"Config(api_id={self.api_id}, "
            f"api_hash={hash_display}, "
            f"phone={self.phone})"
        )


@dataclass
class ClaudeConfig:
    """Configuration for Claude Code integration."""

    allowed_tools: List[str] = field(default_factory=list)
    max_turns: int = 10
    timeout: int = 300  # seconds

    def build_cli_args(self) -> List[str]:
        """Build CLI arguments for claude command."""
        args = []

        if self.allowed_tools:
            args.extend(["--allowedTools", ",".join(self.allowed_tools)])

        args.extend(["--max-turns", str(self.max_turns)])

        return args

    @classmethod
    def from_dict(cls, data: dict) -> ClaudeConfig:
        """Create from dictionary."""
        return cls(
            allowed_tools=data.get("allowed_tools", []),
            max_turns=data.get("max_turns", 10),
            timeout=data.get("timeout", 300),
        )


@dataclass
class TriggerConfig:
    """Configuration for a single daemon trigger."""

    chat: str
    pattern: str
    action: str  # "claude", "reply", "ignore"
    reply_mode: str = "inline"  # "inline" or "new"
    reply_text: Optional[str] = None  # For action="reply"
    debounce_seconds: int = 0  # Wait this long after last message before responding
    system_prompt: Optional[str] = None  # Custom system prompt for claude action

    _compiled: Optional[re.Pattern] = field(default=None, repr=False)

    def __post_init__(self):
        """Compile regex pattern."""
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as e:
            raise ConfigError(f"Invalid regex pattern '{self.pattern}': {e}")

    @property
    def compiled_pattern(self) -> re.Pattern:
        """Get compiled regex pattern."""
        if self._compiled is None:
            self._compiled = re.compile(self.pattern)
        return self._compiled

    def matches_chat(self, chat_name: str) -> bool:
        """Check if trigger matches a chat name."""
        if self.chat == "*":
            return True
        return self.chat.lower() == chat_name.lower()

    def match_message(self, text: str) -> Optional[re.Match]:
        """Match message text against pattern."""
        return self.compiled_pattern.match(text)

    @classmethod
    def from_dict(cls, data: dict) -> TriggerConfig:
        """Create from dictionary."""
        return cls(
            chat=data["chat"],
            pattern=data["pattern"],
            action=data["action"],
            reply_mode=data.get("reply_mode", "inline"),
            reply_text=data.get("reply_text"),
            debounce_seconds=data.get("debounce_seconds", 0),
            system_prompt=data.get("system_prompt"),
        )


@dataclass
class DaemonConfig:
    """Configuration for the daemon process."""

    triggers: List[TriggerConfig] = field(default_factory=list)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    queue_max_concurrent: int = 1
    queue_timeout: int = 600
    log_file: Optional[Path] = None
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: Path) -> DaemonConfig:
        """Load daemon config from YAML file."""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        triggers = [
            TriggerConfig.from_dict(t)
            for t in data.get("triggers", [])
        ]

        claude_data = data.get("claude", {})
        claude = ClaudeConfig.from_dict(claude_data)

        queue_data = data.get("queue", {})

        return cls(
            triggers=triggers,
            claude=claude,
            queue_max_concurrent=queue_data.get("max_concurrent", 1),
            queue_timeout=queue_data.get("timeout", 600),
            log_file=Path(data["logging"]["file"]) if data.get("logging", {}).get("file") else None,
            log_level=data.get("logging", {}).get("level", "INFO"),
        )

    def save(self, path: Path) -> None:
        """Save daemon config to YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "triggers": [
                {
                    "chat": t.chat,
                    "pattern": t.pattern,
                    "action": t.action,
                    "reply_mode": t.reply_mode,
                    **({"reply_text": t.reply_text} if t.reply_text else {}),
                    **({"debounce_seconds": t.debounce_seconds} if t.debounce_seconds else {}),
                    **({"system_prompt": t.system_prompt} if t.system_prompt else {}),
                }
                for t in self.triggers
            ],
            "claude": {
                "allowed_tools": self.claude.allowed_tools,
                "max_turns": self.claude.max_turns,
                "timeout": self.claude.timeout,
            },
            "queue": {
                "max_concurrent": self.queue_max_concurrent,
                "timeout": self.queue_timeout,
            },
            "logging": {
                "file": str(self.log_file) if self.log_file else None,
                "level": self.log_level,
            },
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
