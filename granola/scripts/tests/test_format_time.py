import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from granola import format_time


def test_format_time_converts_iso_to_hhmm():
    assert format_time("2026-02-28T10:15:00+01:00") == "10:15"


def test_format_time_returns_question_mark_for_none():
    assert format_time(None) == "?"


def test_format_time_returns_question_mark_for_invalid():
    assert format_time("not-a-date") == "?"
