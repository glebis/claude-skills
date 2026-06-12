#!/usr/bin/env python3
"""
Extract prosodic (audio-based) features from Wispr Flow dictation history.

This is the "prosody" analysis mode -- a peer of technical/soft/trends/mental,
but it reads the recorded WAV audio (History.audio BLOB) instead of text, and
uses Praat (via parselmouth) to extract pitch, intensity, and voice-quality
features as gentle affect/energy proxies for self-reflection.

Usage:
    python3 extract_prosody.py [--period today|yesterday|week|month|YYYY-MM-DD|YYYY-MM-DD:YYYY-MM-DD]
                               [--format text|json] [--limit N] [--output PATH]

AUDIO RETENTION CAVEAT:
    Wispr keeps the recorded audio only for recent dictations (~900 of 16,000+
    rows). Older rows have audio pruned after upload. Prosody is therefore
    available ONLY for recent dictations -- the report surfaces this honestly
    with a coverage line (X of Y dictations in period had audio).

Requires: praat-parselmouth (pip install praat-parselmouth)

The database is opened strictly READ-ONLY; this script never writes to it.
"""

import sqlite3
import json
import argparse
import os
import sys
import tempfile
import statistics
import math
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

try:
    import parselmouth
    from parselmouth.praat import call
except ImportError:
    print("ERROR: praat-parselmouth is required. Install with: pip install praat-parselmouth",
          file=sys.stderr)
    sys.exit(1)

DB_PATH = os.path.expanduser("~/Library/Application Support/Wispr Flow/flow.sqlite")

# Default cap on clips processed to bound runtime (audio analysis is slow vs SQL).
DEFAULT_LIMIT = 300


def parse_period(period_str):
    """Return (start_datetime_str, end_datetime_str) for SQL WHERE clause.

    Mirrors extract_wispr.py period semantics exactly.
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period_str == "today":
        start = today_start
        end = now
    elif period_str == "yesterday":
        start = today_start - timedelta(days=1)
        end = today_start
    elif period_str == "week":
        start = today_start - timedelta(days=7)
        end = now
    elif period_str == "month":
        start = today_start - timedelta(days=30)
        end = now
    elif ":" in period_str:
        parts = period_str.split(":")
        start = datetime.strptime(parts[0], "%Y-%m-%d")
        end = datetime.strptime(parts[1], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    else:
        start = datetime.strptime(period_str, "%Y-%m-%d")
        end = start.replace(hour=23, minute=59, second=59)

    return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")


def _finite(x):
    """Return float(x) if finite, else None (filters Praat inf/nan sentinels)."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def open_readonly(db_path):
    """Open the SQLite DB strictly read-only (immutable URI)."""
    uri = f"file:{db_path}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def count_period(conn, start, end):
    """Return (total_in_period, with_audio_in_period)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN audio IS NOT NULL THEN 1 ELSE 0 END) AS with_audio
        FROM History
        WHERE isArchived = 0
          AND timestamp >= ? AND timestamp <= ?
    """, (start, end))
    r = cur.fetchone()
    return r["total"] or 0, r["with_audio"] or 0


def fetch_audio_rows(conn, start, end, limit):
    """Fetch period rows that have audio, newest first, capped at `limit`."""
    cur = conn.cursor()
    cur.execute("""
        SELECT timestamp, app, numWords, duration, speechDuration,
               detectedLanguage, language, audio
        FROM History
        WHERE isArchived = 0
          AND timestamp >= ? AND timestamp <= ?
          AND audio IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT ?
    """, (start, end, limit))
    return cur.fetchall()


def normalize_language(row):
    lang = row["detectedLanguage"] or row["language"] or "unknown"
    # Collapse locale variants (en-US -> en, ru-RU -> ru)
    if lang and "-" in lang:
        lang = lang.split("-")[0]
    return lang or "unknown"


def analyze_clip(wav_bytes):
    """Extract prosodic features from a single WAV blob using Praat.

    Returns a dict of features, or None if the clip has no voiced frames /
    cannot be analyzed at all. Individual fragile features (jitter/shimmer/HNR)
    are wrapped so they degrade to None instead of failing the whole clip.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(wav_bytes)
            tmp_path = tf.name

        snd = parselmouth.Sound(tmp_path)

        # --- Pitch (F0) ---
        try:
            pitch = snd.to_pitch()
            f0 = pitch.selected_array["frequency"]
            voiced = f0[f0 > 0]  # drop unvoiced frames
        except Exception:
            voiced = []

        if len(voiced) < 3:
            # No usable voiced signal -> skip this clip
            return None

        f0_mean = float(statistics.mean(voiced))
        f0_std = float(statistics.pstdev(voiced)) if len(voiced) > 1 else 0.0
        feat = {
            "f0_mean": f0_mean,
            "f0_median": float(statistics.median(voiced)),
            "f0_min": float(min(voiced)),
            "f0_max": float(max(voiced)),
            "f0_range": float(max(voiced) - min(voiced)),
            "f0_std": f0_std,
            "f0_cv": float(f0_std / f0_mean) if f0_mean else None,  # monotone<->expressive
        }

        # --- Intensity (dB) ---
        try:
            intensity = snd.to_intensity()
            ivals = intensity.values[0]
            ivals = ivals[~(ivals != ivals)]  # drop NaN
            ivals = [float(v) for v in ivals if v > 0]
            if ivals:
                feat["intensity_mean"] = float(statistics.mean(ivals))
                feat["intensity_range"] = float(max(ivals) - min(ivals))
                feat["intensity_std"] = float(statistics.pstdev(ivals)) if len(ivals) > 1 else 0.0
        except Exception:
            pass

        # --- Voice quality: jitter, shimmer, HNR ---
        # These are fragile on short/noisy clips -- degrade gracefully.
        try:
            point_process = call(snd, "To PointProcess (periodic, cc)", 75, 500)
            jitter = _finite(call(point_process, "Get jitter (local)",
                                  0, 0, 0.0001, 0.02, 1.3))
            if jitter is not None:
                feat["jitter_local"] = jitter
            shimmer = _finite(call([snd, point_process], "Get shimmer (local)",
                                   0, 0, 0.0001, 0.02, 1.3, 1.6))
            if shimmer is not None:
                feat["shimmer_local"] = shimmer
        except Exception:
            pass

        try:
            harmonicity = snd.to_harmonicity_cc()
            hnr = _finite(call(harmonicity, "Get mean", 0, 0))
            if hnr is not None and hnr > -200:  # filter undefined sentinel
                feat["hnr"] = hnr
        except Exception:
            pass

        return feat
    except Exception:
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def compute_tempo(row):
    """Speaking rate (WPM) and pause ratio from DB columns (not audio)."""
    numWords = row["numWords"] or 0
    speech = row["speechDuration"] or 0
    total = row["duration"] or 0
    wpm = None
    if speech and speech > 0:
        wpm = numWords / (speech / 60.0)
    pause_ratio = None
    if total and total > 0:
        pause_ratio = max(0.0, (total - speech) / total)
    return wpm, pause_ratio


def _agg(values):
    """Mean/median/min/max/std for a list of numbers, ignoring None."""
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if not vals:
        return None
    return {
        "n": len(vals),
        "mean": round(float(statistics.mean(vals)), 3),
        "median": round(float(statistics.median(vals)), 3),
        "min": round(float(min(vals)), 3),
        "max": round(float(max(vals)), 3),
        "std": round(float(statistics.pstdev(vals)), 3) if len(vals) > 1 else 0.0,
    }


def _wmean(pairs):
    """Weighted mean of (value, weight) pairs, ignoring None values."""
    num = den = 0.0
    for v, w in pairs:
        if v is None or w is None or w <= 0:
            continue
        num += v * w
        den += w
    return round(num / den, 3) if den else None


def aggregate(clips):
    """Aggregate per-clip feature dicts into period-level summaries.

    `clips` is a list of dicts: each has 'feat' (or None), 'lang', 'date',
    'wpm', 'pause_ratio', 'speech'.
    """
    metrics = ["f0_mean", "f0_median", "f0_range", "f0_std", "f0_cv",
               "intensity_mean", "intensity_range", "intensity_std",
               "jitter_local", "shimmer_local", "hnr"]

    overall = {}
    for m in metrics:
        overall[m] = _agg([c["feat"].get(m) for c in clips if c["feat"]])

    # Tempo (from DB, present even when audio feature extraction fails)
    overall["wpm"] = _agg([c["wpm"] for c in clips])
    overall["pause_ratio"] = _agg([c["pause_ratio"] for c in clips])

    # Speech-duration-weighted F0 mean and WPM (longer clips count more)
    overall["f0_mean_weighted"] = _wmean(
        [(c["feat"].get("f0_mean") if c["feat"] else None, c["speech"]) for c in clips]
    )
    overall["wpm_weighted"] = _wmean([(c["wpm"], c["speech"]) for c in clips])

    return overall


def by_language(clips):
    groups = defaultdict(list)
    for c in clips:
        groups[c["lang"]].append(c)
    out = {}
    for lang, cs in sorted(groups.items(), key=lambda x: -len(x[1])):
        out[lang] = {
            "n_clips": len(cs),
            "n_voiced": sum(1 for c in cs if c["feat"]),
            "f0_mean": _agg([c["feat"].get("f0_mean") for c in cs if c["feat"]]),
            "f0_cv": _agg([c["feat"].get("f0_cv") for c in cs if c["feat"]]),
            "wpm": _agg([c["wpm"] for c in cs]),
            "hnr": _agg([c["feat"].get("hnr") for c in cs if c["feat"]]),
        }
    return out


def daily_trend(clips):
    days = defaultdict(list)
    for c in clips:
        days[c["date"]].append(c)
    rows = []
    for day in sorted(days.keys()):
        cs = days[day]
        feats = [c["feat"] for c in cs if c["feat"]]

        def m(key, source=None):
            src = source if source is not None else feats
            vals = [f.get(key) for f in src if f and f.get(key) is not None] if source is None \
                else [x for x in src if x is not None]
            return round(statistics.mean(vals), 1) if vals else None

        rows.append({
            "date": day,
            "n_clips": len(cs),
            "n_voiced": len(feats),
            "f0_mean": m("f0_mean"),
            "f0_cv": (round(statistics.mean([f["f0_cv"] for f in feats if f.get("f0_cv") is not None]), 3)
                      if any(f.get("f0_cv") is not None for f in feats) else None),
            "intensity_mean": m("intensity_mean"),
            "wpm": (round(statistics.mean([c["wpm"] for c in cs if c["wpm"] is not None]), 1)
                    if any(c["wpm"] is not None for c in cs) else None),
            "hnr": m("hnr"),
        })
    return rows


def build_report(period_label, total, with_audio, processed, skipped_no_voice,
                 truncated, limit, clips):
    overall = aggregate(clips)
    langs = by_language(clips)
    trend = daily_trend(clips)
    feature_failures = {
        "jitter": sum(1 for c in clips if c["feat"] and "jitter_local" not in c["feat"]),
        "shimmer": sum(1 for c in clips if c["feat"] and "shimmer_local" not in c["feat"]),
        "hnr": sum(1 for c in clips if c["feat"] and "hnr" not in c["feat"]),
        "intensity": sum(1 for c in clips if c["feat"] and "intensity_mean" not in c["feat"]),
    }
    return {
        "period": period_label,
        "coverage": {
            "total_dictations_in_period": total,
            "dictations_with_audio": with_audio,
            "clips_processed": processed,
            "clips_skipped_no_voice": skipped_no_voice,
            "truncated_by_limit": truncated,
            "limit": limit,
        },
        "overall": overall,
        "by_language": langs,
        "daily_trend": trend,
        "feature_failures": feature_failures,
    }


def _fmt(agg, key="mean", unit=""):
    if not agg or agg.get(key) is None:
        return "n/a"
    return f"{agg[key]}{unit}"


def format_text(report):
    cov = report["coverage"]
    ov = report["overall"]
    lines = []
    lines.append(f"## Wispr Prosody Analysis: {report['period']}")
    lines.append("")
    lines.append(f"**Coverage**: {cov['dictations_with_audio']} of "
                 f"{cov['total_dictations_in_period']} dictations in this period had "
                 f"retained audio. Processed {cov['clips_processed']} clips "
                 f"({cov['clips_skipped_no_voice']} skipped: no voiced frames).")
    if cov["truncated_by_limit"]:
        lines.append(f"> NOTE: more clips had audio than the --limit of {cov['limit']}; "
                     f"coverage is capped. Raise --limit to process all.")
    lines.append("")
    lines.append("_Audio is retained only for recent dictations; older rows are "
                 "timing-only. Treat these as gentle reflection proxies, not measures._")
    lines.append("")

    lines.append("### Pitch (F0) -- monotone <-> expressive")
    f0m = ov.get("f0_mean") or {}
    lines.append(f"- Mean F0: {_fmt(f0m, 'mean', ' Hz')} "
                 f"(median {_fmt(f0m, 'median', ' Hz')}, "
                 f"range {_fmt(f0m, 'min')}-{_fmt(f0m, 'max')} Hz)")
    if ov.get("f0_mean_weighted") is not None:
        lines.append(f"- Mean F0 (speech-duration weighted): {ov['f0_mean_weighted']} Hz")
    lines.append(f"- F0 CV (variability proxy): {_fmt(ov.get('f0_cv'))} "
                 f"(higher = more expressive/varied intonation)")
    lines.append(f"- F0 std: {_fmt(ov.get('f0_std'), 'mean', ' Hz')}, "
                 f"range {_fmt(ov.get('f0_range'), 'mean', ' Hz')}")
    lines.append("")

    lines.append("### Intensity (loudness dynamics)")
    lines.append(f"- Mean intensity: {_fmt(ov.get('intensity_mean'), 'mean', ' dB')}")
    lines.append(f"- Intensity range: {_fmt(ov.get('intensity_range'), 'mean', ' dB')}, "
                 f"std {_fmt(ov.get('intensity_std'), 'mean', ' dB')}")
    lines.append("")

    lines.append("### Voice quality")
    lines.append(f"- Jitter (local): {_fmt(ov.get('jitter_local'))}")
    lines.append(f"- Shimmer (local): {_fmt(ov.get('shimmer_local'))}")
    lines.append(f"- HNR: {_fmt(ov.get('hnr'), 'mean', ' dB')} "
                 f"(lower can track fatigue/vocal strain)")
    lines.append("")

    lines.append("### Tempo (from timing columns)")
    lines.append(f"- Speaking rate: {_fmt(ov.get('wpm'), 'mean', ' WPM')}")
    if ov.get("wpm_weighted") is not None:
        lines.append(f"- Speaking rate (weighted): {ov['wpm_weighted']} WPM")
    pr = ov.get("pause_ratio") or {}
    lines.append(f"- Pause ratio: {_fmt(pr, 'mean')} "
                 f"(fraction of total time not actively speaking)")
    lines.append("")

    if report["by_language"]:
        lines.append("### By Language")
        lines.append("| Lang | Clips | Voiced | Mean F0 | F0 CV | WPM | HNR |")
        lines.append("|------|-------|--------|---------|-------|-----|-----|")
        for lang, d in report["by_language"].items():
            def cell(a, k="mean"):
                return a[k] if a and a.get(k) is not None else "n/a"
            lines.append(f"| {lang} | {d['n_clips']} | {d['n_voiced']} | "
                         f"{cell(d['f0_mean'])} | {cell(d['f0_cv'])} | "
                         f"{cell(d['wpm'])} | {cell(d['hnr'])} |")
        lines.append("")

    if len(report["daily_trend"]) > 1:
        lines.append("### Daily Trend")
        lines.append("| Date | Clips | Voiced | Mean F0 | F0 CV | Intensity | WPM | HNR |")
        lines.append("|------|-------|--------|---------|-------|-----------|-----|-----|")
        for t in report["daily_trend"]:
            def c(v):
                return v if v is not None else "n/a"
            lines.append(f"| {t['date']} | {t['n_clips']} | {t['n_voiced']} | "
                         f"{c(t['f0_mean'])} | {c(t['f0_cv'])} | "
                         f"{c(t['intensity_mean'])} | {c(t['wpm'])} | {c(t['hnr'])} |")
        lines.append("")

    ff = report["feature_failures"]
    if any(ff.values()):
        lines.append("### Feature extraction notes")
        lines.append(f"- Voiced clips where a feature could not be computed: "
                     f"jitter {ff['jitter']}, shimmer {ff['shimmer']}, "
                     f"HNR {ff['hnr']}, intensity {ff['intensity']}.")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract prosodic (audio-based) features from Wispr Flow history")
    parser.add_argument("--period", default="today",
                        help="today, yesterday, week, month, YYYY-MM-DD, or "
                             "YYYY-MM-DD:YYYY-MM-DD")
    parser.add_argument("--format", default="text", choices=["text", "json"],
                        help="Output format")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"Max clips to process (default {DEFAULT_LIMIT}). "
                             "Logs when coverage is truncated.")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    start, end = parse_period(args.period)
    period_label = (f"{start} to {end}"
                    if args.period not in ("today", "yesterday", "week", "month")
                    else args.period)

    conn = open_readonly(DB_PATH)
    total, with_audio = count_period(conn, start, end)
    rows = fetch_audio_rows(conn, start, end, args.limit)
    conn.close()

    truncated = with_audio > args.limit
    if truncated:
        print(f"[prosody] NOTE: {with_audio} clips have audio but --limit={args.limit}; "
              f"processing newest {args.limit}. Coverage truncated.", file=sys.stderr)

    print(f"[prosody] Processing {len(rows)} clips for period '{args.period}'...",
          file=sys.stderr)

    clips = []
    skipped_no_voice = 0
    for i, row in enumerate(rows):
        if i and i % 50 == 0:
            print(f"[prosody]   {i}/{len(rows)} clips analyzed...", file=sys.stderr)
        feat = analyze_clip(row["audio"])
        if feat is None:
            skipped_no_voice += 1
        wpm, pause_ratio = compute_tempo(row)
        date = row["timestamp"].split(" ")[0] if row["timestamp"] else "unknown"
        clips.append({
            "feat": feat,
            "lang": normalize_language(row),
            "date": date,
            "wpm": wpm,
            "pause_ratio": pause_ratio,
            "speech": row["speechDuration"] or 0,
        })

    report = build_report(period_label, total, with_audio, len(rows),
                          skipped_no_voice, truncated, args.limit, clips)

    if args.format == "json":
        result = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        result = format_text(report)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
