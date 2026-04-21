from __future__ import annotations
import re
from skill_studio.presets import load_preset


FORCES_SIGNALS = re.compile(r"\b(stuck|meant to|never do|avoid|keep meaning|procrastina\w+|dread|anxious|afraid)\b", re.I)
OUTCOMES_SIGNALS = re.compile(r"\b(\d+\s*(hour|min|%|percent)|reduce|cut|speed up|down to|from \d)\b", re.I)
FSE_SIGNALS = re.compile(r"\b(team|colleagues|boss|client|reputation|image|seen as|come across)\b", re.I)


def suggest_frame(transcript: str, preset: str) -> str:
    text = transcript.lower()
    if OUTCOMES_SIGNALS.search(text):
        return "outcomes"
    if FSE_SIGNALS.search(text):
        return "fse"
    if FORCES_SIGNALS.search(text):
        return "forces"
    return load_preset(preset).default_jtbd_frame
