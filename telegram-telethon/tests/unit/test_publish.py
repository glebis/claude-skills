"""Tests for the publish-draft helpers.

These are pure functions — no Telethon, no I/O except filesystem reads
in the channel-config helpers (tested with tmp_path).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from telegram_telethon.modules.publish import (
    parse_draft_frontmatter,
    extract_media_references,
    resolve_media_paths,
    strip_draft_header,
    strip_media_wikilinks,
    check_footer_exists,
    append_footer,
    load_channel_config,
    resolve_channel_from_draft,
)


# ---------- parse_draft_frontmatter ----------

class TestParseDraftFrontmatter:
    def test_basic_frontmatter(self):
        content = "---\ntitle: Test\nchannel: klodkot\n---\n\nBody text here"
        fm, body = parse_draft_frontmatter(content)
        assert fm["title"] == "Test"
        assert fm["channel"] == "klodkot"
        assert body == "Body text here"

    def test_no_frontmatter(self):
        fm, body = parse_draft_frontmatter("Just a body")
        assert fm == {}
        assert body == "Just a body"

    def test_invalid_yaml_raises(self):
        with pytest.raises(ValueError) as exc:
            parse_draft_frontmatter("---\nthis is: not: valid: yaml\n---\nBody")
        assert "frontmatter" in str(exc.value).lower()

    def test_frontmatter_with_list_field(self):
        content = "---\ntags:\n  - a\n  - b\n---\nBody"
        fm, body = parse_draft_frontmatter(content)
        assert fm["tags"] == ["a", "b"]


# ---------- extract_media_references ----------

class TestExtractMediaReferences:
    def test_video_from_frontmatter(self):
        assert extract_media_references({"video": "demo.mp4"}, "body") == ["demo.mp4"]

    def test_image_wikilinks_in_body(self):
        body = "intro\n\n![[chart.png]] and ![[photo.jpg]]"
        refs = extract_media_references({}, body)
        assert "chart.png" in refs and "photo.jpg" in refs

    def test_wikilink_with_alt_text(self):
        body = "![[image.png|alt description]]"
        refs = extract_media_references({}, body)
        assert refs == ["image.png"]

    def test_case_insensitive_extensions(self):
        body = "![[File.MP4]] and ![[Pic.JPEG]]"
        refs = extract_media_references({}, body)
        assert "File.MP4" in refs and "Pic.JPEG" in refs

    def test_non_media_wikilinks_ignored(self):
        body = "see [[Other Note]] for details"
        assert extract_media_references({}, body) == []

    def test_frontmatter_and_body_combined(self):
        fm = {"video": "intro.mp4"}
        body = "![[chart.png]]"
        refs = extract_media_references(fm, body)
        assert refs == ["intro.mp4", "chart.png"]


# ---------- resolve_media_paths ----------

class TestResolveMediaPaths:
    def test_finds_in_channel_attachments(self, tmp_path):
        channel_attach = tmp_path / "Channels" / "klodkot" / "attachments"
        channel_attach.mkdir(parents=True)
        (channel_attach / "demo.mp4").write_bytes(b"fake")

        paths = resolve_media_paths(["demo.mp4"], tmp_path, channel_folder="klodkot")
        assert paths == [channel_attach / "demo.mp4"]

    def test_falls_back_to_sources(self, tmp_path):
        sources = tmp_path / "Sources"
        sources.mkdir()
        (sources / "paper.png").write_bytes(b"fake")

        paths = resolve_media_paths(["paper.png"], tmp_path)
        assert paths == [sources / "paper.png"]

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError) as exc:
            resolve_media_paths(["nope.mp4"], tmp_path, channel_folder="klodkot")
        assert "nope.mp4" in str(exc.value)

    def test_multiple_files_preserve_order(self, tmp_path):
        sources = tmp_path / "Sources"
        sources.mkdir()
        for n in ["a.png", "b.png", "c.png"]:
            (sources / n).write_bytes(b"x")
        paths = resolve_media_paths(["c.png", "a.png", "b.png"], tmp_path)
        assert [p.name for p in paths] == ["c.png", "a.png", "b.png"]


# ---------- strip_draft_header ----------

class TestStripDraftHeader:
    def test_removes_telegram_draft_header(self):
        body = "# Title - Telegram Draft\n\nReal content"
        assert strip_draft_header(body).strip() == "Real content"

    def test_removes_draft_header(self):
        body = "# Topic — Draft\n\nBody"
        assert strip_draft_header(body).strip() == "Body"

    def test_keeps_non_draft_headers(self):
        body = "# Actual Title\n\nBody"
        assert strip_draft_header(body) == body

    def test_no_header(self):
        assert strip_draft_header("just text") == "just text"


# ---------- strip_media_wikilinks ----------

class TestStripMediaWikilinks:
    def test_removes_embed_wikilink(self):
        body = "intro\n\n![[chart.png]]\n\nmore text"
        result = strip_media_wikilinks(body)
        assert "![[chart.png]]" not in result
        assert "intro" in result and "more text" in result

    def test_keeps_text_only_wikilinks(self):
        body = "see [[Other Note]]"
        assert strip_media_wikilinks(body) == "see [[Other Note]]"

    def test_collapses_blank_runs(self):
        body = "a\n\n![[x.png]]\n\nb"
        result = strip_media_wikilinks(body)
        assert "\n\n\n" not in result


# ---------- footer helpers ----------

class TestFooter:
    def test_check_footer_exists_by_handle(self):
        body = "content\n\n**[NAME](https://t.me/klodkot)** — tagline"
        cfg = {"name": "klodkot"}
        assert check_footer_exists(body, cfg) is True

    def test_check_footer_absent(self):
        assert check_footer_exists("just body", {"name": "klodkot"}) is False

    def test_append_footer_adds_configured_footer(self):
        body = "hello"
        cfg = {"footer": "**[KLODKOT](https://t.me/klodkot)** — agents"}
        out = append_footer(body, cfg)
        assert out.endswith(cfg["footer"])
        assert body in out

    def test_append_footer_separates_with_blank_line(self):
        out = append_footer("x", {"footer": "y"})
        assert out == "x\n\ny"


# ---------- channel config ----------

def _make_channel(tmp: Path, folder: str, handle: str, footer: str | None = None):
    """Create a minimal Channels/<folder>/ layout for tests.

    YAML scalars starting with ``@`` must be quoted, matching how real
    vault files (``Channels/<folder>/<folder>.md``) store the handle.
    """
    channel_dir = tmp / "Channels" / folder
    channel_dir.mkdir(parents=True)
    index = channel_dir / f"{folder}.md"
    index.write_text(
        f'---\ntelegram_channel: "{handle}"\n---\n\n'
        f"Channel intro\n",
        encoding="utf-8",
    )
    if footer:
        pub_dir = channel_dir / "published"
        pub_dir.mkdir()
        (pub_dir / "first.md").write_text(
            f"Post body\n\n{footer}\n",
            encoding="utf-8",
        )
    return channel_dir


class TestLoadChannelConfig:
    def test_loads_by_folder(self, tmp_path):
        _make_channel(tmp_path, "klodkot", "@klodkot")
        cfg = load_channel_config("klodkot", vault_path=tmp_path)
        assert cfg is not None
        assert cfg["handle"] == "@klodkot"
        assert cfg["name"] == "klodkot"

    def test_missing_folder_returns_none(self, tmp_path):
        assert load_channel_config("ghost", vault_path=tmp_path) is None

    def test_extracts_footer_from_published_post(self, tmp_path):
        footer = "**[KLODKOT](https://t.me/klodkot)** — agents"
        _make_channel(tmp_path, "klodkot", "@klodkot", footer=footer)
        cfg = load_channel_config("klodkot", vault_path=tmp_path)
        assert cfg["footer"] == footer


class TestResolveChannelFromDraft:
    def test_resolves_via_folder_structure(self, tmp_path):
        _make_channel(tmp_path, "klodkot", "@klodkot")
        draft = tmp_path / "Channels" / "klodkot" / "drafts" / "post.md"
        draft.parent.mkdir(parents=True)
        draft.write_text("---\n---\nBody")

        cfg = resolve_channel_from_draft(draft, {}, vault_path=tmp_path)
        assert cfg is not None
        assert cfg["folder"] == "klodkot"

    def test_resolves_via_frontmatter_field(self, tmp_path):
        _make_channel(tmp_path, "mentalhealthtech", "@mentalhealthtech")
        # Draft lives outside Channels/
        draft = tmp_path / "loose-draft.md"
        draft.write_text("---\n---\nBody")

        cfg = resolve_channel_from_draft(
            draft, {"channel": "mentalhealthtech"}, vault_path=tmp_path,
        )
        assert cfg is not None
        assert cfg["folder"] == "mentalhealthtech"

    def test_unresolvable_returns_none(self, tmp_path):
        draft = tmp_path / "x.md"
        draft.write_text("---\n---\nBody")
        assert resolve_channel_from_draft(draft, {}, vault_path=tmp_path) is None
