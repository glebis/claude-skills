"""Pure helpers for the publish-to-channel workflow.

Factors out the non-Telethon parts of skill A's ``publish_draft`` so the
orchestrator (added next) can focus on Telegram I/O and post-publish
bookkeeping. Everything here is deterministic, side-effect-free apart
from filesystem reads in the channel-config helpers — those take an
explicit ``vault_path`` so tests can drive them with ``tmp_path``.

Contract map (skill A → this module):
    parse_draft_frontmatter         (unchanged)
    extract_media_references        (unchanged)
    resolve_media_paths             (unchanged)
    strip_draft_header              (unchanged)
    strip_media_wikilinks           (unchanged)
    check_footer_exists             (unchanged)
    append_footer                   (unchanged)
    load_channel_config             (accepts vault_path)
    resolve_channel_from_draft      (accepts vault_path)

``vault_path`` defaults to ``~/Brains/brain`` (same as skill A) so
production callers don't need to pass it.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from telegram_telethon.modules.lint import detect_unrendered_markup
from telegram_telethon.modules.markdown import convert_markdown_to_telegram_html
from telegram_telethon.modules.messages import resolve_entity


logger = logging.getLogger(__name__)

DEFAULT_VAULT_PATH = Path.home() / "Brains" / "brain"


# ---------- frontmatter / body ----------

def parse_draft_frontmatter(content: str) -> Tuple[Dict, str]:
    """Split a markdown file into (frontmatter dict, body)."""
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse frontmatter: {exc}")

    return frontmatter, parts[2].strip()


# ---------- media ----------

_MEDIA_EXTS = r"mp4|png|jpg|jpeg"
_WIKILINK_PATTERN = re.compile(
    r"\[\[([^\[\]]+\.(?:" + _MEDIA_EXTS + r"))(?:\|[^\]]+)?\]\]",
    re.IGNORECASE,
)
_EMBED_PATTERN = re.compile(
    r"!\[\[([^\[\]]+\.(?:" + _MEDIA_EXTS + r"))(?:\|[^\]]+)?\]\]\n?",
    re.IGNORECASE,
)


def extract_media_references(frontmatter: Dict, body: str) -> List[str]:
    """Collect media filenames from frontmatter ``video:`` + body wikilinks."""
    media: List[str] = []

    video = frontmatter.get("video") if frontmatter else None
    if video:
        media.append(video)

    for match in _WIKILINK_PATTERN.finditer(body):
        media.append(match.group(1))

    return media


def resolve_media_paths(
    filenames: List[str],
    vault_path: Path,
    channel_folder: Optional[str] = None,
) -> List[Path]:
    """Resolve filenames against the vault's conventional media locations.

    Search order: channel attachments → channel videos → Attachments/ → Sources/.
    Raises ``FileNotFoundError`` if any filename can't be located.
    """
    search_dirs: List[Path] = []
    if channel_folder:
        search_dirs.append(vault_path / "Channels" / channel_folder / "attachments")
        search_dirs.append(vault_path / "Channels" / channel_folder / "videos")
    search_dirs.append(vault_path / "Attachments")
    search_dirs.append(vault_path / "Sources")

    resolved: List[Path] = []
    for name in filenames:
        for dir_ in search_dirs:
            candidate = dir_ / name
            if candidate.exists():
                resolved.append(candidate)
                break
        else:
            raise FileNotFoundError(
                f"Media file not found: {name}. "
                f"Searched in: {', '.join(str(d) for d in search_dirs)}"
            )

    return resolved


# ---------- body cleanup ----------

_DRAFT_MARKERS = ("telegram draft", "draft", "— draft")


def strip_draft_header(body: str) -> str:
    """Remove a leading ``# ... Draft`` heading from the body if present."""
    lines = body.strip().split("\n")
    if not lines or not lines[0].startswith("#"):
        return body

    first_lower = lines[0].lower()
    if not any(marker in first_lower for marker in _DRAFT_MARKERS):
        return body

    lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    return "\n".join(lines)


def strip_media_wikilinks(body: str) -> str:
    """Remove embed-style media wikilinks (``![[file.ext]]``) from the body."""
    cleaned = _EMBED_PATTERN.sub("", body)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ---------- footer ----------

def check_footer_exists(body: str, channel_config: Optional[Dict] = None) -> bool:
    """Return True if ``body`` already includes the channel's footer signature."""
    if channel_config and channel_config.get("name"):
        return bool(
            re.search(r"t\.me/" + re.escape(channel_config["name"]), body, re.IGNORECASE)
        )

    # Legacy fallback — klodkot patterns.
    for pattern in (r"КЛОДКОТ", r"t\.me/klodkot"):
        if re.search(pattern, body, re.IGNORECASE):
            return True
    return False


def append_footer(body: str, channel_config: Optional[Dict] = None) -> str:
    """Append the channel's footer (blank-line separated)."""
    if channel_config and channel_config.get("footer"):
        return body + "\n\n" + channel_config["footer"]
    # Legacy fallback: klodkot-specific footer.
    footer = (
        "**[КЛОДКОТ](https://t.me/klodkot)** — "
        "Claude Code и другие агенты: инструменты, кейсы, вдохновение"
    )
    return body + "\n\n" + footer


# ---------- channel configuration ----------

def _extract_footer_from_dir(directory: Path, name: str) -> Optional[str]:
    """Scan a directory of markdown posts for the channel's footer line."""
    if not directory.exists():
        return None
    footer_re = re.compile(
        r"(\*\*\[.+?\]\(https?://t\.me/" + re.escape(name) + r"\)\*\* — .+?)$",
        re.MULTILINE,
    )
    for post in sorted(directory.glob("*.md"), reverse=True):
        match = footer_re.search(post.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return None


def load_channel_config(
    channel_folder: str,
    vault_path: Path = DEFAULT_VAULT_PATH,
) -> Optional[Dict]:
    """Load a channel's config from its index file frontmatter.

    Returns a dict with keys ``folder``, ``handle``, ``name``, ``footer``,
    ``aliases``. Returns None when the channel folder or index is missing
    or the frontmatter lacks a ``telegram_channel`` field.
    """
    channel_dir = vault_path / "Channels" / channel_folder
    index = channel_dir / f"{channel_folder}.md"
    if not index.exists():
        return None

    try:
        fm, _ = parse_draft_frontmatter(index.read_text(encoding="utf-8"))
    except ValueError:
        return None

    handle = fm.get("telegram_channel")
    if not handle:
        return None

    name = handle.lstrip("@")
    footer = (
        _extract_footer_from_dir(channel_dir / "published", name)
        or _extract_footer_from_dir(channel_dir, name)
    )
    if not footer:
        guidelines = channel_dir / "posting-guidelines.md"
        if guidelines.exists():
            match = re.search(
                r"(\*\*\[.+?\]\(https?://t\.me/" + re.escape(name) + r"\)\*\* — .+?)$",
                guidelines.read_text(encoding="utf-8"),
                re.MULTILINE,
            )
            if match:
                footer = match.group(1)

    return {
        "folder": channel_folder,
        "handle": handle,
        "name": name,
        "footer": footer,
        "aliases": fm.get("aliases", []),
    }


def resolve_channel_from_draft(
    draft_path: Path,
    frontmatter: Dict,
    vault_path: Path = DEFAULT_VAULT_PATH,
) -> Optional[Dict]:
    """Try folder structure first, then frontmatter ``channel:`` field."""
    # 1) Folder-based: Channels/<folder>/drafts/file.md
    try:
        rel = draft_path.relative_to(vault_path / "Channels")
        folder = rel.parts[0]
    except (ValueError, IndexError):
        folder = None

    if folder:
        cfg = load_channel_config(folder, vault_path=vault_path)
        if cfg:
            return cfg

    # 2) frontmatter.channel — scan all channel folders for a match.
    channel_field = frontmatter.get("channel") if frontmatter else None
    if not isinstance(channel_field, str) or not channel_field.strip():
        return None

    # Handle Obsidian wikilinks like "[[Channel Name]]".
    if "[[" in channel_field:
        match = re.search(r"\[\[([^\]|]+)", channel_field)
        if match:
            channel_field = match.group(1).split("(")[0].strip()

    target = channel_field.lower().strip()
    channels_root = vault_path / "Channels"
    if not channels_root.exists():
        return None

    for folder_dir in channels_root.iterdir():
        if not folder_dir.is_dir():
            continue
        cfg = load_channel_config(folder_dir.name, vault_path=vault_path)
        if not cfg:
            continue
        candidates = {
            cfg["folder"].lower(),
            cfg["handle"].lower().lstrip("@"),
            cfg["name"].lower(),
            *(a.lower() for a in cfg.get("aliases", [])),
        }
        if target in candidates:
            return cfg

    return None


# ---------- post-publish helpers ----------

def update_frontmatter(file_path: Path, message_id: int) -> None:
    """Rewrite the draft's frontmatter to mark it as published.

    Adds: type=published, published_date=[[YYYYMMDD]], telegram_message_id.
    Preserves all other frontmatter keys and the body verbatim.
    """
    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = parse_draft_frontmatter(content)
    frontmatter["type"] = "published"
    frontmatter["published_date"] = f"[[{datetime.now().strftime('%Y%m%d')}]]"
    frontmatter["telegram_message_id"] = message_id

    yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    file_path.write_text(f"---\n{yaml_str}---\n\n{body}", encoding="utf-8")


_MD_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_MD_ITALIC_STAR = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_MD_ITALIC_UNDER = re.compile(r"(?<!\w)_([^_\n]+)_(?!\w)")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^\)]+\)")


def extract_first_line(body: str, max_chars: int = 80) -> str:
    """Return the first non-header, non-empty line of ``body``.

    Markdown formatting is stripped. Long lines are truncated with
    an ellipsis so index entries stay on one line.
    """
    for raw in body.strip().split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = _MD_BOLD.sub(r"\1", line)
        line = _MD_ITALIC_STAR.sub(r"\1", line)
        line = _MD_ITALIC_UNDER.sub(r"\1", line)
        line = _MD_LINK.sub(r"\1", line).strip()
        if not line:
            continue
        if len(line) > max_chars:
            line = line[: max_chars - 3] + "..."
        return line
    return "New post"


def update_channel_index(index_path: Path, filename: str, description: str) -> None:
    """Insert a new entry at the top of the channel-index ``Published`` section.

    Expects the index to contain a line like ``**Published**: `published/```.
    Raises ``ValueError`` if that marker isn't found.
    """
    content = index_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    marker = None
    for i, line in enumerate(lines):
        if "**Published**:" in line and "published/" in line:
            marker = i
            break
    if marker is None:
        raise ValueError("Could not find **Published**: section in channel index")

    slug = filename[:-3] if filename.endswith(".md") else filename
    lines.insert(marker + 1, f"- [[{slug}]] — {description}")
    index_path.write_text("\n".join(lines), encoding="utf-8")


def resolve_draft_path(
    draft_path: str,
    vault_path: Path = DEFAULT_VAULT_PATH,
) -> Optional[Path]:
    """Resolve flexible draft references.

    Accepts an absolute path, a path relative to the vault, a filename,
    or a slug without ``.md``. Searches ``Channels/*/drafts/`` for
    filename-only inputs. Returns None when nothing or multiple matches
    are found — callers differentiate using their own glob if they want
    to report ambiguity.
    """
    candidate = Path(draft_path)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None

    full = vault_path / draft_path
    if full.exists():
        return full

    slug = draft_path if draft_path.endswith(".md") else draft_path + ".md"
    matches = list((vault_path / "Channels").glob(f"*/drafts/{slug}"))
    if len(matches) == 1:
        return matches[0]
    return None


# ---------- async orchestration ----------

async def publish_draft(
    client,
    draft_path: str,
    dry_run: bool = False,
    schedule: Optional[datetime] = None,
    vault_path: Path = DEFAULT_VAULT_PATH,
) -> Dict:
    """Publish a draft markdown file to its configured Telegram channel.

    Returns a dict with ``published: bool`` and details. On dry_run,
    returns a preview without sending or mutating the vault.

    Post-publish bookkeeping (frontmatter update, drafts→published move,
    index entry) runs inside a try-block; failures surface as
    ``warnings`` on the result rather than rolling back the send.

    A post-flight lint pass (``detect_unrendered_markup``) scans the
    final body for leaked markdown/HTML and reports any findings under
    ``lint_warnings``.
    """
    draft_file = resolve_draft_path(draft_path, vault_path=vault_path)
    if draft_file is None:
        # Distinguish "not found" from "ambiguous" for the user.
        slug = draft_path if draft_path.endswith(".md") else draft_path + ".md"
        matches = list((vault_path / "Channels").glob(f"*/drafts/{slug}"))
        if len(matches) > 1:
            return {
                "published": False,
                "error": (
                    "Ambiguous draft: "
                    f"found in {[str(m.relative_to(vault_path)) for m in matches]}"
                ),
            }
        return {"published": False, "error": f"Draft file not found: {draft_path}"}

    try:
        content = draft_file.read_text(encoding="utf-8")
        frontmatter, body = parse_draft_frontmatter(content)

        if frontmatter.get("telegram_message_id"):
            return {
                "published": False,
                "error": f"Draft already published (message_id: {frontmatter['telegram_message_id']})",
                "already_published": True,
                "message_id": frontmatter["telegram_message_id"],
            }
        if frontmatter.get("type") == "published":
            return {
                "published": False,
                "error": "Draft type is already 'published'",
                "already_published": True,
            }

        channel_config = resolve_channel_from_draft(
            draft_file, frontmatter, vault_path=vault_path,
        )
        if not channel_config:
            return {
                "published": False,
                "error": (
                    "Could not resolve channel. Draft must live in "
                    "Channels/*/drafts/ or have a valid `channel:` frontmatter field."
                ),
            }

        body = strip_draft_header(body)
        media_filenames = extract_media_references(frontmatter, body)
        try:
            media_paths = (
                resolve_media_paths(media_filenames, vault_path, channel_config["folder"])
                if media_filenames else []
            )
        except FileNotFoundError as exc:
            return {"published": False, "error": str(exc)}

        body = strip_media_wikilinks(body)
        final_body = body if check_footer_exists(body, channel_config) else append_footer(body, channel_config)
        final_body = convert_markdown_to_telegram_html(final_body)

        lint_findings = [f.to_dict() for f in detect_unrendered_markup(final_body)]

        preview = {
            "draft_file": str(draft_file),
            "channel": channel_config["handle"],
            "media_count": len(media_paths),
            "media_files": [p.name for p in media_paths],
            "body_preview": (final_body[:200] + "...") if len(final_body) > 200 else final_body,
        }

        if dry_run:
            preview["published"] = False
            preview["dry_run"] = True
            if lint_findings:
                preview["lint_warnings"] = lint_findings
            return preview

        entity, resolved_name = await resolve_entity(client, channel_config["handle"])
        if entity is None:
            return {
                "published": False,
                "error": f"Could not resolve channel {channel_config['handle']}",
            }

        send_kwargs: Dict = {"parse_mode": "html"}
        if schedule is not None:
            send_kwargs["schedule"] = schedule

        try:
            if media_paths:
                msg = await client.send_file(
                    entity,
                    [str(p) for p in media_paths],
                    caption=final_body,
                    **send_kwargs,
                )
                message_id = msg[0].id if isinstance(msg, list) else msg.id
            else:
                msg = await client.send_message(entity, final_body, **send_kwargs)
                message_id = msg.id
        except Exception as exc:
            return {"published": False, "error": f"Failed to send to Telegram: {exc}"}

        warnings: List[str] = []
        new_path: Optional[Path] = None
        try:
            update_frontmatter(draft_file, message_id)
            published_dir = draft_file.parent.parent / "published"
            published_dir.mkdir(exist_ok=True)
            new_path = published_dir / draft_file.name
            draft_file.rename(new_path)

            index_path = vault_path / "Channels" / channel_config["folder"] / f"{channel_config['folder']}.md"
            if index_path.exists():
                description = extract_first_line(body)
                update_channel_index(index_path, draft_file.name, description)
        except Exception as exc:
            warnings.append(f"Post-publish error: {exc}")
            logger.warning("post-publish bookkeeping failed", exc_info=True)

        result: Dict = {
            "published": True,
            "channel": resolved_name,
            "message_id": message_id,
            "media_count": len(media_paths),
            "moved_to": str(new_path) if new_path else None,
        }
        if schedule is not None:
            result["scheduled_for"] = schedule.isoformat()
        if warnings:
            result["warnings"] = warnings
        if lint_findings:
            result["lint_warnings"] = lint_findings
        return result

    except Exception as exc:
        return {"published": False, "error": f"Unexpected error: {exc}"}


__all__ = [
    "parse_draft_frontmatter",
    "extract_media_references",
    "resolve_media_paths",
    "strip_draft_header",
    "strip_media_wikilinks",
    "check_footer_exists",
    "append_footer",
    "load_channel_config",
    "resolve_channel_from_draft",
    "update_frontmatter",
    "extract_first_line",
    "update_channel_index",
    "resolve_draft_path",
    "publish_draft",
]
