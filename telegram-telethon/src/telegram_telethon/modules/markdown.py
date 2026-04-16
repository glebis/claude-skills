"""Markdown → Telegram HTML converter.

Telegram's ``parse_mode='html'`` accepts a small subset of HTML tags
(``<b>``, ``<i>``, ``<a>``, ``<code>``, ``<pre>``, ``<u>``, ``<s>``,
``<tg-spoiler>``, ``<blockquote>``). This module translates a
markdown-flavored source string into that subset so the sender can write
markdown and still get server-side rendering.

The ruleset mirrors the existing converter in the standalone ``telegram``
skill so posts published from either place render the same way. Unknown
markdown (tables, fenced code with languages, etc.) passes through
unchanged — we're not a general Markdown parser, just a thin adapter for
the formatting users actually put in posts.
"""
from __future__ import annotations

import re


def convert_markdown_to_telegram_html(text: str) -> str:
    """Convert a markdown-flavored string into Telegram-flavored HTML.

    Rules, applied in this order:
    - ``## Header`` on its own line → ``<b>Header</b>``
    - ``* item`` / ``- item`` at line start → ``→ item`` (arrow bullet)
    - ``**bold**`` → ``<b>bold</b>``
    - ``_italic_`` → ``<i>italic</i>``
    - ``[text](url)`` → ``<a href="url">text</a>``

    Line-scoped rules (headers, bullets) run before inline rules so the
    leading ``*`` of a bullet isn't consumed by the bold rule.

    Pre-existing HTML in the input is left intact, making the converter
    idempotent for posts that already use the target format.
    """
    if not text:
        return text

    text = re.sub(r"^##\s+(.+?)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\s+(.+?)$", r"→ \1", text, flags=re.MULTILINE)
    text = re.sub(r"^-\s+(.+?)$", r"→ \1", text, flags=re.MULTILINE)

    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)

    return text


__all__ = ["convert_markdown_to_telegram_html"]
