#!/usr/bin/env python3
"""Cut time spans out of a video (tech difficulties, screen-share fumbling).

Usage:
  cut_spans.py input.mp4 --remove 1245-1270 --remove 781-821 [-o output.mp4]
  cut_spans.py input.mp4 --spans-json spans.json   # [{"start":..,"end":..}, ...]

Re-encodes (libx264 veryfast, aac) — frame-accurate cuts; expect roughly
realtime-or-faster encoding for talking-head content. Refuses to remove more
than 15% of total duration (safety). Spans are merged and clamped.
"""
import json
import subprocess
import sys
from pathlib import Path

MAX_REMOVE_FRACTION = 0.15


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def parse_args(argv):
    inp, out, spans = None, None, []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--remove":
            s, e = argv[i + 1].split("-")
            spans.append((float(s), float(e)))
            i += 2
        elif a == "--spans-json":
            data = json.loads(Path(argv[i + 1]).read_text())
            spans += [(float(d["start"]), float(d["end"])) for d in data]
            i += 2
        elif a == "-o":
            out = argv[i + 1]
            i += 2
        else:
            inp = a
            i += 1
    return inp, out, spans


def main():
    inp, out, spans = parse_args(sys.argv[1:])
    if not inp or not spans:
        print(__doc__)
        sys.exit(2)
    out = out or str(Path(inp).with_suffix("")) + ".cut.mp4"

    dur = probe_duration(inp)
    spans = sorted((max(0.0, s), min(dur, e)) for s, e in spans if e > s)
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    removed = sum(e - s for s, e in merged)
    if removed > dur * MAX_REMOVE_FRACTION:
        print(f"REFUSED: removing {removed:.0f}s of {dur:.0f}s "
              f"(> {MAX_REMOVE_FRACTION:.0%}) — check the spans", file=sys.stderr)
        sys.exit(1)

    # Keep-segments between removed spans
    keep, pos = [], 0.0
    for s, e in merged:
        if s - pos > 0.5:
            keep.append((pos, s))
        pos = e
    if dur - pos > 0.5:
        keep.append((pos, dur))

    parts_v, parts_a, filt = [], [], []
    for i, (s, e) in enumerate(keep):
        filt.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},setpts=PTS-STARTPTS[v{i}];")
        filt.append(f"[0:a]atrim=start={s:.3f}:end={e:.3f},asetpts=PTS-STARTPTS[a{i}];")
        parts_v.append(f"[v{i}]")
        parts_a.append(f"[a{i}]")
    filt.append("".join(x for pair in zip(parts_v, parts_a) for x in pair)
                + f"concat=n={len(keep)}:v=1:a=1[outv][outa]")

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-i", inp,
           "-filter_complex", "".join(filt), "-map", "[outv]", "-map", "[outa]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "faststart", out]
    print(f"cut: removing {len(merged)} span(s), {removed:.0f}s total; "
          f"keeping {len(keep)} segment(s)")
    subprocess.run(cmd, check=True)
    print(f"cut: wrote {out} ({probe_duration(out):.0f}s, was {dur:.0f}s)")


if __name__ == "__main__":
    main()
