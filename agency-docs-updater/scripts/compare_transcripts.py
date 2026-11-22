#!/usr/bin/env python3
"""Compare two timestamped transcripts of the same meeting (e.g. Fathom vs Wispr Flow).

  compare_transcripts.py A B [--names fathom,wispr] [--samples 4] [--terms "Claude Code,Codex,…"]

Accepts anything detect_lesson_start.load_segments reads (Fathom JSON, Zoom VTT,
Wispr live/refined .ndjson, publication .md). Reports:
  - alignment: B's offset vs A found by TEXT matching (median), and jitter (IQR)
    — jitter is what matters for cutting; offset is just a constant
  - granularity: segment count, median words/segment, median gap
  - coverage: first/last timestamp, words total
  - tech terms: Latin spelling hits vs Cyrillic transliterations
  - fillers: э-э / м-м / ну вот rates
  - side-by-side windows for a human read of accuracy
"""
import argparse
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from detect_lesson_start import load_segments  # noqa: E402

DEFAULT_TERMS = {
    # canonical Latin spelling: transliteration patterns that should NOT appear
    "Claude": r"клод\w*",
    "Codex": r"кодекс\w*",
    "ChatGPT": r"чат ?джи ?пи ?ти|чатгпт",
    "Cowork": r"ко-?ворк\w*",
    "Wispr": r"виспер\w*|виспр\w*",
    "Obsidian": r"обсидиан\w*",
    "MCP": r"эм ?си ?пи",
    "Gemini": r"джемини",
    "Telegram": r"телеграм\w*",
}
FILLERS = r"\bэ-?э+\b|\bм-?м+\b|\bэм+\b|\bну вот\b|\bкак бы\b"
WORD = re.compile(r"[\w'-]+", re.U)


def words(t):
    return [w.lower() for w in WORD.findall(t)]


def shingles(t, n=3):
    w = words(t)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def align(a, b, window=900, min_hits=2):
    """For each B segment, best A segment by shared word trigrams within ±window."""
    a_sh = [(t, shingles(x)) for t, x in a]
    pairs = []
    for tb, xb in b:
        sb = shingles(xb)
        if len(sb) < 3:
            continue
        best = max(((len(sb & sa), ta) for ta, sa in a_sh if abs(ta - tb) <= window),
                   default=(0, None))
        if best[0] >= min_hits:
            pairs.append((tb, best[1]))
    return pairs


def clock_steps(pairs, bucket=600, min_n=5, jump=10.0):
    """Text-aligned offset per `bucket` seconds; returns (buckets, steps).
    A step = consecutive bucket medians differing by > `jump` s — the other tool's clock
    skipped or added time (Wispr Flow counts only active-recording ms)."""
    by = {}
    for tb, ta in pairs:
        by.setdefault(int(tb // bucket), []).append(ta - tb)
    buckets = [(k * bucket, st.median(v), len(v)) for k, v in sorted(by.items()) if len(v) >= min_n]
    # A step must PERSIST: buckets i and i+1 both leave the previous level (median of
    # up to 3 prior buckets) and agree with each other. A single deviating bucket that
    # returns (GDA 01: 5 pairs during the break, -31 s) is noise, not a clock step.
    steps, med = [], [m for _, m, _ in buckets]
    for i in range(1, len(buckets) - 1):
        if steps and buckets[i][0] - steps[-1][0] <= bucket:
            continue  # the bucket right after a step still "sees" the old level
        before = st.median(med[max(0, i - 3):i])
        if (abs(med[i] - before) > jump and abs(med[i + 1] - before) > jump
                and abs(med[i + 1] - med[i]) <= jump):
            steps.append((buckets[i][0], st.median(med[i:i + 2]) - before))
    return buckets, steps


def stats(segs):
    wc = [len(words(x)) for _, x in segs]
    gaps = [b[0] - a[0] for a, b in zip(segs, segs[1:])]
    text = " ".join(x for _, x in segs)
    return {
        "segments": len(segs), "words": sum(wc),
        "median words/seg": st.median(wc) if wc else 0,
        "median gap s": round(st.median(gaps), 1) if gaps else 0,
        "span": f"{segs[0][0] / 60:.1f}–{segs[-1][0] / 60:.1f} min" if segs else "-",
        "fillers /1k words": round(1000 * len(re.findall(FILLERS, text.lower())) / max(1, sum(wc)), 1),
        "_text": text,
    }


def term_table(texts, terms):
    rows = []
    for canon, translit in terms.items():
        cells = []
        for t in texts:
            latin = len(re.findall(rf"\b{re.escape(canon)}", t, re.I))
            cyr = len(re.findall(translit, t, re.I))
            cells.append(f"{latin} / {cyr}")
        rows.append((canon, cells))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--names", default="A,B"); p.add_argument("--samples", type=int, default=4)
    p.add_argument("--sample-seconds", type=int, default=45)
    a_args = p.parse_args()
    na, nb = a_args.names.split(",")
    A, B = load_segments(Path(a_args.a)), load_segments(Path(a_args.b))
    sa, sb = stats(A), stats(B)

    pairs = align(A, B)
    offs = [ta - tb for tb, ta in pairs]
    off = st.median(offs) if offs else 0.0
    q = st.quantiles(offs, n=4) if len(offs) >= 4 else [0, 0, 0]
    print(f"## {na} vs {nb}\n")
    print(f"Alignment: {len(pairs)}/{len(B)} {nb} segments matched by text; "
          f"{nb} + {off:+.1f}s = {na} time; jitter IQR {q[2] - q[0]:.1f}s\n")
    _, steps = clock_steps(pairs)
    if steps:
        print("**Clock steps** (the B timeline is not continuous; don't cut video with it): "
              + ", ".join(f"at {nb} {t / 60:.0f} min {d:+.0f}s" for t, d in steps) + "\n")
    print(f"| metric | {na} | {nb} |\n|---|---|---|")
    for k in sa:
        if not k.startswith("_"):
            print(f"| {k} | {sa[k]} | {sb[k]} |")
    print(f"\n### Tech terms (Latin / Cyrillic transliteration)\n\n| term | {na} | {nb} |\n|---|---|---|")
    for canon, cells in term_table([sa["_text"], sb["_text"]], DEFAULT_TERMS):
        if any(c != "0 / 0" for c in cells):
            print(f"| {canon} | {cells[0]} | {cells[1]} |")

    print(f"\n### Side by side ({a_args.sample_seconds}s windows, {na} timeline)\n")
    dur = A[-1][0]
    for i in range(a_args.samples):
        t0 = dur * (i + 1) / (a_args.samples + 1)
        t1 = t0 + a_args.sample_seconds
        ta = " ".join(x for t, x in A if t0 <= t < t1)
        tb = " ".join(x for t, x in B if t0 <= t + off < t1)
        print(f"**{int(t0 // 60)}:{int(t0 % 60):02d}**\n- {na}: {ta[:600]}\n- {nb}: {tb[:600]}\n")


if __name__ == "__main__":
    main()
