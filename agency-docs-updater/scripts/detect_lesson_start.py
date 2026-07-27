#!/usr/bin/env python3
"""Detect the actual lesson start and presentation-opening moments from a timestamped transcript.

Sources supported (auto-detected):
  - Fathom JSON: {"transcript": [{"speaker": {...}, "text": ..., "timestamp": "HH:MM:SS"}, ...]}
    (also accepts a bare list of such segments)
  - Publication markdown with `**[HH:MM:SS] Имя Ф.:**` blocks
  - Zoom VTT (WEBVTT with HH:MM:SS.mmm --> ... cues)

Usage:
  detect_lesson_start.py TRANSCRIPT [--window-min 20] [--json]

Prints the detected moments; with --json emits machine-readable output:
  {"lesson_start_s": float|null, "presentation_open_s": float|null,
   "lesson_phrase": str|null, "presentation_phrase": str|null}

Intended pipeline use (SKILL Step 3-pre): trim the video to
max(silence_end, lesson_start - LEAD_IN) and add the presentation moment
as a YouTube chapter.
"""
import json
import re
import sys
from pathlib import Path

# Phrases the host uses to open the lesson (RU + EN). Order = priority.
# Greetings count: before the greeting there is only dead air.
LESSON_START_PATTERNS = [
    r"добро пожаловать",
    r"всем привет",
    r"привет,? всем",
    r"давайте начина\w*",
    r"будем начинать",
    r"начн[её]м",
    r"начинаем",
    r"пора начинать",
    r"поехали",
    r"стартуем",
    r"welcome,? everyone",
    r"h(i|ello),? everyone",
    r"let'?s (start|begin|get started|kick off)",
    r"shall we (start|begin)",
]

# Phrases around opening/sharing the presentation / screen.
PRESENTATION_PATTERNS = [
    r"открою презентаци\w*",
    r"покажу презентаци\w*",
    r"презентаци\w* (сегодня|наш\w*|открыва\w*)",
    r"поделюсь экраном",
    r"расшарю экран",
    r"шерю экран",
    r"видно (мой )?экран",
    r"экран видно",
    r"share (my )?screen",
    r"screen ?shar\w*",
    r"see my screen",
    r"pull up the (slides|deck|presentation)",
    r"открыва\w* слайд\w*",
    r"перв\w* слайд",
]


def ts_to_seconds(ts: str) -> float:
    parts = [float(p) for p in ts.replace(",", ".").split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def load_segments(path: Path):
    """Return list of (seconds, text)."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Fathom JSON
    if path.suffix == ".json" or raw.lstrip().startswith(("{", "[")):
        data = json.loads(raw)
        segs = data.get("transcript", data) if isinstance(data, dict) else data
        out = []
        for s in segs:
            ts = s.get("timestamp")
            if ts is None:
                continue
            sec = ts_to_seconds(ts) if isinstance(ts, str) else float(ts)
            out.append((sec, s.get("text", "")))
        return out
    # VTT
    if "WEBVTT" in raw[:200]:
        out, cur = [], None
        for line in raw.splitlines():
            m = re.match(r"(\d{1,2}:\d{2}:\d{2}[.,]\d+)\s+-->", line)
            if m:
                cur = ts_to_seconds(m.group(1))
            elif cur is not None and line.strip() and "-->" not in line:
                out.append((cur, line.strip()))
        return out
    # Publication markdown with [HH:MM:SS]
    out = []
    for m in re.finditer(r"\*\*\[(\d{1,2}:\d{2}:\d{2})\][^:]*:\*\*\s*(.+)", raw):
        out.append((ts_to_seconds(m.group(1)), m.group(2)))
    return out


# Technical-difficulty markers around screen sharing.
# Strong: alone they open a tech-check span.
TECH_STRONG_PATTERNS = [
    r"видно (мою |нашу |мой )?(презентаци|экран)",
    r"(презентаци\w*|экран) (видно|видите)",
    r"не видно",
    r"меня слышно",
    r"слышно меня",
    r"перешарю",
    r"ещ[её] раз (по)?шерю",
    r"can you (see|hear)",
    r"is (my|the) screen (visible|showing)",
    r"do you see (my|the)",
]
# Weak: count only within NEAR_S of a strong match or of presentation_open.
TECH_WEAK_PATTERNS = [
    r"одну секундочку",
    r"секундочку",
    r"один момент",
    r"подождите",
    r"сейчас[,.]? сейчас",
    r"one sec\w*",
    r"hold on",
]
NEAR_S = 45          # weak marker attaches to a strong anchor within this distance
SPAN_PRE_S = 5       # span padding before first marker
SPAN_POST_S = 20     # span padding after last marker
SPAN_MERGE_S = 60    # merge spans closer than this


def tech_spans(segments, window_s, anchor_ts=None):
    """Return list of {start,end,context} candidate spans of technical fumbling."""
    strong, weak = [], []
    screen_word = re.compile(r"презентаци|экран|слайд|screen|slide")
    for sec, text in segments:
        if sec > window_s:
            break
        low = text.lower()
        if any(re.search(p, low) for p in TECH_STRONG_PATTERNS):
            strong.append((sec, text[:100]))
        elif any(re.search(p, low) for p in TECH_WEAK_PATTERNS):
            # a weak marker in the same breath as a screen/slides word is strong
            if screen_word.search(low):
                strong.append((sec, text[:100]))
            else:
                weak.append((sec, text[:100]))
    anchors = [s for s, _ in strong]
    if anchor_ts is not None:
        anchors.append(anchor_ts)
    hits = strong + [(s, t) for s, t in weak
                     if any(abs(s - a) <= NEAR_S for a in anchors)]
    hits.sort()
    spans = []
    for sec, ctx in hits:
        if spans and sec - spans[-1]["end"] <= SPAN_MERGE_S:
            spans[-1]["end"] = sec + SPAN_POST_S
            spans[-1]["context"].append(ctx)
        else:
            spans.append({"start": max(0.0, sec - SPAN_PRE_S),
                          "end": sec + SPAN_POST_S,
                          "context": [ctx]})
    return spans


def first_match(segments, patterns, window_s):
    for sec, text in segments:
        if sec > window_s:
            break
        low = text.lower()
        for pat in patterns:
            m = re.search(pat, low)
            if m:
                return sec, m.group(0), text[:120]
    return None, None, None


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    window_min = 20.0
    if "--window-min" in args:
        i = args.index("--window-min")
        window_min = float(args[i + 1])
        del args[i:i + 2]
    if not args:
        print(__doc__)
        sys.exit(2)

    segments = sorted(load_segments(Path(args[0])), key=lambda x: x[0])
    if not segments:
        print("ERROR: no timestamped segments found in transcript", file=sys.stderr)
        sys.exit(1)

    window_s = window_min * 60
    start_s, start_pat, start_ctx = first_match(segments, LESSON_START_PATTERNS, window_s)
    # presentation is searched in a wider window (it can come after intro talk)
    pres_s, pres_pat, pres_ctx = first_match(segments, PRESENTATION_PATTERNS, window_s * 2)

    spans = tech_spans(segments, window_s * 2, anchor_ts=pres_s)

    if as_json:
        print(json.dumps({
            "lesson_start_s": start_s,
            "lesson_phrase": start_pat,
            "presentation_open_s": pres_s,
            "presentation_phrase": pres_pat,
            "tech_check_spans": spans,
        }, ensure_ascii=False))
        return

    def fmt(s):
        if s is None:
            return "—"
        return f"{int(s // 3600):02d}:{int(s % 3600 // 60):02d}:{int(s % 60):02d}"

    print(f"lesson start:       {fmt(start_s)}  ({start_pat or 'not found'})")
    if start_ctx:
        print(f"  context: {start_ctx}")
    print(f"presentation open:  {fmt(pres_s)}  ({pres_pat or 'not found'})")
    if pres_ctx:
        print(f"  context: {pres_ctx}")
    if spans:
        print(f"tech-check spans ({len(spans)}) — candidates, review before cutting:")
        for sp in spans:
            print(f"  {fmt(sp['start'])}–{fmt(sp['end'])}  {sp['context'][0]}")
    else:
        print("tech-check spans:   none")


if __name__ == "__main__":
    main()
