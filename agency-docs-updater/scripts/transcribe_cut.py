#!/usr/bin/env python3
"""Transcribe the EDITED video (Groq Whisper) so chapters and transcript timecodes
match what is published. Never remap source-transcript timestamps through cuts.

  GROQ_API_KEY=... transcribe_cut.py VIDEO -o out.json [--slug goal-driven-ai] [--lang ru]

Audio -> 16 kHz mono 24 kbps chunks (20 min, Groq file-size limits), whisper-large-v3
verbose_json, segments re-based onto the full timeline. The lab's `asr_glossary`
(labs.json) is passed as the Whisper prompt — proper nouns are where both Fathom and
Wispr Flow failed on GDA 01 (Allama, Py, плод-код, JLM…).
Output: {"transcript": [{"timestamp": seconds, "end": seconds, "text": ...}]} —
readable by detect_lesson_start.load_segments.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import lab_layout  # noqa: E402

CHUNK = 1200

# Whisper hallucinations learned from Russian subtitle credits / YouTube outros.
# Seen on GDA 01 (Fathom and Groq alike): «Субтитры сделал DimaTorzok», bare «DimaTorzok»,
# «Продолжение следует...». Narrow on purpose: «накладывать текст субтитров» is real speech.
import re  # noqa: E402
HALLUCINATION_RE = re.compile(
    r"^\W*(DimaTorzok|Субтитры (сделал|создавал|делал|подготовил)\w*\b.*|"
    r"Продолжение следует\W*|Спасибо за просмотр\W*|Редактор субтитров.*|Корректор .*|"
    r"Thanks for watching\W*|Thank you for watching\W*|Subtitles by .*|"
    r"The following is (a|the) (video|recording).*)\W*$", re.I)
# Fillers Whisper invents in SILENCE (GDA 01 #02: 8 min of "Thank you." before the
# meeting). Real speech can say them too, so drop only when Whisper itself doubts speech.
SILENCE_FILLER_RE = re.compile(r"^\W*(thank you|thanks|you|bye|спасибо)\W*$", re.I)


def is_hallucination(text, no_speech_prob=None):
    t = text.strip()
    if HALLUCINATION_RE.match(t):
        return True
    return bool(SILENCE_FILLER_RE.match(t)) and (no_speech_prob or 0) >= 0.3


def first_speech(video, noise="-35dB", min_silence=5.0):
    """Seconds of leading silence to skip (minus 1 s). A chunk that opens with minutes of
    silence makes Whisper's language detection guess wrong: GDA 01 #02 came back
    TRANSLATED into English for 8:25-10:09 of Russian speech."""
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-t", "1800", "-i", str(video), "-vn",
                          "-af", f"silencedetect=noise={noise}:d={min_silence}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = re.findall(r"silence_start: (-?[0-9.]+)", log)
    ends = re.findall(r"silence_end: ([0-9.]+)", log)
    if starts and ends and float(starts[0]) <= 1.0:
        return max(0.0, float(ends[0]) - 1.0)
    return 0.0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--slug", default=os.environ.get("LAB_SLUG", "claude-code"))
    p.add_argument("--lang", default=None, help="omit = auto-detect")
    p.add_argument("--model", default="whisper-large-v3")
    a = p.parse_args()
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        sys.exit("GROQ_API_KEY not set")
    glossary = lab_layout.load_registry().get(a.slug, {}).get("asr_glossary", [])
    prompt = ("Встреча лаборатории. Термины: " + ", ".join(glossary) + ".") if glossary else None
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "csv=p=0", a.video], capture_output=True, text=True, check=True).stdout)
    segs = []
    with tempfile.TemporaryDirectory() as tmp:
        start = first_speech(a.video)
        if start:
            print(f"  skipping {start:.0f}s of leading silence", file=sys.stderr)
        while start < dur:
            chunk = Path(tmp) / f"c{int(start)}.ogg"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(start), "-t",
                            str(CHUNK), "-i", a.video, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libopus",
                            "-b:a", "24k", str(chunk)], check=True)
            data = {"model": a.model, "response_format": "verbose_json", "temperature": "0"}
            if prompt:
                data["prompt"] = prompt
            if a.lang:
                data["language"] = a.lang
            for attempt in range(3):
                r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions",
                                  headers={"Authorization": f"Bearer {key}"}, data=data,
                                  files={"file": (chunk.name, chunk.open("rb"), "audio/ogg")}, timeout=600)
                if r.status_code == 200:
                    break
                print(f"  chunk {start / 60:.0f}m: HTTP {r.status_code} {r.text[:120]}", file=sys.stderr)
            r.raise_for_status()
            for s in r.json().get("segments", []):
                if is_hallucination(s["text"], s.get("no_speech_prob")):
                    print(f"  dropped hallucination @ {start + s['start']:.0f}s: {s['text'].strip()[:50]}", file=sys.stderr)
                    continue
                segs.append({"timestamp": round(start + s["start"], 2), "end": round(start + s["end"], 2),
                             "text": s["text"].strip(), "no_speech_prob": s.get("no_speech_prob")})
            print(f"  {start / 60:.0f}-{min(dur, start + CHUNK) / 60:.0f} min: {len(segs)} segments", file=sys.stderr)
            start += CHUNK
    Path(a.out).write_text(json.dumps({"transcript": segs, "source": str(Path(a.video).resolve()),
                                       "model": a.model, "prompt": prompt}, ensure_ascii=False, indent=1))
    print(a.out)


if __name__ == "__main__":
    main()
