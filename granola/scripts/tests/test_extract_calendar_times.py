import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from granola import extract_calendar_times


def test_extract_calendar_times_returns_start_and_end_from_calendar_event():
    doc = {
        "google_calendar_event": {
            "start": {"dateTime": "2026-02-28T10:00:00+01:00"},
            "end": {"dateTime": "2026-02-28T11:00:00+01:00"}
        }
    }
    start, end = extract_calendar_times(doc)
    assert start == "2026-02-28T10:00:00+01:00"
    assert end == "2026-02-28T11:00:00+01:00"


def test_extract_calendar_times_returns_none_for_missing_event():
    doc = {}
    start, end = extract_calendar_times(doc)
    assert start is None
    assert end is None


def test_extract_calendar_times_returns_none_for_non_dict_event():
    doc = {"google_calendar_event": None}
    start, end = extract_calendar_times(doc)
    assert start is None
    assert end is None
