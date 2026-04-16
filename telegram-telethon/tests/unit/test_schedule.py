"""Tests for the schedule-string parser.

Accepts three forms:
- ISO 8601 (``2026-04-10T10:00`` or ``2026-04-10 10:00``)
- Relative from now (``+1h``, ``+30m``, ``+2h30m``)
- Natural ``tomorrow HH:MM``

All naive inputs are anchored to Europe/Berlin (CET) — that's the user's
timezone and matches skill A. The returned datetime is always tz-aware.
"""
from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta

import pytest

from telegram_telethon.modules.schedule import parse_schedule


CET = zoneinfo.ZoneInfo("Europe/Berlin")


class TestRelative:
    def test_plus_hours(self):
        before = datetime.now(CET)
        result = parse_schedule("+1h")
        after = datetime.now(CET)
        delta_before = result - before
        delta_after = result - after
        # result is between now and now + small skew, offset by 1h
        assert timedelta(hours=1) - timedelta(seconds=2) <= delta_after
        assert delta_before <= timedelta(hours=1) + timedelta(seconds=2)

    def test_plus_minutes(self):
        before = datetime.now(CET)
        result = parse_schedule("+30m")
        assert result > before
        # ~30 minutes from now, allow 5s skew
        assert abs((result - before).total_seconds() - 30 * 60) < 5

    def test_plus_hours_and_minutes(self):
        before = datetime.now(CET)
        result = parse_schedule("+2h30m")
        assert abs((result - before).total_seconds() - 150 * 60) < 5

    def test_relative_is_tz_aware(self):
        assert parse_schedule("+1h").tzinfo is not None


class TestTomorrow:
    def test_tomorrow_sets_time(self):
        result = parse_schedule("tomorrow 10:00")
        today = datetime.now(CET).date()
        assert result.date() == today + timedelta(days=1)
        assert result.hour == 10 and result.minute == 0 and result.second == 0

    def test_tomorrow_case_insensitive(self):
        assert parse_schedule("Tomorrow 14:30").hour == 14
        assert parse_schedule("TOMORROW 14:30").minute == 30

    def test_tomorrow_is_tz_aware(self):
        assert parse_schedule("tomorrow 09:15").tzinfo is not None


class TestIso:
    def test_iso_datetime_with_t(self):
        result = parse_schedule("2027-01-15T09:30")
        assert result.year == 2027 and result.month == 1 and result.day == 15
        assert result.hour == 9 and result.minute == 30

    def test_iso_datetime_with_space(self):
        result = parse_schedule("2027-01-15 09:30")
        assert result.hour == 9 and result.minute == 30

    def test_naive_iso_is_anchored_to_cet(self):
        # No tz in input → treat as CET.
        result = parse_schedule("2027-01-15T09:30")
        assert result.tzinfo is not None
        assert result.utcoffset() == datetime(2027, 1, 15, tzinfo=CET).utcoffset()

    def test_iso_with_explicit_tz_preserved(self):
        result = parse_schedule("2027-01-15T09:30+00:00")
        # UTC input stays UTC, not remapped to CET
        assert result.utcoffset() == timedelta(0)


class TestErrors:
    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_schedule("")

    def test_gibberish_raises(self):
        with pytest.raises(ValueError) as exc:
            parse_schedule("next Tuesday-ish")
        assert "Cannot parse schedule" in str(exc.value)

    def test_error_lists_supported_formats(self):
        with pytest.raises(ValueError) as exc:
            parse_schedule("bad")
        msg = str(exc.value)
        assert "ISO" in msg and "tomorrow" in msg
