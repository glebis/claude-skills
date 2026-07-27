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

    if as_json:
        print(json.dumps({
            "lesson_start_s": start_s,
            "lesson_phrase": start_pat,
            "presentation_open_s": pres_s,
            "presentation_phrase": pres_pat,
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


if __name__ == "__main__":
    main()
