#!/usr/bin/env python3
"""Context-aware pause/silence editing for lab recordings.

Two-phase so a human/agent can review before anything is cut:

  edit_video.py analyze VIDEO [--transcript zoom.vtt|fathom.json] [--offset auto|SECONDS]
                [--noise -35dB] [--min-pause 1.2] [--keep-pause 0.5] [--no-screen] -o edl.json
  edit_video.py report  edl.json            # markdown review table
  edit_video.py apply   VIDEO edl.json [-o out.mp4] [--max-remove 0.35]

analyze combines three signals for every silence >= --min-pause:
  audio   ffmpeg silencedetect                       -> where nobody speaks
  screen  ffmpeg scene score (4 fps): webcam / screen updates / static
  speech  transcript text just before/after          -> why it is quiet
and classifies it:
  lead      leading dead air before the meeting                -> cut to 2 s lead-in
  break     "перерыв"/"break" announced                        -> cut to keep-pause
  exercise  participants asked to try/write something          -> cut to 2 s, review
  demo      screen changes or host waits on a tool/agent       -> keep <= 12 s, else keep
                                                                  first 4 s + last 2 s, review if long
  dead_air  webcam or static view, no reason given             -> cut to keep-pause
  pause     short mid-speech gap                               -> tighten to keep-pause
  tech      screen-share fumbling (detect_lesson_start)         -> proposed, NOT approved
Every action carries approved/review flags + context lines. Edit the JSON
(flip "approved") to change decisions, then apply. Cuts land inside silence,
so no audio clicks.

Transcript alignment: Zoom VTT matches the Zoom MP4 exactly. Fathom timestamps
can be offset from the Zoom file; --offset auto estimates it by matching
transcript segment starts to audio speech onsets. Vault Fathom .md files carry
no timestamps — analysis then runs on audio+screen only (no exercise/break/tech
classes).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from detect_lesson_start import load_segments, tech_spans  # noqa: E402

# Spoken instructions to the editing/summarising agent recorded in the session
# (e.g. «Агент, это конец паузы, вырежи паузу», «агент, фактчекни это»).
# Vocative only: "агент"/"agent" opening a phrase (segment start, after punctuation
# or a discourse marker) and followed by a comma — "какой-то агент, который…" and
# "агент 24 на 7" are the lab's topic, not an instruction.
ADDRESS_RE = re.compile(r"(?:^|[.!?,:;]\s*|\b(?:так|окей|ок|вот|ну|so|okay|ok)[,\s]+)(агент|agent)\s*[,!:]", re.I)
IMPERATIVE_RE = re.compile(
    r"пожалуйста|выреж|убер|фактчек|провер|добав|запиш|сохран|отмет|сделай|помет|"
    r"please|cut|remove|fact-?check|add|note", re.I)
CUT_VERB_RE = re.compile(r"выреж|вырез|убер[иё]|cut (this|it|that)|remove (this|it)", re.I)
PAUSE_WORD_RE = re.compile(r"пауз|перерыв|break", re.I)
BREAK_RE = re.compile(r"перерыв|break\b", re.I)
EXERCISE_RE = re.compile(
    r"попробуйте|напишите|сделайте|задани|упражнени|минут\w* на|даю вам|ваша очередь|"
    r"поработайте|подумайте|try it|take a (minute|few)|your turn|write (down|in the chat)", re.I)
DEMO_RE = re.compile(
    r"запуска|смотрите|посмотрим|подожд|думает|генерир|загружа|работает|пишет|"
    r"let'?s see|watch|running|thinking|loading|generat", re.I)


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def _pairs(log, start_key, end_key, dur):
    """Pair ffmpeg *_start / *_end events in log order.

    Real recordings can start at a NEGATIVE pts (AAC priming: "silence_start: -0.0213");
    a [0-9.]+ regex silently dropped that start and shifted every pair by one, giving
    negative-length silences (GDA 01: 183/183 broken)."""
    events = re.findall(rf"({re.escape(start_key)}|{re.escape(end_key)}): ?(-?[0-9.]+)", log)
    pairs, cur = [], None
    for key, val in events:
        v = max(0.0, float(val))
        if key == start_key:
            cur = v
        elif cur is not None:
            if v > cur:
                pairs.append((cur, v))
            cur = None
    if cur is not None and dur > cur:
        pairs.append((cur, dur))  # running to EOF
    return pairs


def detect_silences(video, noise, min_pause, dur):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn", "-af",
                          f"silencedetect=noise={noise}:d={min_pause}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return _pairs(log, "silence_start", "silence_end", dur)


def detect_scene_scores(video):
    """Per-frame change magnitude (ffmpeg scene score, 4 fps, 320 px) -> [(t, score)].

    Measured on a real lab recording (GDA 01, 2026-10-10):
      talking head  median ~0.010-0.014, never still (faces always move)
      screen share  median ~0.001-0.002, still with sparse jumps up to ~0.12
      camera off    0.0000
    so "is anything moving" cannot tell a demo from a webcam; "still screen with
    discrete updates" can (see visual_state)."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-hwaccel", "videotoolbox",
                          "-i", str(video), "-an", "-vf",
                          "fps=4,scale=320:-2,select='gte(scene\\,0)',metadata=print",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    times = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", log)]
    scores = [float(x) for x in re.findall(r"lavfi\.scene_score=([0-9.]+)", log)]
    if len(times) != len(scores):
        times = [i / 4.0 for i in range(len(scores))]
    return list(zip(times, scores))


WEBCAM_MEDIAN = 0.006   # continuous small motion => a person on camera
UPDATE_SCORE = 0.03     # a discrete screen update (new text, window, image)


def visual_state(scores, a, b):
    """'webcam' | 'screen_activity' | 'static' for the span [a, b]."""
    import bisect
    import statistics
    i, j = bisect.bisect_left(scores, (a, -1.0)), bisect.bisect_right(scores, (b, 2.0))
    window = [sc for _, sc in scores[i:j]]
    if not window:
        return "static"
    if statistics.median(window) >= WEBCAM_MEDIAN:
        return "webcam"
    return "screen_activity" if any(sc >= UPDATE_SCORE for sc in window) else "static"


def overlap(a, b, spans):
    return sum(max(0.0, min(b, e) - max(a, s)) for s, e in spans)


def same_source(transcript, video):
    """True when the transcript JSON says it was made from this very video file."""
    try:
        src = json.loads(Path(transcript).read_text(encoding="utf-8")).get("source")
    except (OSError, ValueError, AttributeError):
        return False
    return bool(src) and Path(src).resolve() == Path(video).resolve()


def offset_peak_z(segments, silences, search=900, step=0.5, tol=1.5):
    """How far the best alignment score stands above the score distribution (z-score).
    GDA 01 #02: with dense pauses (~1 per 20 s) and Whisper segments that split mid-speech,
    random offsets scored 193 while the true offset 0 scored 146 — a flat, noisy landscape
    where the argmax means nothing. Real alignment shows as a sharp, isolated peak."""
    import bisect
    import statistics
    onsets = sorted(e for _, e in silences)
    starts = [t for t, _ in segments]
    if len(onsets) < 5 or len(starts) < 5:
        return 0.0

    def score(d):
        hits = 0
        for t in starts:
            x = t + d
            i = bisect.bisect_left(onsets, x - tol)
            hits += i < len(onsets) and onsets[i] <= x + tol
        return hits

    vals = [score(k * step - search) for k in range(int(2 * search / step) + 1)]
    sd = statistics.pstdev(vals) or 1.0
    return (max(vals) - statistics.median(vals)) / sd


def estimate_offset(segments, silences, search=900, step=0.5, tol=1.5):
    """Shift transcript times so segment starts line up with speech onsets."""
    onsets = sorted(e for _, e in silences)
    starts = [t for t, _ in segments]
    if not onsets or not starts:
        return 0.0, 0.0
    import bisect

    def score(d):
        hits = 0
        for t in starts:
            x = t + d
            i = bisect.bisect_left(onsets, x - tol)
            hits += i < len(onsets) and onsets[i] <= x + tol
        return hits

    # The hit-count is flat over a ±tol plateau; picking its edge is off by ~tol.
    # Refine inside the plateau by the median distance to the nearest onset.
    grid = [k * step - search for k in range(int(2 * search / step) + 1)]
    scores = {d: score(d) for d in grid}
    top = max(scores.values())

    def residual(d):
        res = []
        for t in starts:
            x = t + d
            i = bisect.bisect_left(onsets, x)
            res.append(min(abs(x - onsets[j]) for j in (i - 1, i) if 0 <= j < len(onsets)))
        return sorted(res)[len(res) // 2]

    best = min((d for d in grid if scores[d] == top), key=lambda d: (residual(d), abs(d)))
    # Confidence = share of speech onsets (silence ends) that have a cue nearby.
    # (Share of cues near an onset is ~10% for continuous speech even when aligned:
    # most sentences don't follow a >=1.2 s pause — GDA 01 reported 9% at offset 0.)
    shifted = sorted(t + best for t in starts)
    near = sum(1 for o in onsets
               if (k := bisect.bisect_left(shifted, o - tol)) < len(shifted) and shifted[k] <= o + tol)
    return best, near / len(onsets)


def directives(segments, silences, lookback=420):
    """Find spoken instructions addressed to the agent.

    Returns (cut_actions, agent_notes). A cut directive that mentions a pause/break
    proposes removing from the start of the longest silence in the preceding
    `lookback` s through the end of the directive sentence. Always review-only:
    the boundary of "the next few meta words" is a judgement call. Non-cut
    directives (fact-check this, add this to the summary) become notes for the
    summary step.
    """
    cuts, notes = [], []
    for i, (t, txt) in enumerate(segments):
        m = ADDRESS_RE.search(txt)
        if not m:
            continue
        # directives often span segments: «агент, это конец паузы.» | «Пожалуйста, вырежи паузу.»
        joined = " ".join(x for _, x in segments[i:i + 3])
        window = joined[m.start(1):m.start(1) + 200]
        if not IMPERATIVE_RE.search(window):
            continue
        last = i + 1
        while last < min(i + 3, len(segments)) and not CUT_VERB_RE.search(segments[last - 1][1]):
            last += 1
        nxt = segments[last][0] if last < len(segments) else t + 8
        if CUT_VERB_RE.search(window):
            start, why = t, "spoken cut directive"
            if PAUSE_WORD_RE.search(window):
                # a break is rarely pure silence (room noise, someone unmutes) — audio
                # splits it up, but the transcript shows it as one long gap
                prior = [(e - s0, s0) for s0, e in silences if t - lookback <= s0 < t]
                prior += [(nt - pt - 5, pt + 5) for (pt, _), (nt, _) in zip(segments, segments[1:])
                          if t - lookback <= pt < t and nt - pt > 60]
                if prior:
                    start = max(prior)[1]
                    why = "spoken directive: cut the break before it (and the directive itself)"
                    # a gap start is a guess (last cue + 5 s); a silence inside the gap is exact
                    inside = [s0 for s0, _ in silences if start - 10 <= s0 <= start + 30]
                    if inside:
                        start = min(inside)
            cuts.append({"start": round(start, 2), "end": round(nxt, 2), "class": "directive",
                         "remove": [round(start, 2), round(nxt, 2)], "approved": False, "review": True,
                         "reason": why, "before": window, "after": ""})
        else:
            notes.append({"at": round(t, 2), "text": window})
    return cuts, notes


def context(segments, a, b):
    return " ".join(txt for t, txt in segments if a <= t <= b)[:300]


def classify(s, e, visual, before, after, is_first, keep_pause):
    """Return (class, remove_start, remove_end, approved, review, reason).
    visual: 'webcam' | 'screen_activity' | 'static' (see visual_state)."""
    L = e - s
    half = keep_pause / 2
    waiting = bool(DEMO_RE.search(before)) and L > 3
    if is_first and s < 2.0 and L > 10:
        return "lead", s, e - 2.0, True, False, f"{L:.0f}s dead air before first speech"
    if BREAK_RE.search(before) and L > 30:
        return "break", s + half, e - half, True, True, "break announced"
    if EXERCISE_RE.search(before) and L > 8:
        return "exercise", s + 1.0, e - 1.0, True, True, "participants working — viewers wait"
    if visual == "screen_activity" or (visual == "static" and waiting):
        why = "screen updates during silence" if visual == "screen_activity" else "waiting on a tool"
        if L <= 12:
            return "demo", s, s, False, False, f"{why} — kept"
        return "demo", s + 4.0, e - 2.0, True, L > 60, f"long demo wait ({why}) — keep head+tail"
    if L >= 4:
        return "dead_air", s + half, e - half, True, False, f"no speech, {visual} view"
    return "pause", s + half, e - half, True, False, "mid-speech pause"


def analyze(a):
    dur = probe_duration(a.video)
    print(f"analyze: {a.video} ({dur / 60:.1f} min)", file=sys.stderr)
    silences = detect_silences(a.video, a.noise, a.min_pause, dur)
    print(f"  {len(silences)} silences >= {a.min_pause}s", file=sys.stderr)
    scores = []
    if not a.no_screen:
        # frame scoring is the slow part (~5 min / 2.5 h) — cache it for review re-runs
        st_ = Path(a.video).stat()
        cache = Path(a.out).with_suffix(".scores.json")
        key = f"{Path(a.video).resolve()}|{st_.st_size}|{int(st_.st_mtime)}"
        if cache.exists() and json.loads(cache.read_text()).get("key") == key:
            scores = [tuple(x) for x in json.loads(cache.read_text())["scores"]]
        else:
            scores = detect_scene_scores(a.video)
            cache.write_text(json.dumps({"key": key, "scores": scores}))
    if not a.no_screen:
        print(f"  {len(scores)} frames scored for visual state", file=sys.stderr)

    segments, offset, conf, drift_warning = [], 0.0, None, None
    if a.transcript:
        segments = load_segments(Path(a.transcript))
        if not segments:
            print("  ! transcript has no timestamps — audio+screen only", file=sys.stderr)
        elif a.offset == "auto" and same_source(a.transcript, a.video):
            offset, conf = 0.0, 1.0
            print("  transcript made from this video (transcribe_cut.py) — offset 0", file=sys.stderr)
        elif a.offset == "auto":
            offset, conf = estimate_offset(segments, silences)
            peak = offset_peak_z(segments, silences)
            if peak < 4.0:
                print(f"  ! no clear alignment peak (z={peak:.1f}; best guess {offset:+.1f}s) — using 0. "
                      "Context classes may be shifted; prefer a transcript from this video "
                      "(transcribe_cut.py) or pass --offset", file=sys.stderr)
                offset, conf = 0.0, 0.0
            else:
                print(f"  transcript offset {offset:+.1f}s (match {conf:.0%}, peak z={peak:.1f})", file=sys.stderr)
        else:
            offset = float(a.offset)
        # Audio-onset matching can't detect clock drift on real speech (GDA 01: false
        # drift on a same-recording transcript, missed Wispr's real +59 s step). Guard on
        # what the transcript declares instead; check cross-tool drift by TEXT with
        # compare_transcripts.py.
        head = Path(a.transcript).read_text(encoding="utf-8", errors="replace")[:300]
        if "recording_active_ms" in head:
            drift_warning = "transcript clock = recording_active_ms (Wispr Flow): pauses are skipped"
            print(f"  ! {drift_warning} — not the video clock; offsets jump after any pause. "
                  "Use the transcript from the SAME recording as the video, or check with "
                  "compare_transcripts.py", file=sys.stderr)
        else:
            drift_warning = None
        segments = [(t + offset, txt) for t, txt in segments]

    actions = []
    for i, (s, e) in enumerate(silences):
        L = e - s
        visual = visual_state(scores, s, e) if scores else "static"
        # only what was said right before explains a silence; wider windows leak
        # earlier topics (a demo announced 20 s ago is not why the screen froze now)
        before, after = context(segments, s - 8, s + 0.5), context(segments, e - 0.5, e + 10)
        cls, rs, re_, ok, review, why = classify(s, e, visual, before, after, i == 0, a.keep_pause)
        if re_ - rs < 0.3:
            ok = False
        actions.append({"start": round(s, 2), "end": round(e, 2), "class": cls,
                        "remove": [round(rs, 2), round(max(rs, re_), 2)],
                        "approved": ok, "review": review, "visual": visual,
                        "reason": why, "before": before[-160:], "after": after[:120]})

    if segments:
        for sp in tech_spans(segments, dur):
            actions.append({"start": sp["start"], "end": sp["end"], "class": "tech",
                            "remove": [sp["start"], sp["end"]], "approved": False, "review": True,
                            "reason": "screen-share fumbling — read context, approve only real Q&A about visibility",
                            "before": " | ".join(sp.get("context", []))[:300] if isinstance(sp.get("context"), list)
                            else str(sp.get("context", ""))[:300], "after": ""})

    agent_notes = []
    if segments:
        dcuts, agent_notes = directives(segments, silences)
        actions += dcuts
        for n in agent_notes:
            print(f"  note for summary @ {_mmss(n['at'])}: {n['text'][:90]}", file=sys.stderr)

    edl = {"source": str(Path(a.video).resolve()), "duration": round(dur, 2), "agent_notes": agent_notes,
           "transcript": a.transcript, "offset": offset, "offset_confidence": conf, "offset_drift": drift_warning,
           "params": {"noise": a.noise, "min_pause": a.min_pause, "keep_pause": a.keep_pause},
           "actions": sorted(actions, key=lambda x: x["start"])}
    Path(a.out).write_text(json.dumps(edl, ensure_ascii=False, indent=1), encoding="utf-8")
    print(report(edl))
    print(f"\nEDL: {a.out}", file=sys.stderr)


def _mmss(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def report(edl):
    dur, acts = edl["duration"], edl["actions"]
    by = {}
    for x in acts:
        if x["approved"]:
            r = by.setdefault(x["class"], [0, 0.0])
            r[0] += 1
            r[1] += x["remove"][1] - x["remove"][0]
    # headline = UNION of approved spans (apply merges overlaps; per-class rows may overlap)
    spans = sorted(x["remove"] for x in acts if x["approved"] and x["remove"][1] > x["remove"][0])
    total, cur = 0.0, None
    for s0, e0 in spans:
        if cur and s0 <= cur[1]:
            cur[1] = max(cur[1], e0)
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = [s0, e0]
    if cur:
        total += cur[1] - cur[0]
    lines = [f"## Edit plan — removes {total / 60:.1f} min of {dur / 60:.1f} ({total / dur:.0%})", "",
             "| class | cuts | removed |", "|---|---|---|"]
    lines += [f"| {k} | {v[0]} | {v[1]:.0f}s |" for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])]
    rev = [x for x in acts if x["review"]]
    if rev:
        lines += ["", "### Needs review (edit `approved` in the EDL)", "",
                  "| at | len | class | approved | reason | said before |", "|---|---|---|---|---|---|"]
        for x in rev:
            said = x["before"].replace("|", "/")[-90:]
            lines.append(f"| {_mmss(x['start'])} | {x['end'] - x['start']:.0f}s | {x['class']} | "
                         f"{x['approved']} | {x['reason']} | {said} |")
    return "\n".join(lines)


def apply(a):
    edl = json.loads(Path(a.edl).read_text(encoding="utf-8"))
    spans = [{"start": x["remove"][0], "end": x["remove"][1]}
             for x in edl["actions"] if x["approved"] and x["remove"][1] - x["remove"][0] >= 0.3]
    tmp = Path(a.edl).with_suffix(".spans.json")
    tmp.write_text(json.dumps(spans))
    out = a.out or str(Path(a.video).with_suffix("")) + ".edited.mp4"
    rc = subprocess.run([sys.executable, str(Path(__file__).with_name("cut_spans.py")), a.video,
                         "--spans-json", str(tmp), "--max-remove", str(a.max_remove), "-o", out]).returncode
    if rc:
        sys.exit(rc)
    print(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    an = sub.add_parser("analyze")
    an.add_argument("video"); an.add_argument("--transcript"); an.add_argument("--offset", default="auto")
    an.add_argument("--noise", default="-35dB"); an.add_argument("--min-pause", type=float, default=1.2)
    an.add_argument("--keep-pause", type=float, default=0.5); an.add_argument("--no-screen", action="store_true")
    an.add_argument("-o", "--out", required=True)
    rp = sub.add_parser("report"); rp.add_argument("edl")
    ap = sub.add_parser("apply")
    ap.add_argument("video"); ap.add_argument("edl"); ap.add_argument("-o", "--out")
    ap.add_argument("--max-remove", type=float, default=0.35)
    a = p.parse_args()
    if a.cmd == "analyze":
        analyze(a)
    elif a.cmd == "report":
        print(report(json.loads(Path(a.edl).read_text(encoding="utf-8"))))
    else:
        apply(a)


if __name__ == "__main__":
    main()
