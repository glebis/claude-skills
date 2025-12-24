"""Image downloading with magic byte detection for proper extensions."""

import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib import error, parse, request


def detect_image_type_from_bytes(data: bytes) -> Optional[str]:
    """Detect image type from magic bytes."""
    signatures = {
        b'\x89PNG\r\n\x1a\n': '.png',
        b'\xff\xd8\xff': '.jpg',
        b'GIF87a': '.gif',
        b'GIF89a': '.gif',
        b'RIFF': '.webp',  # WebP starts with RIFF....WEBP
        b'BM': '.bmp',
    }
    for sig, ext in signatures.items():
        if data.startswith(sig):
            if ext == '.webp' and b'WEBP' not in data[:12]:
                continue
            return ext
    return None


def slugify(value: str, fallback: str = "image") -> str:
    """Create URL-safe slug from string."""
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or fallback


def pick_extension(link: str, mime: Optional[str]) -> str:
    """Determine file extension from MIME type or URL."""
    if mime:
        ext = mimetypes.guess_extension(mime.split(";")[0].strip())
        if ext in {".jpe", ".jpeg"}:
            return ".jpg"
        if ext:
            return ext
    path = parse.urlsplit(link).path
    _, ext = os.path.splitext(path)
    if ext:
        return ext
    return ".bin"


def download_single_image(url: str, dest: Path) -> Tuple[bool, Optional[str]]:
    """Download a single image to destination path."""
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except error.URLError as err:
        return False, f"Failed to download {url}: {err}"
    except TimeoutError:
        return False, f"Timeout downloading {url}"
    dest.write_bytes(data)
    return True, None


def download_all_images(
    results: Iterable[Dict[str, Any]],
    download_dir: Path,
) -> int:
    """Download all images from results, detecting proper extensions."""
    download_dir.mkdir(parents=True, exist_ok=True)
    total_downloaded = 0

    for bundle in results:
        heading = bundle["entry"].get("heading") or bundle["entry"].get("id", "section")
        section_slug = slugify(heading)

        for idx, item in enumerate(bundle["results"], start=1):
            link = item.get("link")
            if not link:
                continue

            ext = pick_extension(link, item.get("mime"))
            filename = f"{section_slug}-{idx:02d}{ext}"
            destination = download_dir / filename

            success, err = download_single_image(link, destination)
            if success:
                # If extension unknown, detect from magic bytes and rename
                if ext == ".bin":
                    data = destination.read_bytes()
                    detected_ext = detect_image_type_from_bytes(data)
                    if detected_ext:
                        new_destination = destination.with_suffix(detected_ext)
                        destination.rename(new_destination)
                        destination = new_destination

                item["localPath"] = str(destination)
                total_downloaded += 1
            else:
                item["downloadError"] = err

    return total_downloaded


def download_best_images(
    results: Iterable[Dict[str, Any]],
    download_dir: Path,
) -> int:
    """Download only the best (final choice or top scored) images."""
    download_dir.mkdir(parents=True, exist_ok=True)
    total_downloaded = 0

    for bundle in results:
        heading = bundle["entry"].get("heading") or bundle["entry"].get("id", "section")
        section_slug = slugify(heading)

        # Find best image: finalChoice or top scored
        best_item = None
        for item in bundle["results"]:
            if item.get("finalChoice"):
                best_item = item
                break

        if not best_item and bundle["results"]:
            # Fall back to highest scored
            sorted_items = sorted(
                bundle["results"],
                key=lambda x: x.get("evaluation", {}).get("score", float("-inf")),
                reverse=True,
            )
            best_item = sorted_items[0]

        if not best_item or not best_item.get("link"):
            continue

        link = best_item["link"]
        ext = pick_extension(link, best_item.get("mime"))
        filename = f"{section_slug}{ext}"
        destination = download_dir / filename

        success, err = download_single_image(link, destination)
        if success:
            if ext == ".bin":
                data = destination.read_bytes()
                detected_ext = detect_image_type_from_bytes(data)
                if detected_ext:
                    new_destination = destination.with_suffix(detected_ext)
                    destination.rename(new_destination)
                    destination = new_destination

            best_item["localPath"] = str(destination)
            total_downloaded += 1
        else:
            best_item["downloadError"] = err

    return total_downloaded
