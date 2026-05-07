#!/usr/bin/env python3
"""Deterministic message classifier for the daemon hook.

No LLM reasoning — only exact matching and config lookup.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

import yaml


@dataclass
class RouteResult:
    """Result of deterministic routing."""

    route: str
    contact_mode: Optional[str] = None
    template_name: Optional[str] = None
    priority: int = 50


class ResponderConfig:
    """Loads and queries tg-responder config."""

    def __init__(self, config_path: Path):
        with open(config_path) as f:
            self._raw = yaml.safe_load(f) or {}

        self._contacts: Dict[str, dict] = {}
        self._ignore_list: List[str] = []
        self._course_patterns: List[str] = []
        self._course_template: Optional[str] = None
        self._default_mode: str = "draft_only"

        self._parse_contacts()

    def _parse_contacts(self) -> None:
        contacts = self._raw.get("contacts", {})

        for name, cfg in contacts.items():
            if name == "_ignore":
                self._ignore_list = [n.lower() for n in cfg]
            elif name == "_course_inquiry":
                self._course_patterns = cfg.get("detect_patterns", [])
                self._course_template = cfg.get("template")
            elif name == "_default":
                self._default_mode = cfg.get("mode", "draft_only") if isinstance(cfg, dict) else "draft_only"
            else:
                self._contacts[name.lower()] = cfg

    @property
    def daemon(self) -> dict:
        return self._raw.get("daemon", {})

    @property
    def worker(self) -> dict:
        return self._raw.get("worker", {})

    @property
    def scan(self) -> dict:
        return self._raw.get("scan", {})

    def is_ignored(self, sender_name: str) -> bool:
        return sender_name.lower() in self._ignore_list

    def is_course_inquiry(self, text: str) -> bool:
        for pattern in self._course_patterns:
            if pattern in text:
                return True
        return False

    def get_contact(self, sender_name: str) -> Optional[dict]:
        return self._contacts.get(sender_name.lower())

    def classify(self, sender_name: str, text: str, is_bot: bool = False) -> RouteResult:
        """Deterministic classification of an incoming message."""
        if is_bot and self.scan.get("ignore_bots", True):
            return RouteResult(route="ignored")

        if self.is_ignored(sender_name):
            return RouteResult(route="ignored")

        if text and self.is_course_inquiry(text):
            return RouteResult(
                route="course_inquiry",
                contact_mode="auto_respond",
                template_name=self._course_template,
                priority=10,
            )

        contact = self.get_contact(sender_name)
        if contact:
            mode = contact.get("mode", self._default_mode)
            return RouteResult(
                route="known_contact",
                contact_mode=mode,
                priority=30 if mode == "auto" else 50,
            )

        return RouteResult(
            route="needs_classification",
            contact_mode=self._default_mode,
            priority=50,
        )


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def load_config(config_path: Path = CONFIG_PATH) -> ResponderConfig:
    return ResponderConfig(config_path)


if __name__ == "__main__":
    cfg = load_config()

    tests = [
        ("AGENCY Community Bot", "some message", False),
        ("Lora Vit", "Сделай мне PDF", False),
        ("Анастасия", "Привет! Хочу записаться на лабораторию по Claude code!", False),
        ("Unknown Person", "Привет, как дела?", False),
        ("SomeBot", "spam", True),
    ]

    for name, text, bot in tests:
        result = cfg.classify(name, text, bot)
        print(f"{name:30s} → route={result.route:25s} mode={result.contact_mode}")
