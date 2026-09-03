#!/usr/bin/env python3
"""
Batch download + transcript pipeline.

Reads YouTube links from a JSON file, downloads each video,
and extracts timestamped transcripts to Markdown.

Usage:
    python3 batch.py videos.json
    python3 batch.py videos.json --download-dir ~/Downloads/yt-videos --transcript-dir ~/Downloads/yt-transcripts

JSON format:
    {
      "videos": [
        {"url": "https://www.youtube.com/watch?v=abc123"},
        {"url": "https://youtu.be/def456", "name": "optional-custom-name"}
      ]
    }
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
EXTRACT_SCRIPT = SCRIPT_DIR / "extract_transcript.py"

DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "yt-dlp"
DEFAULT_TRANSCRIPT_DIR = Path.home() / "Downloads" / "yt-transcripts"

KNOWN_YTDLP_PATHS = [
    Path("/usr/local/bin/yt-dlp"),
    Path("/opt/homebrew/bin/yt-dlp"),
    Path.home() / ".local" / "bin" / "yt-dlp",
]


def find_ytdlp() -> str:
    found = shutil.which("yt-dlp")
    if found:
        return found
    for p in KNOWN_YTDLP_PATHS:
        if p.exists() and os.access(p, os.X_OK):
            return str(p)
    sys.exit("Error: yt-dlp not found. Install it or add it to PATH.")


def load_videos(json_path: str) -> list[dict]:
    with open(json_path) as f:
        data = json.load(f)
    videos = data if isinstance(data, list) else data.get("videos", [])
    for v in videos:
        if isinstance(v, str):
            yield {"url": v}
        else:
            yield v


def download_video(url: str, output_dir: Path, name: str | None = None, ytdlp: str = "yt-dlp") -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    template = f"{output_dir}/{name}.%(ext)s" if name else f"{output_dir}/%(title)s.%(ext)s"

    result = subprocess.run(
        [
            ytdlp,
            "--no-exec",
            "--no-playlist",
            "--restrict-filenames",
            "-o", template,
            url,
        ],
        capture_output=True, text=True,
    )

    if result.returncode != 0:
        print(f"  ERROR downloading: {result.stderr[:200]}")
        return None

    for line in result.stdout.splitlines():
        if "has already been downloaded" in line or "Destination:" in line:
            path_str = line.split("Destination: ")[-1] if "Destination:" in line else line.split(" has already")[0].replace("[download] ", "")
            return Path(path_str.strip())

    merged = [l for l in result.stdout.splitlines() if "Merging" in l]
    if merged:
        return Path(merged[-1].split('"')[1]) if '"' in merged[-1] else None

    candidates = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def extract_transcript(url: str, output_name: str | None = None, ytdlp: str = "yt-dlp") -> bool:
    env = os.environ.copy()
    ytdlp_dir = str(Path(ytdlp).parent)
    env["PATH"] = ytdlp_dir + os.pathsep + env.get("PATH", "")
    cmd = [sys.executable, str(EXTRACT_SCRIPT), url]
    if output_name:
        cmd.append(f"{output_name}.md")

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        stderr = result.stderr[:200] if result.stderr else result.stdout[:200]
        print(f"  ERROR transcript: {stderr}")
        return False

    for line in result.stdout.splitlines():
        if "Saved to" in line or "No subtitles" in line:
            print(f"  {line.strip()}")
    return result.returncode == 0


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 batch.py videos.json [--download-dir DIR] [--transcript-dir DIR]")
        sys.exit(1)

    json_path = Path(sys.argv[1]).expanduser()
    if not json_path.exists():
        parent_dir = SCRIPT_DIR.parent
        alt = parent_dir / json_path.name
        if alt.exists():
            json_path = alt
        else:
            sys.exit(f"Error: file not found: {json_path}")

    download_dir = DEFAULT_DOWNLOAD_DIR
    transcript_dir = DEFAULT_TRANSCRIPT_DIR

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--download-dir" and i + 1 < len(args):
            download_dir = Path(args[i + 1])
            i += 2
        elif args[i] == "--transcript-dir" and i + 1 < len(args):
            transcript_dir = Path(args[i + 1])
            i += 2
        else:
            i += 1

    ytdlp = find_ytdlp()
    print(f"Using yt-dlp: {ytdlp}")

    videos = list(load_videos(str(json_path)))
    print(f"Processing {len(videos)} videos\n")

    results = {"ok": [], "failed": []}

    for idx, video in enumerate(videos, 1):
        url = video["url"]
        name = video.get("name")
        print(f"[{idx}/{len(videos)}] {name or url}")

        print("  Downloading...")
        video_path = download_video(url, download_dir, name, ytdlp=ytdlp)
        if video_path:
            print(f"  Video: {video_path}")
        else:
            print("  Video download failed, continuing to transcript...")

        print("  Extracting transcript...")
        ok = extract_transcript(url, name, ytdlp=ytdlp)

        if ok:
            results["ok"].append(url)
        else:
            results["failed"].append(url)

        print()

    print(f"Done: {len(results['ok'])} ok, {len(results['failed'])} failed")
    if results["failed"]:
        print("Failed:")
        for u in results["failed"]:
            print(f"  - {u}")


if __name__ == "__main__":
    main()
