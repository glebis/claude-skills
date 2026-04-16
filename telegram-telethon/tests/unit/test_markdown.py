"""Tests for the markdown→Telegram-HTML converter.

Behavior contract: the converter takes a markdown-flavored string and
returns a string using the subset of HTML tags that Telegram's ``parse_mode='html'``
understands. Unsupported markdown (e.g. tables, fenced code blocks with
languages) passes through untouched.
"""
from __future__ import annotations

import pytest

from telegram_telethon.modules.markdown import convert_markdown_to_telegram_html


class TestPlainText:
    def test_empty_string_passthrough(self):
        assert convert_markdown_to_telegram_html("") == ""

    def test_plain_prose_passthrough(self):
        assert convert_markdown_to_telegram_html("Hello world") == "Hello world"

    def test_newlines_preserved(self):
        assert convert_markdown_to_telegram_html("a\nb\nc") == "a\nb\nc"


class TestBold:
    def test_single_bold(self):
        assert convert_markdown_to_telegram_html("**hi**") == "<b>hi</b>"

    def test_bold_in_sentence(self):
        assert (
            convert_markdown_to_telegram_html("This is **important** text")
            == "This is <b>important</b> text"
        )

    def test_multiple_bolds(self):
        assert (
            convert_markdown_to_telegram_html("**one** and **two**")
            == "<b>one</b> and <b>two</b>"
        )


class TestItalic:
    def test_single_italic(self):
        assert convert_markdown_to_telegram_html("_emphasis_") == "<i>emphasis</i>"

    def test_italic_in_sentence(self):
        assert (
            convert_markdown_to_telegram_html("this is _emphasized_ text")
            == "this is <i>emphasized</i> text"
        )


class TestLink:
    def test_http_link(self):
        assert (
            convert_markdown_to_telegram_html("see [docs](https://example.com)")
            == 'see <a href="https://example.com">docs</a>'
        )

    def test_multiple_links(self):
        text = "[a](https://a.io) and [b](https://b.io)"
        expected = '<a href="https://a.io">a</a> and <a href="https://b.io">b</a>'
        assert convert_markdown_to_telegram_html(text) == expected


class TestHeader:
    def test_h2_becomes_bold(self):
        assert convert_markdown_to_telegram_html("## Section") == "<b>Section</b>"

    def test_h2_inside_document(self):
        text = "intro\n\n## Heading\n\nbody"
        expected = "intro\n\n<b>Heading</b>\n\nbody"
        assert convert_markdown_to_telegram_html(text) == expected


class TestBullets:
    def test_star_bullet_becomes_arrow(self):
        assert convert_markdown_to_telegram_html("* item") == "→ item"

    def test_dash_bullet_becomes_arrow(self):
        assert convert_markdown_to_telegram_html("- item") == "→ item"

    def test_bullet_list_in_block(self):
        text = "Items:\n* one\n* two\n* three"
        expected = "Items:\n→ one\n→ two\n→ three"
        assert convert_markdown_to_telegram_html(text) == expected


class TestCombination:
    def test_full_post(self):
        text = (
            "## Release\n\n"
            "**Version 2** ships _today_. "
            "See [changelog](https://example.com/cl).\n\n"
            "* fast\n"
            "* stable"
        )
        expected = (
            "<b>Release</b>\n\n"
            "<b>Version 2</b> ships <i>today</i>. "
            'See <a href="https://example.com/cl">changelog</a>.\n\n'
            "→ fast\n"
            "→ stable"
        )
        assert convert_markdown_to_telegram_html(text) == expected


class TestIdempotenceOfRawHtml:
    def test_already_html_passes_through(self):
        # If the input already contains `<b>` tags (e.g. a post that was
        # hand-authored as HTML), the converter must not double-encode or
        # mangle them.
        assert (
            convert_markdown_to_telegram_html("<b>already bold</b>")
            == "<b>already bold</b>"
        )
