#!/usr/bin/env python3
"""Lab layout registry resolver for agency-docs-updater.

Reads labs.json (skill root) and answers: where do this lab's meeting MDX
files live, what is the public page URL, which YouTube playlist, which
language. Every path-building step must go through this instead of the
legacy hardcoded `{slug}-internal-{lab}` scheme (kept as fallback).

CLI:
  lab_layout.py SLUG [--lab 01] [--meeting 02] [--json]
"""
import json
import sys
from pathlib import Path

REGISTRY = Path(__file__).resolve().parent.parent / "labs.json"

LEGACY = {
    "meetings_dir": "content/docs/{slug}-internal-{lab}/meetings",
    "page_url": "/{slug}-lab-{lab}/meetings/{meeting}",
    "playlist": "{title} Lab {lab}",
    "lang": "ru",
    "thumbnail_style": "claude-code",
}


def load_registry() -> dict:
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (OSError, json.JSONDecodeError):
        return {}


def resolve(slug: str, lab: str = "01", meeting: str = "01") -> dict:
    """Return dict with meetings_dir, page_url, playlist, lang, thumbnail_style,
    site_slug, preserve_placeholder_frontmatter, registered(bool)."""
    reg = load_registry()
    entry = reg.get(slug)
    registered = entry is not None
    if entry is None:
        title = slug.replace("-", " ").title().replace("Ai ", "AI ")
        entry = {k: v.replace("{title}", title) if isinstance(v, str) else v
                 for k, v in LEGACY.items()}
    merged = dict(entry)
    fmt = {"slug": slug, "lab": str(lab).zfill(2), "meeting": str(meeting).zfill(2)}
    for key in ("meetings_dir", "page_url", "playlist"):
        if key in merged and isinstance(merged[key], str):
            merged[key] = merged[key].format(**fmt)
    merged.setdefault("site_slug", slug)
    merged.setdefault("lang", "ru")
    merged.setdefault("thumbnail_style", "claude-code")
    merged.setdefault("preserve_placeholder_frontmatter", False)
    merged["registered"] = registered
    return merged


def all_meeting_dirs() -> list:
    """Relative meetings dirs for every registered lab (lab placeholder globbed)."""
    dirs = []
    for slug, entry in load_registry().items():
        d = entry.get("meetings_dir")
        if d:
            dirs.append(d.replace("{lab}", "*"))
    return dirs


def main():
    args = [a for a in sys.argv[1:]]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    lab, meeting = "01", "01"
    if "--lab" in args:
        i = args.index("--lab"); lab = args[i + 1]; del args[i:i + 2]
    if "--meeting" in args:
        i = args.index("--meeting"); meeting = args[i + 1]; del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit(2)
    r = resolve(args[0], lab, meeting)
    if as_json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        for k, v in r.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
