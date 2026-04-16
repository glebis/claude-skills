"""Tests for the unrendered-markup detector."""
from __future__ import annotations

import pytest

from telegram_telethon.modules.lint import detect_unrendered_markup, Finding


def _make_entity(class_name: str, offset: int, length: int):
    """Create a fake entity whose class name matches Telethon's types.

    The detector identifies code spans by checking ``type(ent).__name__``
    so any object whose class bears the right name works.
    """
    cls = type(class_name, (), {})
    ent = cls()
    ent.offset = offset
    ent.length = length
    return ent


def _kinds(text: str, entities=None) -> list[str]:
    return [f.kind for f in detect_unrendered_markup(text, entities)]


class TestCleanText:
    def test_empty_returns_no_findings(self):
        assert detect_unrendered_markup("") == []
        assert detect_unrendered_markup(None) == []

    def test_plain_prose_is_clean(self):
        assert detect_unrendered_markup("Hello world, how are you?") == []

    def test_asterisk_as_punctuation_is_clean(self):
        # A lone asterisk used as a bullet or emphasis shouldn't trip
        # the bold rule (which requires matching `**…**`).
        assert detect_unrendered_markup("See footnote*.") == []

    def test_single_underscore_is_clean(self):
        # Bare `_snake_case_` identifiers are valid prose.
        assert detect_unrendered_markup("use snake_case here") == []


class TestMarkdownLeaks:
    def test_leaked_bold(self):
        findings = detect_unrendered_markup("This is **bold** text")
        assert len(findings) == 1
        assert findings[0].kind == "markdown_bold"
        assert findings[0].match == "**bold**"

    def test_leaked_italic_underscore(self):
        findings = detect_unrendered_markup("This is __italic__ text")
        assert len(findings) == 1
        assert findings[0].kind == "markdown_italic_underscore"

    def test_leaked_strikethrough(self):
        findings = detect_unrendered_markup("old ~~wrong~~ new")
        assert len(findings) == 1
        assert findings[0].kind == "markdown_strikethrough"

    def test_leaked_link(self):
        findings = detect_unrendered_markup("see [docs](https://example.com/x)")
        assert len(findings) == 1
        assert findings[0].kind == "markdown_link"
        assert findings[0].match == "[docs](https://example.com/x)"

    def test_leaked_header(self):
        findings = detect_unrendered_markup("## Section\nbody here")
        assert len(findings) == 1
        assert findings[0].kind == "markdown_header"

    def test_multiple_leaks_reported_in_order(self):
        text = "**bold** then [link](https://x.y) and __em__"
        findings = detect_unrendered_markup(text)
        kinds = [f.kind for f in findings]
        assert kinds == [
            "markdown_bold",
            "markdown_link",
            "markdown_italic_underscore",
        ]
        # offsets are strictly increasing
        offsets = [f.offset for f in findings]
        assert offsets == sorted(offsets)


class TestHtmlLeaks:
    def test_leaked_bold_tag(self):
        findings = detect_unrendered_markup("This is <b>bold</b>")
        kinds = [f.kind for f in findings]
        assert "html_tag" in kinds
        assert len([k for k in kinds if k == "html_tag"]) == 2  # open + close

    def test_leaked_anchor_with_attrs(self):
        findings = detect_unrendered_markup(
            'see <a href="https://example.com">link</a>'
        )
        kinds = [f.kind for f in findings]
        # open <a ...> and closing </a>
        assert kinds.count("html_tag") == 2

    def test_unrelated_angle_brackets_clean(self):
        # A generic `<foo>` that isn't on the HTML allowlist is ignored —
        # we only flag Telegram-supported HTML tags that visibly leak.
        assert _kinds("x <foo>bar</foo> y") == []


class TestCodeSpanSuppression:
    def test_match_inside_code_entity_suppressed(self):
        # Raw text contains `**bold**` but the whole span is marked as
        # MessageEntityCode — it's inline code, not leaked markup.
        text = "See example: **bold** inline"
        entity = _make_entity(
            "MessageEntityCode",
            offset=text.index("**bold**"),
            length=len("**bold**"),
        )
        findings = detect_unrendered_markup(text, [entity])
        assert findings == []

    def test_match_outside_code_entity_still_reported(self):
        text = "Code: `ok` but also **bold** outside"
        entity = _make_entity(
            "MessageEntityCode",
            offset=text.index("`ok`"),
            length=len("`ok`"),
        )
        findings = detect_unrendered_markup(text, [entity])
        assert [f.kind for f in findings] == ["markdown_bold"]

    def test_non_code_entity_does_not_suppress(self):
        # A bold entity doesn't give license to leave `**` in the raw text.
        text = "bad **bold** here"
        entity = _make_entity(
            "MessageEntityBold",
            offset=text.index("**bold**"),
            length=len("**bold**"),
        )
        findings = detect_unrendered_markup(text, [entity])
        assert [f.kind for f in findings] == ["markdown_bold"]


class TestFindingSerialization:
    def test_to_dict_has_expected_keys(self):
        findings = detect_unrendered_markup("<b>x</b>")
        assert findings
        d = findings[0].to_dict()
        assert set(d) == {"kind", "pattern", "match", "offset", "length", "note"}
