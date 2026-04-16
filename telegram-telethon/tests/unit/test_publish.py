"""Tests for the publish-draft helpers.

These are pure functions — no Telethon, no I/O except filesystem reads
in the channel-config helpers (tested with tmp_path).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
    update_frontmatter,
    extract_first_line,
    update_channel_index,
    resolve_draft_path,
    publish_draft,
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


# ---------- post-publish helpers ----------

class TestUpdateFrontmatter:
    def test_adds_published_fields(self, tmp_path):
        f = tmp_path / "draft.md"
        f.write_text("---\ntitle: Hi\n---\n\nBody text", encoding="utf-8")

        update_frontmatter(f, message_id=42)

        fm, body = parse_draft_frontmatter(f.read_text(encoding="utf-8"))
        assert fm["type"] == "published"
        assert fm["telegram_message_id"] == 42
        today = datetime.now().strftime("%Y%m%d")
        assert fm["published_date"] == f"[[{today}]]"
        assert "Body text" in body


class TestExtractFirstLine:
    def test_skips_headers_and_empty_lines(self):
        body = "\n\n# Header\n\nFirst real line of content"
        assert extract_first_line(body) == "First real line of content"

    def test_strips_markdown_formatting(self):
        body = "**bold** text and _italic_ and [link](https://x.io)"
        assert extract_first_line(body) == "bold text and italic and link"

    def test_truncates_long_lines(self):
        body = "x" * 200
        out = extract_first_line(body)
        assert out.endswith("...")
        assert len(out) == 80

    def test_empty_body_returns_fallback(self):
        assert extract_first_line("") == "New post"
        assert extract_first_line("\n\n# Only a header\n\n") == "New post"


class TestUpdateChannelIndex:
    def test_inserts_new_entry_at_top_of_published_section(self, tmp_path):
        idx = tmp_path / "klodkot.md"
        idx.write_text(
            "# Klodkot\n\n**Published**: `published/`\n- [[older-post]] — older summary\n",
            encoding="utf-8",
        )
        update_channel_index(idx, "new-post.md", "New summary")

        content = idx.read_text(encoding="utf-8")
        lines = content.split("\n")
        pub_idx = next(i for i, l in enumerate(lines) if "**Published**:" in l)
        # New entry immediately after the marker line
        assert lines[pub_idx + 1] == "- [[new-post]] — New summary"
        # Older entry still present
        assert "older-post" in content

    def test_missing_published_section_raises(self, tmp_path):
        idx = tmp_path / "nopub.md"
        idx.write_text("# A channel without a published section\n", encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            update_channel_index(idx, "post.md", "x")
        assert "Published" in str(exc.value)


class TestResolveDraftPath:
    def test_absolute_path_returned_verbatim(self, tmp_path):
        draft = tmp_path / "a.md"
        draft.write_text("x")
        assert resolve_draft_path(str(draft), vault_path=tmp_path) == draft

    def test_relative_under_channels(self, tmp_path):
        d = tmp_path / "Channels" / "klodkot" / "drafts"
        d.mkdir(parents=True)
        (d / "post.md").write_text("x")
        got = resolve_draft_path("Channels/klodkot/drafts/post.md", vault_path=tmp_path)
        assert got == d / "post.md"

    def test_filename_only_found_by_glob(self, tmp_path):
        d = tmp_path / "Channels" / "klodkot" / "drafts"
        d.mkdir(parents=True)
        (d / "post.md").write_text("x")
        assert resolve_draft_path("post.md", vault_path=tmp_path) == d / "post.md"

    def test_slug_without_extension(self, tmp_path):
        d = tmp_path / "Channels" / "klodkot" / "drafts"
        d.mkdir(parents=True)
        (d / "post.md").write_text("x")
        assert resolve_draft_path("post", vault_path=tmp_path) == d / "post.md"

    def test_ambiguous_match_returns_none(self, tmp_path):
        for folder in ("klodkot", "mht"):
            d = tmp_path / "Channels" / folder / "drafts"
            d.mkdir(parents=True)
            (d / "same.md").write_text("x")
        # Caller is expected to report ambiguity separately.
        assert resolve_draft_path("same.md", vault_path=tmp_path) is None

    def test_not_found_returns_none(self, tmp_path):
        assert resolve_draft_path("ghost.md", vault_path=tmp_path) is None


# ---------- publish_draft orchestrator ----------

def _setup_klodkot_vault(tmp_path, footer="**[KLODKOT](https://t.me/klodkot)** — tagline"):
    """Build a minimal vault with klodkot channel + index + published section."""
    chan = tmp_path / "Channels" / "klodkot"
    chan.mkdir(parents=True)
    (chan / "klodkot.md").write_text(
        f'---\ntelegram_channel: "@klodkot"\n---\n\n'
        f"# Klodkot channel\n\n**Published**: `published/`\n",
        encoding="utf-8",
    )
    # Seed a published post so the footer extractor finds the signature.
    pub = chan / "published"
    pub.mkdir()
    (pub / "seed.md").write_text(f"Body\n\n{footer}\n", encoding="utf-8")
    (chan / "drafts").mkdir()
    return chan


class TestPublishDraft:
    @pytest.mark.asyncio
    async def test_dry_run_returns_preview_without_sending(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "hello.md"
        draft.write_text(
            '---\ntitle: Hi\n---\n\n# Hi — Draft\n\n**Hello** world',
            encoding="utf-8",
        )
        client = AsyncMock()

        result = await publish_draft(
            client, str(draft), dry_run=True, vault_path=tmp_path,
        )

        assert result.get("dry_run") is True
        assert result["channel"] == "@klodkot"
        assert "body_preview" in result
        client.send_message.assert_not_called()
        client.send_file.assert_not_called()
        # Draft not moved
        assert draft.exists()

    @pytest.mark.asyncio
    async def test_already_published_returns_error(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "p.md"
        draft.write_text(
            '---\ntelegram_message_id: 77\n---\n\nBody',
            encoding="utf-8",
        )
        result = await publish_draft(
            AsyncMock(), str(draft), dry_run=True, vault_path=tmp_path,
        )
        assert result.get("already_published") is True
        assert result["published"] is False

    @pytest.mark.asyncio
    async def test_unresolvable_channel_returns_error(self, tmp_path):
        # Draft outside Channels/ and with no channel frontmatter
        (tmp_path / "Channels").mkdir()
        draft = tmp_path / "orphan.md"
        draft.write_text("---\n---\nBody", encoding="utf-8")
        result = await publish_draft(
            AsyncMock(), str(draft), dry_run=True, vault_path=tmp_path,
        )
        assert result["published"] is False
        assert "channel" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_sends_text_only_and_updates_metadata(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "post.md"
        draft.write_text(
            '---\ntitle: Hi\n---\n\nHello **world**',
            encoding="utf-8",
        )

        # Mock Telethon client: send_message returns object with .id
        client = AsyncMock()
        entity = MagicMock()
        sent = MagicMock(id=5050)
        client.send_message = AsyncMock(return_value=sent)

        with patch(
            "telegram_telethon.modules.publish.resolve_entity",
            new=AsyncMock(return_value=(entity, "@klodkot")),
        ):
            result = await publish_draft(
                client, str(draft), dry_run=False, vault_path=tmp_path,
            )

        assert result["published"] is True
        assert result["message_id"] == 5050
        client.send_message.assert_awaited_once()
        kwargs = client.send_message.await_args.kwargs
        # Body was converted to HTML (<b>world</b>)
        sent_text = client.send_message.await_args.args[1]
        assert "<b>world</b>" in sent_text
        assert kwargs["parse_mode"] == "html"

        # File moved
        moved = chan / "published" / "post.md"
        assert moved.exists()
        assert not draft.exists()

        # Frontmatter updated
        fm, _ = parse_draft_frontmatter(moved.read_text(encoding="utf-8"))
        assert fm["type"] == "published"
        assert fm["telegram_message_id"] == 5050

    @pytest.mark.asyncio
    async def test_sends_album_when_media_present(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        attach = chan / "attachments"
        attach.mkdir()
        (attach / "pic.png").write_bytes(b"x")
        (attach / "vid.mp4").write_bytes(b"x")

        draft = chan / "drafts" / "media-post.md"
        draft.write_text(
            '---\nvideo: vid.mp4\n---\n\nIntro\n\n![[pic.png]]',
            encoding="utf-8",
        )

        client = AsyncMock()
        client.send_file = AsyncMock(return_value=[MagicMock(id=1), MagicMock(id=2)])

        with patch(
            "telegram_telethon.modules.publish.resolve_entity",
            new=AsyncMock(return_value=(MagicMock(), "@klodkot")),
        ):
            result = await publish_draft(
                client, str(draft), dry_run=False, vault_path=tmp_path,
            )

        assert result["published"] is True
        assert result["message_id"] == 1
        assert result["media_count"] == 2
        client.send_file.assert_awaited_once()
        # First positional is the entity, second is the list of paths
        paths = client.send_file.await_args.args[1]
        assert len(paths) == 2

    @pytest.mark.asyncio
    async def test_missing_media_returns_error(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "x.md"
        draft.write_text(
            '---\nvideo: missing.mp4\n---\n\nBody',
            encoding="utf-8",
        )
        result = await publish_draft(
            AsyncMock(), str(draft), dry_run=True, vault_path=tmp_path,
        )
        assert result["published"] is False
        assert "missing.mp4" in result["error"]

    @pytest.mark.asyncio
    async def test_schedule_forwarded_and_reported(self, tmp_path):
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "later.md"
        draft.write_text('---\n---\nHello', encoding="utf-8")

        client = AsyncMock()
        client.send_message = AsyncMock(return_value=MagicMock(id=9))
        when = datetime(2027, 6, 1, 10, 0)

        with patch(
            "telegram_telethon.modules.publish.resolve_entity",
            new=AsyncMock(return_value=(MagicMock(), "@klodkot")),
        ):
            result = await publish_draft(
                client, str(draft), dry_run=False,
                schedule=when, vault_path=tmp_path,
            )

        assert result["scheduled_for"] == when.isoformat()
        kwargs = client.send_message.await_args.kwargs
        assert kwargs["schedule"] == when

    @pytest.mark.asyncio
    async def test_lint_warnings_surface_in_result(self, tmp_path):
        """If the body still contains HTML-ish leaked markup (e.g. raw <b>
        tags that the converter leaves intact), lint findings appear
        in the result so a reviewer can catch render issues."""
        chan = _setup_klodkot_vault(tmp_path)
        draft = chan / "drafts" / "lint-post.md"
        # Raw HTML that markdown converter leaves intact — detected by lint
        draft.write_text(
            '---\n---\nBody with <b>hand-rolled</b> html',
            encoding="utf-8",
        )
        client = AsyncMock()
        client.send_message = AsyncMock(return_value=MagicMock(id=1))

        with patch(
            "telegram_telethon.modules.publish.resolve_entity",
            new=AsyncMock(return_value=(MagicMock(), "@klodkot")),
        ):
            result = await publish_draft(
                client, str(draft), dry_run=False, vault_path=tmp_path,
            )

        # Sent ok, but lint flagged raw HTML tag
        assert result["published"] is True
        assert "lint_warnings" in result
        assert any(w.get("kind") == "html_tag" for w in result["lint_warnings"])
