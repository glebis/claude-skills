"""Obsidian vault detection and note enrichment."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def detect_obsidian_vault(path: Path) -> Optional[Path]:
    """Check if path is in an Obsidian vault, return vault root."""
    current = path.resolve()
    if current.is_file():
        current = current.parent

    while current != current.parent:
        if (current / ".obsidian").is_dir():
            return current
        current = current.parent

    return None


def get_attachments_folder(vault_root: Path, default: str = "Attachments") -> Path:
    """Get configured attachments folder from vault settings."""
    app_json = vault_root / ".obsidian" / "app.json"

    if app_json.exists():
        try:
            settings = json.loads(app_json.read_text(encoding="utf-8"))
            attachment_path = settings.get("attachmentFolderPath", default)
            if attachment_path:
                return vault_root / attachment_path
        except (json.JSONDecodeError, KeyError):
            pass

    return vault_root / default


def extract_headings(note_content: str) -> List[Tuple[str, int, int]]:
    """Extract markdown headings with their levels and line positions.

    Returns: [(heading_text, level, line_number), ...]
    """
    headings = []
    lines = note_content.split("\n")

    for line_num, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((text, level, line_num))

    return headings


def extract_frontmatter(note_content: str) -> Tuple[Optional[Dict], str]:
    """Extract YAML frontmatter from note content.

    Returns: (frontmatter_dict or None, content_without_frontmatter)
    """
    if not note_content.startswith("---"):
        return None, note_content

    lines = note_content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return None, note_content

    frontmatter_lines = lines[1:end_idx]
    content_lines = lines[end_idx + 1:]

    # Simple YAML parsing (key: value)
    frontmatter = {}
    for line in frontmatter_lines:
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip()

    return frontmatter, "\n".join(content_lines)


def find_heading_line(note_content: str, heading_text: str) -> Optional[int]:
    """Find line number for a specific heading."""
    headings = extract_headings(note_content)
    for text, _, line_num in headings:
        if text.lower() == heading_text.lower():
            return line_num
    return None


def insert_image_after_heading(
    note_content: str,
    heading_text: str,
    image_embed: str,
) -> str:
    """Insert image embed after specified heading."""
    lines = note_content.split("\n")
    heading_line = find_heading_line(note_content, heading_text)

    if heading_line is None:
        # Heading not found, append at end
        return note_content + "\n\n" + image_embed

    # Insert after heading line
    insert_pos = heading_line + 1

    # Skip any empty lines right after heading
    while insert_pos < len(lines) and not lines[insert_pos].strip():
        insert_pos += 1

    # Insert image with blank lines
    lines.insert(insert_pos, "")
    lines.insert(insert_pos + 1, image_embed)
    lines.insert(insert_pos + 2, "")

    return "\n".join(lines)


def insert_images_below_headings(
    note_content: str,
    images: Dict[str, str],  # {heading: image_embed}
) -> str:
    """Insert image embeds below relevant headings.

    Args:
        note_content: The note content
        images: Dict mapping heading text to image embed string
    """
    for heading, embed in images.items():
        note_content = insert_image_after_heading(note_content, heading, embed)

    return note_content


def format_obsidian_embed(
    filename: str,
    alt_text: Optional[str] = None,
    width: Optional[int] = None,
) -> str:
    """Format as Obsidian-style image embed.

    Examples:
        ![[image.png]]
        ![[image.png|alt text]]
        ![[image.png|500]]
    """
    if alt_text and width:
        return f"![[{filename}|{alt_text}|{width}]]"
    elif alt_text:
        return f"![[{filename}|{alt_text}]]"
    elif width:
        return f"![[{filename}|{width}]]"
    else:
        return f"![[{filename}]]"


def format_standard_embed(
    path_or_url: str,
    alt_text: str = "Image",
) -> str:
    """Format as standard markdown image embed."""
    # Escape brackets in alt text
    alt_text = alt_text.replace("[", "(").replace("]", ")")
    return f"![{alt_text}]({path_or_url})"


def find_best_heading_match(
    target: str,
    headings: List[str],
) -> Optional[str]:
    """Find best matching heading using partial matching."""
    if not target or not headings:
        return None

    target_lower = target.lower()

    # Try exact match first
    for h in headings:
        if h.lower() == target_lower:
            return h

    # Try if target is contained in heading (handles "1. AI Safety" matching "AI Safety")
    for h in headings:
        if target_lower in h.lower():
            return h

    # Try if heading is contained in target
    for h in headings:
        if h.lower() in target_lower:
            return h

    # Try word overlap
    target_words = set(target_lower.split())
    best_match = None
    best_overlap = 0
    for h in headings:
        h_words = set(h.lower().split())
        overlap = len(target_words & h_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = h

    if best_overlap >= 2:  # At least 2 words overlap
        return best_match

    return None


def map_terms_to_headings(
    terms: List[Dict[str, Any]],
    headings: List[Tuple[str, int, int]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Map extracted terms to their target headings using fuzzy matching.

    Returns: {heading_text: [term_entries]}
    """
    heading_texts = [h[0] for h in headings]
    result: Dict[str, List[Dict[str, Any]]] = {}

    for term in terms:
        target_heading = term.get("heading")

        # Try fuzzy matching
        matched_heading = find_best_heading_match(target_heading, heading_texts)

        if matched_heading:
            result.setdefault(matched_heading, []).append(term)
        elif heading_texts:
            # Assign to first heading if no match found
            result.setdefault(heading_texts[0], []).append(term)
        else:
            # No headings in document
            result.setdefault("", []).append(term)

    return result


def create_backup(note_path: Path) -> Path:
    """Create backup of note before modification."""
    backup_path = note_path.with_suffix(note_path.suffix + ".bak")
    backup_path.write_text(note_path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def enrich_note_with_images(
    note_path: Path,
    images_by_heading: Dict[str, Dict[str, Any]],  # {heading: best_image_item}
    attachments_folder: Path,
    use_obsidian_embeds: bool = True,
    create_backup_file: bool = True,
) -> str:
    """Enrich note by inserting images below headings.

    Args:
        note_path: Path to the note file
        images_by_heading: Dict mapping heading text to best image item
        attachments_folder: Where images are saved
        use_obsidian_embeds: Use ![[]] format vs standard markdown
        create_backup_file: Create .bak file before modifying

    Returns: Modified note content
    """
    note_content = note_path.read_text(encoding="utf-8")

    if create_backup_file:
        create_backup(note_path)

    image_embeds = {}
    for heading, item in images_by_heading.items():
        local_path = item.get("localPath")
        if not local_path:
            continue

        filename = Path(local_path).name
        alt_text = item.get("title", "Image")

        if use_obsidian_embeds:
            embed = format_obsidian_embed(filename, alt_text)
        else:
            # Use relative path from note to attachments
            embed = format_standard_embed(local_path, alt_text)

        image_embeds[heading] = embed

    return insert_images_below_headings(note_content, image_embeds)
