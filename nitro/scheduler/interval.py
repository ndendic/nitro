"""
Human-readable interval expressions for the scheduler.

Supports duration strings like ``"30s"``, ``"5m"``, ``"2h"``, ``"1d"``
and combinations like ``"1h30m"``.
"""

from __future__ import annotations

import re
from typing import Optional


_INTERVAL_RE = re.compile(
    r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", re.IGNORECASE
)

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_interval(expr: str) -> float:
    """Parse a human-readable interval string into seconds.

    Args:
        expr: Duration string (e.g. ``"30s"``, ``"5m"``, ``"1h30m"``).

    Returns:
        Total seconds as a float.

    Raises:
        ValueError: If the expression cannot be parsed.

    Examples::

        parse_interval("30s")   # 30.0
        parse_interval("5m")    # 300.0
        parse_interval("1h30m") # 5400.0
        parse_interval("2d")    # 172800.0
    """
    expr = expr.strip()
    if not expr:
        raise ValueError("Empty interval expression")

    # Try simple single-unit form first: "30s", "5m", etc.
    if expr[-1].isalpha() and expr[:-1].isdigit():
        unit = expr[-1].lower()
        if unit not in _UNIT_SECONDS:
            raise ValueError(f"Unknown time unit '{unit}' in {expr!r}")
        total = int(expr[:-1]) * _UNIT_SECONDS[unit]
        if total <= 0:
            raise ValueError(f"Interval must be positive: {expr!r}")
        return float(total)

    # Try compound form: "1h30m", "2d12h", etc.
    match = _INTERVAL_RE.match(expr)
    if match and any(match.groups()):
        days = int(match.group(1) or 0)
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        seconds = int(match.group(4) or 0)
        total = days * 86400 + hours * 3600 + minutes * 60 + seconds
        if total <= 0:
            raise ValueError(f"Interval must be positive: {expr!r}")
        return float(total)

    # Try bare number (treat as seconds)
    try:
        val = float(expr)
        if val <= 0:
            raise ValueError(f"Interval must be positive: {expr!r}")
        return val
    except ValueError:
        pass

    raise ValueError(f"Cannot parse interval: {expr!r}")


def every(interval: str) -> str:
    """Validate an interval expression and return it for use in scheduler.

    This is a convenience function that validates the expression
    at definition time rather than at first run.

    Args:
        interval: Duration string (e.g. ``"30s"``, ``"5m"``).

    Returns:
        The validated interval string prefixed with ``@every/``.

    Raises:
        ValueError: If the expression is invalid.

    Examples::

        @scheduler.job(every("30s"))
        async def cleanup():
            ...
    """
    parse_interval(interval)
    return f"@every/{interval}"


def is_interval_schedule(schedule: str) -> bool:
    """Return ``True`` if the schedule string is an interval (not cron)."""
    return schedule.startswith("@every/")


def extract_interval(schedule: str) -> float:
    """Extract interval seconds from a ``@every/`` prefixed schedule string."""
    if not schedule.startswith("@every/"):
        raise ValueError(f"Not an interval schedule: {schedule!r}")
    return parse_interval(schedule[7:])
