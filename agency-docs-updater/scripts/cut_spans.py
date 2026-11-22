#!/usr/bin/env python3
"""Cut time spans out of a video (tech difficulties, screen-share fumbling).

Usage:
  cut_spans.py input.mp4 --remove 1245-1270 --remove 781-821 [-o output.mp4]
  cut_spans.py input.mp4 --spans-json spans.json   # [{"start":..,"end":..}, ...]
  cut_spans.py ... --max-remove 0.35               # raise the safety cap (pause editing)

Re-encodes (libx264 veryfast, aac) — frame-accurate cuts; expect roughly
realtime-or-faster encoding for talking-head content. Refuses to remove more
than 15% of total duration by default (safety; --max-remove to change). Spans are
merged and clamped. >20 spans switch to a single-pass select/aselect filter
(scales to hundreds of pause cuts; trim/concat re-decodes per segment).
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
    inp, out, spans, cap = None, None, [], MAX_REMOVE_FRACTION
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
        elif a == "--max-remove":
            cap = float(argv[i + 1])
            i += 2
        elif a == "-o":
            out = argv[i + 1]
            i += 2
        else:
            inp = a
            i += 1
    return inp, out, spans, cap


def main():
    inp, out, spans, cap = parse_args(sys.argv[1:])
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
    if removed > dur * cap:
        print(f"REFUSED: removing {removed:.0f}s of {dur:.0f}s "
              f"(> {cap:.0%}) — check the spans", file=sys.stderr)
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

    graph = "".join(filt)
    if len(merged) > 20:
        # Single pass. Both streams go through the SAME timeline map
        #   new_t = t - (seconds removed before t)
        # instead of frame-count timestamps (N/FRAME_RATE, N/SR), which drift
        # with whole-frame audio drops and variable-frame-rate Zoom files.
        # Half-open [s,e) so a frame on a boundary is never double-dropped.
        # ffmpeg's expression parser fails ("Cannot allocate memory") on one expression
        # with ~145 terms (GDA 01: 145 pause cuts). Chain filters of GROUP terms each:
        # selects in any order (all test ORIGINAL t); setpts groups LATEST FIRST, so for a
        # frame after a later span, t - len_later >= that span's start >= every earlier
        # span's end, and the earlier groups' gte(T, end) tests still hold.
        GROUP = 25
        groups = [merged[i:i + GROUP] for i in range(0, len(merged), GROUP)]
        cond = lambda g: "+".join(f"gte(t,{s:.4f})*lt(t,{e:.4f})" for s, e in g)
        shift = lambda g: "+".join(f"gte(T,{e:.4f})*{e - s:.4f}" for s, e in g)
        vsel = ",".join(f"select='not({cond(g)})'" for g in groups)
        asel = ",".join(f"aselect='not({cond(g)})'" for g in groups)
        vpts = ",".join(f"setpts='PTS-({shift(g)})/TB'" for g in reversed(groups))
        apts = ",".join(f"asetpts='PTS-({shift(g)})/TB'" for g in reversed(groups))
        graph = (f"[0:v]{vsel},{vpts}[outv];"
                 f"[0:a]asetnsamples=n=256,{asel},{apts},aresample=async=1:first_pts=0[outa]")
    script = Path(out).with_suffix(".filter.txt")
    script.write_text(graph)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-i", inp,
           "-/filter_complex", str(script), "-map", "[outv]", "-map", "[outa]",
           # Zoom MP4s carry a chapter/text track; ffmpeg copies chapters by default,
           # leaving markers on the OLD timeline past the new end (GDA 01 #02).
           "-map_chapters", "-1", "-dn",
           "-fps_mode", "vfr", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "faststart", out]
    print(f"cut: removing {len(merged)} span(s), {removed:.0f}s total; "
          f"keeping {len(keep)} segment(s)")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(f"cut: ffmpeg failed ({r.returncode}): {r.stderr.strip()[-600:]}", file=sys.stderr)
        print(f"cut: filter graph kept for debugging: {script}", file=sys.stderr)
        sys.exit(r.returncode)
    script.unlink(missing_ok=True)
    print(f"cut: wrote {out} ({probe_duration(out):.0f}s, was {dur:.0f}s)")


if __name__ == "__main__":
    main()
