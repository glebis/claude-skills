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

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


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
]
