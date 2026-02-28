import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from granola import compute_duration


def test_compute_duration_from_utterance_timestamps():
    utterances = [
        {"start_timestamp": "2026-02-28T10:00:00Z", "end_timestamp": "2026-02-28T10:05:00Z"},
        {"start_timestamp": "2026-02-28T10:30:00Z", "end_timestamp": "2026-02-28T11:27:00Z"},
    ]
    assert compute_duration(utterances) == "01:27"


def test_compute_duration_returns_none_for_empty_list():
    assert compute_duration([]) is None


def test_compute_duration_returns_none_for_missing_timestamps():
    utterances = [{"start_timestamp": "", "end_timestamp": ""}]
    assert compute_duration(utterances) is None
