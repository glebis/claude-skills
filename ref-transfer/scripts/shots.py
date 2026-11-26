#!/usr/bin/env python3
"""Turn a reference video into a measured shot list: shots, stills, motion, beat alignment, board.

Usage:
  shots.py VIDEO -o OUTDIR [--threshold 0.15] [--merge 0.25] [--min-shot 0.6] [--song SONG.json]

Writes into OUTDIR:
  shots.json    one record per shot: n, start, end, dur, still, motion (mean luma change), motion_peak,
                beats_in_shot, cut_on_beat (distance from the cut to the nearest beat, s), hits (song hits inside)
  shots.md      the same as a table, with empty columns (what / camera / type / sound) for the agent to fill
  stills/       one JPG per shot, from the shot's middle
  board.png     the stills tiled with shot number, timecode and duration

Cuts come from `raea media cuts`, beats from `raea song` (run it if --song is not given).
Soft transitions (morphs, push-ins) give clusters of weak cuts; --merge folds a cluster into one cut and
--threshold drops weak ones. Shots shorter than --min-shot are merged into the previous shot.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def probe_duration(video):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]).strip())


def detect_cuts(video, threshold, merge):
    raw = json.loads(run(["raea", "media", "cuts", str(video)]))["cuts"]
    clusters = []
    for c in raw:
        if clusters and c["at"] - clusters[-1][-1]["at"] <= merge:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    cuts = []
    for cl in clusters:
        best = max(cl, key=lambda c: c["score"])
        if best["score"] >= threshold:
            cuts.append({"at": cl[0]["at"], "score": round(best["score"], 3), "soft": len(cl) > 1 or best["score"] < 0.4})
    return cuts


def motion_curve(video, fps=6):
    """Per-frame mean absolute luma difference (YDIF) at a low frame rate: a cheap 'how much moves' curve."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vf",
         f"fps={fps},scale=240:-2,signalstats,metadata=print:key=lavfi.signalstats.YDIF:file=-",
         "-f", "null", "-"], capture_output=True, text=True).stdout
    pts, vals = [], []
    for line in out.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            pts.append(float(m.group(1)))
        m = re.search(r"YDIF=([\d.]+)", line)
        if m:
            vals.append(float(m.group(1)))
    return list(zip(pts, vals))


def still(video, t, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                    "-vf", "scale=640:-2", "-q:v", "3", str(path)], check=True)


def tc(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def board(shots, outdir, cols=6):
    from PIL import Image, ImageDraw, ImageFont
    tiles = [Image.open(outdir / s["still"]) for s in shots]
    w, h = tiles[0].size
    pad, label = 12, 40
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + label + pad) + pad), (18, 18, 20))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/SFNSMono.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    for i, (s, t) in enumerate(zip(shots, tiles)):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + label + pad)
        img.paste(t, (x, y))
        d.text((x, y + h + 8), f"{s['n']:02d}  {tc(s['start'])}  {s['dur']:.1f}s", fill=(230, 230, 230), font=font)
    img.save(outdir / "board.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--threshold", type=float, default=0.15)
    ap.add_argument("--merge", type=float, default=0.25)
    ap.add_argument("--min-shot", type=float, default=0.6)
    ap.add_argument("--song", help="existing raea song JSON; otherwise raea song is run")
    a = ap.parse_args()

    video, outdir = Path(a.video).resolve(), Path(a.out).resolve()
    (outdir / "stills").mkdir(parents=True, exist_ok=True)
    dur = probe_duration(video)

    song_path = Path(a.song) if a.song else outdir / "song.json"
    if not song_path.exists():
        subprocess.run(["raea", "song", str(video), "-o", str(song_path), "--srt", "none",
                        "--plot", str(outdir / "song.png")], check=True, capture_output=True)
    song = json.loads(song_path.read_text())
    beats = song.get("beats", [])
    events = song.get("events", [])
    hits = [e["time"] for e in events if e.get("kind") == "hit"]

    cuts = detect_cuts(video, a.threshold, a.merge)
    bounds = [0.0] + [c["at"] for c in cuts] + [dur]
    soft = {c["at"]: c["soft"] for c in cuts}
    spans = []
    for s, e in zip(bounds, bounds[1:]):
        if spans and e - s < a.min_shot:
            spans[-1] = (spans[-1][0], e)
        else:
            spans.append((s, e))

    curve = motion_curve(video)
    shots = []
    for i, (s, e) in enumerate(spans, 1):
        vals = [v for t, v in curve if s <= t < e] or [0.0]
        mid = s + (e - s) / 2
        name = f"stills/shot-{i:02d}.jpg"
        still(video, mid, outdir / name)
        near = min(beats, key=lambda b: abs(b - s)) if beats else None
        shots.append({
            "n": i, "start": round(s, 3), "end": round(e, 3), "dur": round(e - s, 3),
            "transition_in": "start" if i == 1 else ("soft" if soft.get(s) else "cut"),
            "still": name,
            "motion": round(sum(vals) / len(vals), 2), "motion_peak": round(max(vals), 2),
            "beats_in_shot": sum(1 for b in beats if s <= b < e),
            "cut_on_beat": None if near is None or i == 1 else round(s - near, 3),
            "hits": [round(h, 2) for h in hits if s <= h < e],
        })

    meta = {"video": str(video), "duration": round(dur, 3), "tempo": song.get("tempo"),
            "sections": [{k: x[k] for k in ("name", "time", "end", "energy") if k in x} for x in song.get("sections", [])],
            "shots": shots}
    (outdir / "shots.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    lines = [f"# Shot list: {video.name}", "",
             f"{len(shots)} shots, {dur:.1f} s, tempo {song.get('tempo')} BPM, mean shot {dur / len(shots):.1f} s", "",
             "| # | in | dur | trans | motion | beats | cut-beat | what the shot does | camera | type / UI motion | sound |",
             "|---|----|-----|-------|--------|-------|----------|----|----|----|----|"]
    for s in shots:
        lines.append(f"| {s['n']} | {tc(s['start'])} | {s['dur']:.1f} | {s['transition_in']} | {s['motion']} | "
                     f"{s['beats_in_shot']} | {s['cut_on_beat'] if s['cut_on_beat'] is not None else ''} |  |  |  |  |")
    (outdir / "shots.md").write_text("\n".join(lines) + "\n")
    board(shots, outdir)
    print(json.dumps({"shots": len(shots), "duration": round(dur, 2), "tempo": song.get("tempo"),
                      "out": str(outdir)}))


if __name__ == "__main__":
    sys.exit(main())
