#!/usr/bin/env python3
"""Measure how a reference video MOVES: camera vs element motion, motion events and their easing, and how
the motion sits on the music's beat.

Usage:
  motion.py VIDEO -o OUTDIR [--song SONG.json] [--shots shots.json] [--width 320] [--start S] [--end S]

Per frame (dense optical flow, Farneback, on a downscaled grey copy):
  speed       mean flow magnitude, px/frame at --width
  dx, dy      mean flow vector (camera pan / tilt direction when coherent)
  zoom        mean divergence (+ push-in / expand, − pull-out / contract)
  spin        mean curl (rotation)
  coverage    share of pixels moving > 0.5 px (camera move ≈ whole frame; element animation ≈ part of it)
  coherence   |mean vector| / mean magnitude (1 = everything moves the same way)
  kind        static | pan | tilt | push-in | pull-out | element | burst

Motion events = peaks of the smoothed speed curve. For each: onset, peak, end, attack (onset→peak),
decay (peak→end), easing (ease-out = quick attack, long settle; ease-in = slow build, abrupt stop;
ease-in-out = symmetric), overshoot (the dominant direction reverses while still moving), and the
offset of onset and peak to the nearest beat and nearest hit.

Writes OUTDIR/motion.json (frames, events, per-shot summary, beat-sync stats) and OUTDIR/rhythm.png.
"""
import argparse, json, math, random
from pathlib import Path

import cv2
import numpy as np


def flow_series(video, width, start, end):
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if start:
        cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    prev, rows, i = None, [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = start + i / fps
        i += 1
        if end and t > end:
            break
        h = int(frame.shape[0] * width / frame.shape[1])
        g = cv2.cvtColor(cv2.resize(frame, (width, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        if prev is None:
            prev = g
            continue
        f = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        prev = g
        fx, fy = f[..., 0], f[..., 1]
        mag = np.hypot(fx, fy)
        speed = float(mag.mean())
        mx, my = float(fx.mean()), float(fy.mean())
        div = float((np.gradient(fx, axis=1) + np.gradient(fy, axis=0)).mean())
        curl = float((np.gradient(fy, axis=1) - np.gradient(fx, axis=0)).mean())
        # radial component: positive when flow points away from the centre (push-in)
        yy, xx = np.mgrid[0:h, 0:width]
        rx, ry = xx - width / 2, yy - h / 2
        rn = np.hypot(rx, ry) + 1e-6
        radial = float(((fx * rx + fy * ry) / rn).mean())
        rows.append({"t": round(t, 3), "speed": round(speed, 3), "dx": round(mx, 3), "dy": round(my, 3),
                     "zoom": round(radial, 3), "div": round(div, 4), "spin": round(curl, 4),
                     "coverage": round(float((mag > 0.5).mean()), 3),
                     "coherence": round(math.hypot(mx, my) / (speed + 1e-6), 3)})
    cap.release()
    return fps, rows


def classify(r):
    if r["speed"] < 0.15:
        return "static"
    if r["coverage"] > 0.55:
        if abs(r["zoom"]) > 0.35 * r["speed"] and r["coherence"] < 0.5:
            return "push-in" if r["zoom"] > 0 else "pull-out"
        if r["coherence"] > 0.55:
            return "pan" if abs(r["dx"]) >= abs(r["dy"]) else "tilt"
        return "burst"
    return "element"


def smooth(x, k=5):
    k = max(1, k)
    return np.convolve(x, np.ones(k) / k, mode="same")


def find_events(rows, fps, min_peak, min_gap_s=0.25):
    sp = smooth(np.array([r["speed"] for r in rows]), 5)
    n, gap = len(sp), int(min_gap_s * fps)
    peaks = []
    for i in range(1, n - 1):
        if sp[i] >= min_peak and sp[i] >= sp[i - 1] and sp[i] > sp[i + 1]:
            lo, hi = max(0, i - gap), min(n, i + gap + 1)
            if sp[i] == sp[lo:hi].max():
                peaks.append(i)
    events = []
    for p in peaks:
        thr = 0.2 * sp[p]
        a = p
        while a > 0 and sp[a - 1] > thr and sp[a - 1] <= sp[a] + 1e-9:
            a -= 1
        b = p
        while b < n - 1 and sp[b + 1] > thr and sp[b + 1] <= sp[b] + 1e-9:
            b += 1
        attack, decay = (p - a) / fps, (b - p) / fps
        if attack < 0.6 * decay:
            easing = "ease-out"          # snaps in, settles slowly
        elif attack > 1.6 * decay:
            easing = "ease-in"           # builds, stops abruptly
        else:
            easing = "ease-in-out"
        # overshoot: dominant axis of motion reverses after the peak while still moving
        ax = "dx" if abs(rows[p]["dx"]) >= abs(rows[p]["dy"]) else "dy"
        sign = np.sign(rows[p][ax])
        over = any(np.sign(rows[j][ax]) == -sign and abs(rows[j][ax]) > 0.15 * abs(rows[p][ax]) and rows[j]["speed"] > 0.1
                   for j in range(p + 1, min(n, b + int(0.4 * fps))))
        kinds = [classify(rows[j]) for j in range(a, b + 1)]
        kind = max(set(kinds), key=kinds.count)
        events.append({"onset": rows[a]["t"], "peak": rows[p]["t"], "end": rows[b]["t"],
                       "attack": round(attack, 3), "decay": round(decay, 3), "peak_speed": round(float(sp[p]), 2),
                       "easing": easing, "overshoot": bool(over and abs(rows[p][ax]) > 0.2), "kind": kind})
    return events


def nearest(t, grid):
    if not grid:
        return None
    g = min(grid, key=lambda b: abs(b - t))
    return round(t - g, 3)


def sync_stats(times, beats, tol=(0.05, 0.1)):
    """Share of times within tol of a beat, against the share expected by chance (uniform phase)."""
    if not times or len(beats) < 2:
        return {}
    period = float(np.median(np.diff(beats)))
    out = {"n": len(times), "beat_period": round(period, 3)}
    for t in tol:
        hit = sum(1 for x in times if abs(nearest(x, beats)) <= t)
        out[f"within_{int(t * 1000)}ms"] = round(hit / len(times), 2)
        out[f"chance_{int(t * 1000)}ms"] = round(min(1.0, 2 * t / period), 2)
    # mean phase of the events in the beat (0 = on the beat, 0.5 = halfway)
    ph = [((x - beats[0]) / period) % 1.0 for x in times]
    ang = np.angle(np.mean(np.exp(2j * np.pi * np.array(ph))))
    out["mean_phase"] = round(float((ang / (2 * np.pi)) % 1.0), 2)
    out["phase_consistency"] = round(float(abs(np.mean(np.exp(2j * np.pi * np.array(ph))))), 2)
    return out


def plot(rows, events, beats, hits, cuts, shots, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = np.array([r["t"] for r in rows])
    sp = smooth(np.array([r["speed"] for r in rows]), 5)
    colors = {"static": "#3a3d44", "pan": "#4c9be8", "tilt": "#7cc4ff", "push-in": "#f2b134", "pull-out": "#e8743b",
              "element": "#9b7be8", "burst": "#e84c6a"}
    ease_c = {"ease-out": "#5fd38d", "ease-in": "#ff8a65", "ease-in-out": "#ffd54f"}
    fig, axs = plt.subplots(4, 1, figsize=(24, 10), sharex=True, gridspec_kw={"height_ratios": [3, 0.5, 1.6, 1.2]},
                            facecolor="#141518")
    for ax in axs:
        ax.set_facecolor("#141518")
        ax.tick_params(colors="#9aa3b1")
        for s in ax.spines.values():
            s.set_color("#30333a")
    ax = axs[0]
    for b in beats:
        ax.axvline(b, color="#2a2d33", lw=0.8, zorder=0)
    for c in cuts:
        ax.axvline(c, color="#ffffff", lw=1.2, ls="--", alpha=0.6)
    ax.plot(t, sp, color="#e6e8ec", lw=1.4)
    for e in events:
        ax.axvspan(e["onset"], e["end"], color=ease_c[e["easing"]], alpha=0.12)
        ax.plot([e["peak"]], [e["peak_speed"]], "o", color=ease_c[e["easing"]], ms=6)
        if e["overshoot"]:
            ax.plot([e["peak"]], [e["peak_speed"] * 1.12], "^", color="#ffffff", ms=5)
    ymax = max(sp.max() * 1.25, 1)
    for h in hits:
        ax.plot([h], [ymax * 0.95], "v", color="#ff5c8a", ms=7)
    for s in shots:
        ax.text(s["start"] + 0.1, ymax * 0.86, f"{s['n']:02d}", color="#9aa3b1", fontsize=10)
    ax.set_ylim(0, ymax)
    ax.set_ylabel("speed (px/frame)", color="#9aa3b1")
    ax.set_title("Motion vs. music: speed curve, beats (grey), hits (pink ▼), cuts (white --), "
                 "events coloured by easing: ease-out green · ease-in orange · in-out yellow · ▲ overshoot",
                 color="#e6e8ec", loc="left", fontsize=12)
    ax = axs[1]
    kinds = [classify(r) for r in rows]
    for i in range(len(t) - 1):
        ax.axvspan(t[i], t[i + 1], color=colors[kinds[i]], lw=0)
    ax.set_yticks([])
    ax.set_ylabel("kind", color="#9aa3b1")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
    ax.legend(handles, colors.keys(), ncol=7, loc="upper left", bbox_to_anchor=(0, -0.1), frameon=False,
              labelcolor="#9aa3b1", fontsize=9)
    ax = axs[2]
    ax.plot(t, smooth(np.array([r["dx"] for r in rows]), 5), color="#4c9be8", lw=1, label="pan x (→ +)")
    ax.plot(t, smooth(np.array([r["dy"] for r in rows]), 5), color="#7cc4ff", lw=1, label="tilt y (↓ +)")
    ax.plot(t, smooth(np.array([r["zoom"] for r in rows]), 5), color="#f2b134", lw=1.2, label="zoom (+ push-in)")
    ax.axhline(0, color="#30333a", lw=0.8)
    ax.legend(loc="upper right", frameon=False, labelcolor="#9aa3b1", fontsize=9)
    ax.set_ylabel("camera", color="#9aa3b1")
    ax = axs[3]
    ax.fill_between(t, smooth(np.array([r["coverage"] for r in rows]), 5), color="#9b7be8", alpha=0.6)
    ax.set_ylim(0, 1)
    ax.set_ylabel("frame moving", color="#9aa3b1")
    ax.set_xlabel("seconds", color="#9aa3b1")
    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor=fig.get_facecolor())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--song")
    ap.add_argument("--shots")
    ap.add_argument("--width", type=int, default=320)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=0.0)
    ap.add_argument("--min-peak", type=float, default=0.6, help="smallest speed peak that counts as an event")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    fps, rows = flow_series(a.video, a.width, a.start, a.end)
    for r in rows:
        r["kind"] = classify(r)
    song = json.loads(Path(a.song).read_text()) if a.song else {}
    beats = song.get("beats", [])
    hits = [e["time"] for e in song.get("events", []) if e.get("kind") == "hit"]
    shots = json.loads(Path(a.shots).read_text())["shots"] if a.shots else []
    cuts = [s["start"] for s in shots[1:]]

    events = find_events(rows, fps, a.min_peak)
    for e in events:
        e["onset_to_beat"] = nearest(e["onset"], beats)
        e["peak_to_beat"] = nearest(e["peak"], beats)
        e["peak_to_hit"] = nearest(e["peak"], hits)

    per_shot = []
    for s in shots:
        rs = [r for r in rows if s["start"] <= r["t"] < s["end"]]
        es = [e for e in events if s["start"] <= e["peak"] < s["end"]]
        if not rs:
            continue
        kinds = [r["kind"] for r in rs]
        share = {k: round(kinds.count(k) / len(kinds), 2) for k in sorted(set(kinds), key=kinds.count, reverse=True)}
        per_shot.append({"n": s["n"], "start": s["start"], "dur": s["dur"], "kinds": share,
                         "mean_speed": round(float(np.mean([r["speed"] for r in rs])), 2),
                         "events": len(es), "events_per_s": round(len(es) / max(s["dur"], 1e-6), 2),
                         "easing": {k: sum(1 for e in es if e["easing"] == k) for k in ("ease-out", "ease-in", "ease-in-out")},
                         "overshoots": sum(1 for e in es if e["overshoot"]),
                         "median_attack": round(float(np.median([e["attack"] for e in es])), 2) if es else None,
                         "median_decay": round(float(np.median([e["decay"] for e in es])), 2) if es else None})

    allk = [r["kind"] for r in rows]
    summary = {
        "fps": round(fps, 3), "frames": len(rows), "events": len(events),
        "events_per_s": round(len(events) / max(rows[-1]["t"] - rows[0]["t"], 1e-6), 2) if rows else 0,
        "kinds": {k: round(allk.count(k) / len(allk), 2) for k in sorted(set(allk), key=allk.count, reverse=True)},
        "easing": {k: sum(1 for e in events if e["easing"] == k) for k in ("ease-out", "ease-in", "ease-in-out")},
        "overshoots": sum(1 for e in events if e["overshoot"]),
        "median_attack_s": round(float(np.median([e["attack"] for e in events])), 2) if events else None,
        "median_decay_s": round(float(np.median([e["decay"] for e in events])), 2) if events else None,
        "sync_onsets_to_beats": sync_stats([e["onset"] for e in events], beats),
        "sync_peaks_to_beats": sync_stats([e["peak"] for e in events], beats),
        "sync_cuts_to_beats": sync_stats(cuts, beats),
        "peaks_within_100ms_of_a_hit": round(sum(1 for e in events if e["peak_to_hit"] is not None and abs(e["peak_to_hit"]) <= 0.1) / max(len(events), 1), 2),
        "tempo": song.get("tempo"),
    }
    (out / "motion.json").write_text(json.dumps({"summary": summary, "shots": per_shot, "events": events, "frames": rows}, indent=1))
    plot(rows, events, beats, hits, cuts, shots, out / "rhythm.png")
    print(json.dumps({"summary": summary, "shots": per_shot}, indent=1))


if __name__ == "__main__":
    main()
