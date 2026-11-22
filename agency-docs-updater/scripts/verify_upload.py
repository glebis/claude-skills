#!/usr/bin/env python3
"""Verify a YouTube upload (Step 3a) and, only if fully verified, trash local recordings.

  YT=$YOUTUBE_UPLOADER_DIR
  $YT/.venv/bin/python verify_upload.py VIDEO_ID --uploaded EDITED.mp4 \
      [--trash RAW.mp4 EDITED.mp4 …] [--wait 1200]

"Fully verified" is stricter than "safe to continue the pipeline":
  - the video exists and is not rejected/failed,
  - uploadStatus == processed AND processingStatus == succeeded
    (merely "uploaded" can still fail processing, and then you need the file to re-upload),
  - YouTube's duration matches the uploaded file within DURATION_TOLERANCE_S
    (catches uploading the wrong file, e.g. only part 2 of a split recording, GDA 01 #05).

Files go to the macOS Trash via the `trash` CLI; never rm. If `trash` is missing, nothing is deleted.

Exit codes: 0 verified (files trashed if requested) · 1 failed (rejected, failed, wrong
duration) · 2 not ready before --wait ran out (files kept; re-run later).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

DURATION_TOLERANCE_S = 5


def parse_iso_duration(s):
    """YouTube contentDetails.duration (ISO 8601, e.g. PT1H45M3S) → seconds."""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", s or "")
    if not m:
        raise ValueError(f"bad ISO duration: {s!r}")
    d, h, mi, se = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + se


def assess(item, local_duration=None):
    """Decide from a videos.list item. Returns (state, reason); state ∈ ok | wait | fail.
    Only "ok" allows trashing local files."""
    if not item:
        return "wait", "video not visible yet"
    status = item.get("status", {})
    if status.get("rejectionReason"):
        return "fail", f"rejected: {status['rejectionReason']}"
    upload = status.get("uploadStatus")
    if upload in ("failed", "deleted", "rejected"):
        return "fail", f"uploadStatus={upload} ({status.get('failureReason', 'no reason')})"
    processing = item.get("processingDetails", {}).get("processingStatus")
    if processing in ("failed", "terminated"):
        return "fail", f"processingStatus={processing}"
    if upload != "processed" or processing != "succeeded":
        return "wait", f"uploadStatus={upload}, processingStatus={processing}"
    if local_duration is not None:
        yt = parse_iso_duration(item.get("contentDetails", {}).get("duration"))
        if abs(yt - local_duration) > DURATION_TOLERANCE_S:
            return "fail", f"duration mismatch: YouTube {yt}s vs local {local_duration:.0f}s"
    return "ok", "processed, succeeded, duration matches"


def trash_files(paths, verified):
    """Move existing files to the Trash. Refuses unless verified. Returns trashed paths."""
    if not verified:
        return []
    if not shutil.which("trash"):
        print("✗ `trash` CLI not found; keeping files (install: brew install trash)")
        return []
    done = []
    for p in map(Path, paths):
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        if subprocess.run(["trash", str(p)]).returncode == 0:
            done.append(p)
            print(f"  trashed: {p}")
        else:
            print(f"  ✗ could not trash: {p}")
    return done


def local_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video_id")
    ap.add_argument("--uploaded", help="the file that was uploaded, for the duration check")
    ap.add_argument("--trash", nargs="*", default=[], help="files to trash once fully verified")
    ap.add_argument("--wait", type=int, default=1200, help="seconds to wait for processing (default 1200)")
    ap.add_argument("--interval", type=int, default=30)
    a = ap.parse_args()

    dur = local_duration(a.uploaded) if a.uploaded else None
    a.trash = [str(Path(p).resolve()) for p in a.trash]           # before chdir below
    uploader = os.path.expanduser(os.environ.get("YOUTUBE_UPLOADER_DIR", "~/ai_projects/youtube-uploader"))
    os.chdir(uploader)                                             # auth.py reads token/secrets from cwd
    sys.path.insert(0, uploader)
    from auth import get_authenticated_service  # noqa: E402  (youtube-uploader)

    youtube = get_authenticated_service()
    deadline = time.time() + a.wait
    while True:
        items = youtube.videos().list(part="status,processingDetails,contentDetails", id=a.video_id).execute()["items"]
        state, why = assess(items[0] if items else None, dur)
        print(f"{a.video_id}: {state} — {why}")
        if state != "wait" or time.time() >= deadline:
            break
        time.sleep(a.interval)

    if state == "ok":
        print(f"✓ Video {a.video_id} verified OK")
        trash_files(a.trash, verified=True)
        return 0
    if a.trash:
        print(f"  keeping {len(a.trash)} local file(s): verification {state}")
    return 1 if state == "fail" else 2


if __name__ == "__main__":
    sys.exit(main())
