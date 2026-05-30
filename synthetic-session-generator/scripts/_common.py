#!/usr/bin/env python3
"""Shared helpers for the synthetic-session-generator scripts.

Centralizes the mandatory watermark, config loading/validation, turn allocation, timestamp
emulation, and YAML-safe frontmatter so the four CLI scripts stay consistent.
"""
import argparse
import json
import os
import sys

# --- Single source of truth for the mandatory watermark (exact-match downstream checks rely on it).
WATERMARK = ("⚠️ SYNTHETIC — AI-generated fictional session. "
             "Not a real person, not clinical advice.")

LANGUAGES = {
    "en": "English", "ru": "Russian", "de": "German", "es": "Spanish",
    "fr": "French", "pt": "Portuguese", "it": "Italian", "nl": "Dutch",
}
MODALITIES = ["icf-grow", "cbt", "ifs", "act-mi"]
DEFAULTS = {"language": "en", "modality": "cbt", "duration_minutes": 50}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")


# --- argparse validators -----------------------------------------------------
def positive_int(value):
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {ivalue}")
    return ivalue


# --- config ------------------------------------------------------------------
def load_config():
    """Return validated defaults merged with config.json. Invalid values fall back to DEFAULTS."""
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):  # ValueError covers JSON decode, bad UTF-8, oversized ints
            return cfg
        if isinstance(raw, dict):
            # isinstance(str) guards both type and hashability (a list value would raise TypeError).
            if isinstance(raw.get("language"), str) and raw["language"] in LANGUAGES:
                cfg["language"] = raw["language"]
            if isinstance(raw.get("modality"), str) and raw["modality"] in MODALITIES:
                cfg["modality"] = raw["modality"]
            dur = raw.get("duration_minutes")
            # bool is an int subclass — exclude it so `true` is not accepted as a duration.
            if isinstance(dur, int) and not isinstance(dur, bool) and dur > 0:
                cfg["duration_minutes"] = dur
    return cfg


def run_cli(main):
    """Run a CLI main(), swallowing BrokenPipeError when a downstream consumer closes the pipe."""
    try:
        main()
        # Flush inside the guard: buffered stdout to a closed pipe otherwise raises at shutdown (exit 120).
        sys.stdout.flush()
    except BrokenPipeError:
        # Redirect stdout to devnull so the interpreter's shutdown flush doesn't re-raise.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)


def write_text(path, text):
    """Write text, exiting cleanly (code 2) on any filesystem error instead of a traceback."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as e:
        print(f"ERROR: could not write {path} ({e})", file=sys.stderr)
        sys.exit(2)


def save_config(cfg):
    write_text(CONFIG_PATH, json.dumps(cfg, ensure_ascii=False, indent=2))


def duration_to_length(mins):
    """Map clock minutes to a turn budget (~0.6 turns/min, clamped 8–80) and a length bucket."""
    # Clamp the input first so absurdly large ints can't overflow float conversion in `mins * 0.6`.
    mins = max(1, min(int(mins), 100_000))
    turns = max(8, min(80, round(mins * 0.6)))
    bucket = "short" if turns <= 20 else "standard" if turns <= 38 else "long"
    return turns, bucket


def allocate_turns(weights, budget):
    """Distribute `budget` turns across phases by `weights`, summing exactly to budget.

    Uses the largest-remainder method; guarantees at least 1 per phase when budget >= len(weights).
    """
    n = len(weights)
    total = sum(weights) or n
    raw = [budget * w / total for w in weights]
    floor = [int(x) for x in raw]
    remainder = budget - sum(floor)
    order = sorted(range(n), key=lambda i: raw[i] - floor[i], reverse=True)
    for k in range(max(0, remainder)):
        floor[order[k % n]] += 1
    # Ensure no phase is 0 when we can afford it, by borrowing from the largest.
    if budget >= n:
        for i in range(n):
            if floor[i] == 0:
                donor = max(range(n), key=lambda j: floor[j])
                if floor[donor] > 1:
                    floor[donor] -= 1
                    floor[i] += 1
    return floor


# --- session JSON validation -------------------------------------------------
class SessionError(ValueError):
    pass


def validate_session(data):
    """Validate and normalize a session dict in place. Returns the spec and turns."""
    if not isinstance(data, dict):
        raise SessionError("session JSON root must be an object")
    spec = data.get("spec")
    if spec is None:
        spec = {}
    if not isinstance(spec, dict):
        raise SessionError("'spec' must be an object")
    turns = data.get("turns")
    if turns is None:
        turns = []
    if not isinstance(turns, list):
        raise SessionError("'turns' must be a list")
    norm = []
    for i, t in enumerate(turns):
        if not isinstance(t, dict):
            raise SessionError(f"turn {i} must be an object")
        t["speaker"] = "" if t.get("speaker") is None else str(t.get("speaker"))
        t["text"] = "" if t.get("text") is None else str(t.get("text"))
        if t.get("timestamp") is not None:
            t["timestamp"] = str(t["timestamp"])
        norm.append(t)
    data["spec"] = spec
    data["turns"] = norm
    return spec, norm


def as_str_list(value):
    """Coerce a ground_truth field to a list of strings (a bare string becomes a 1-item list)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


# --- timestamps --------------------------------------------------------------
def fmt_ts(seconds):
    seconds = int(round(max(0, seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def emulate_timestamps(turns, wpm=150, gap=1.5):
    """Compute internally consistent timestamps from turn length (overwrites authored values)."""
    wps = max(0.1, wpm / 60.0)
    t = 0.0
    for turn in turns:
        turn["timestamp"] = fmt_ts(t)
        words = max(1, len(str(turn.get("text", "")).split()))
        t += words / wps + max(0.0, gap)
    return turns


# --- YAML-safe frontmatter ---------------------------------------------------
def yaml_scalar(value):
    """Render a scalar safely for YAML frontmatter (JSON strings are valid YAML)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def frontmatter(pairs):
    """Build a YAML frontmatter block from an iterable of (key, value)."""
    lines = ["---"]
    for k, v in pairs:
        lines.append(f"{k}: {yaml_scalar(v)}")
    lines.append("---")
    return "\n".join(lines)
