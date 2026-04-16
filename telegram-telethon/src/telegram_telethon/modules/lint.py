"""Linter for published Telegram messages.

Detects unrendered markdown/HTML markup that leaked into the raw text of
a published message. When Telegram successfully parses formatting, the
markup characters are stripped from ``message.text`` and a corresponding
entity is attached. If ``**bold**`` or ``<b>foo</b>`` is still visible in
the raw text, the parsing was skipped — usually because the sender forgot
``--markdown`` or the conversion to Telegram HTML failed.

The detector is a pure function so it can run against any text+entities
pair, whether fetched from a channel history, a draft, or a just-sent
message.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Iterable, List, Optional, Sequence


CODE_ENTITY_CLASS_NAMES = {"MessageEntityCode", "MessageEntityPre"}


@dataclass
class Finding:
    """One unrendered-markup hit inside a message."""

    kind: str            # e.g. "markdown_bold", "html_tag", "markdown_link"
    pattern: str         # rule label
    match: str           # literal substring from the raw text
    offset: int          # UTF-16 code-unit offset in the raw text (Telegram's unit)
    length: int          # UTF-16 code-unit length of the match
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# Each rule: (kind, regex, note). Regex uses re.MULTILINE where relevant.
# Patterns are intentionally tight so valid prose (e.g. a lone asterisk)
# does not trip them. Anything that matches one of these in raw text is
# almost certainly a formatting leak — because when Telegram parses the
# markup, it strips these characters.
_RULES: List[tuple[str, re.Pattern[str], Optional[str]]] = [
    (
        "markdown_bold",
        re.compile(r"\*\*[^\s*][^*\n]*?[^\s*]\*\*|\*\*[^\s*]\*\*"),
        "`**text**` survived — Markdown bold was not parsed.",
    ),
    (
        "markdown_italic_underscore",
        re.compile(r"(?<!\w)__[^\s_][^_\n]*?[^\s_]__(?!\w)"),
        "`__text__` survived — Markdown italic/bold underscore was not parsed.",
    ),
    (
        "markdown_strikethrough",
        re.compile(r"~~[^\s~][^~\n]*?[^\s~]~~"),
        "`~~text~~` survived — Markdown strikethrough was not parsed.",
    ),
    (
        "markdown_link",
        re.compile(r"\[[^\]\n]+\]\((https?://[^\s)]+|mailto:[^\s)]+)\)"),
        "`[text](url)` survived — Markdown link was not parsed.",
    ),
    (
        "markdown_header",
        re.compile(r"(?m)^#{1,6}\s+\S"),
        "`#`-prefixed header line survived — Markdown header was not parsed.",
    ),
    (
        "html_tag",
        re.compile(
            r"</?(?:b|strong|i|em|u|s|del|code|pre|a|tg-spoiler|blockquote)"
            r"(?:\s+[^<>]*)?/?>",
            re.IGNORECASE,
        ),
        "Raw HTML tag survived — HTML was sent as plain text.",
    ),
]


def _entity_class(entity: Any) -> str:
    return type(entity).__name__


def _is_inside_code_span(offset: int, length: int, entities: Iterable[Any]) -> bool:
    """Return True if [offset, offset+length) falls fully inside a code/pre entity.

    Telegram's entity offsets are in UTF-16 code units, same as the
    regex offsets here (since Python ``re`` on ``str`` uses code points
    and we feed it the raw ``message.text``). Offsets agree for the BMP,
    which covers every realistic markup character, so we can compare
    offsets directly without re-encoding.
    """
    end = offset + length
    for ent in entities or ():
        if _entity_class(ent) not in CODE_ENTITY_CLASS_NAMES:
            continue
        ent_offset = getattr(ent, "offset", None)
        ent_length = getattr(ent, "length", None)
        if ent_offset is None or ent_length is None:
            continue
        if ent_offset <= offset and end <= ent_offset + ent_length:
            return True
    return False


def detect_unrendered_markup(
    text: Optional[str],
    entities: Optional[Sequence[Any]] = None,
) -> List[Finding]:
    """Scan ``text`` for markup fragments Telegram failed to render.

    Args:
        text: Raw message text as received from Telegram (``message.text``
              or ``message.raw_text``). ``None`` or empty returns no
              findings.
        entities: Optional list of Telethon ``MessageEntity`` objects to
                  suppress hits inside fenced code / inline code spans.

    Returns:
        A list of ``Finding`` objects, one per leaked markup occurrence.
        Empty list means the message looks clean.
    """
    if not text:
        return []

    findings: List[Finding] = []
    ents = entities or []
    for kind, pattern, note in _RULES:
        for m in pattern.finditer(text):
            offset = m.start()
            length = m.end() - m.start()
            if _is_inside_code_span(offset, length, ents):
                continue
            findings.append(
                Finding(
                    kind=kind,
                    pattern=pattern.pattern,
                    match=m.group(0),
                    offset=offset,
                    length=length,
                    note=note,
                )
            )

    findings.sort(key=lambda f: (f.offset, f.kind))
    return findings


__all__ = ["Finding", "detect_unrendered_markup"]
