"""Schedule-string parser for Telegram's scheduled delivery.

Users pass ``--schedule`` values to the CLI in one of three flavours:
ISO 8601, relative (``+1h``, ``+30m``, ``+2h30m``), or ``tomorrow HH:MM``.
This module centralises the parsing and always returns a tz-aware
datetime so Telethon can convert to UTC before handing off to the API.

Timezone policy: naive inputs are anchored to Europe/Berlin to match
the user's locale and skill A's behaviour. Inputs that already carry
a tzoffset are respected verbatim.
"""
from __future__ import annotations

import re
import zoneinfo
from datetime import datetime, timedelta


LOCAL_TZ = zoneinfo.ZoneInfo("Europe/Berlin")

_RELATIVE_RE = re.compile(r"^\+(?:(\d+)h)?(?:(\d+)m)?$")
_TOMORROW_RE = re.compile(r"^tomorrow\s+(\d{1,2}):(\d{2})$", re.IGNORECASE)


def parse_schedule(value: str) -> datetime:
    """Parse a schedule string into a tz-aware datetime.

    Raises ``ValueError`` for anything that doesn't match one of the
    three supported forms.
    """
    if value is None:
        raise ValueError("Schedule value is required")

    value = value.strip()
    if not value:
        raise ValueError(
            "Empty schedule. Use ISO (2026-04-10T10:00), relative (+1h, +30m), or 'tomorrow HH:MM'."
        )

    rel = _RELATIVE_RE.match(value)
    if rel and (rel.group(1) or rel.group(2)):
        hours = int(rel.group(1) or 0)
        minutes = int(rel.group(2) or 0)
        return datetime.now(LOCAL_TZ) + timedelta(hours=hours, minutes=minutes)

    tom = _TOMORROW_RE.match(value)
    if tom:
        tomorrow = datetime.now(LOCAL_TZ) + timedelta(days=1)
        return tomorrow.replace(
            hour=int(tom.group(1)), minute=int(tom.group(2)),
            second=0, microsecond=0,
        )

    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"Cannot parse schedule: '{value}'. "
            "Use ISO (2026-04-10T10:00), relative (+1h, +30m), or 'tomorrow HH:MM'."
        )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LOCAL_TZ)
    return dt


__all__ = ["parse_schedule", "LOCAL_TZ"]
