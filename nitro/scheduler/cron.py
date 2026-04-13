"""
Lightweight cron expression parser — no external dependencies.

Supports standard 5-field cron expressions::

    ┌───────────── minute (0–59)
    │ ┌───────────── hour (0–23)
    │ │ ┌───────────── day of month (1–31)
    │ │ │ ┌───────────── month (1–12)
    │ │ │ │ ┌───────────── day of week (0–6, 0 = Sunday)
    │ │ │ │ │
    * * * * *

Supports: ``*``, ranges (``1-5``), steps (``*/15``), lists (``1,3,5``),
and combinations (``1-5/2``).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional, Set


class CronExpr:
    """Parsed cron expression that can compute next-run times.

    Args:
        expression: Standard 5-field cron string.

    Raises:
        ValueError: If the expression is malformed.

    Examples::

        cron = CronExpr("*/5 * * * *")      # every 5 minutes
        cron = CronExpr("0 9 * * 1-5")      # 9am weekdays
        cron = CronExpr("30 2 1 * *")       # 2:30am on the 1st
    """

    __slots__ = ("_expression", "_minutes", "_hours", "_days", "_months", "_weekdays")

    def __init__(self, expression: str) -> None:
        self._expression = expression.strip()
        fields = self._expression.split()
        if len(fields) != 5:
            raise ValueError(
                f"Cron expression must have 5 fields, got {len(fields)}: {expression!r}"
            )
        self._minutes = self._parse_field(fields[0], 0, 59)
        self._hours = self._parse_field(fields[1], 0, 23)
        self._days = self._parse_field(fields[2], 1, 31)
        self._months = self._parse_field(fields[3], 1, 12)
        self._weekdays = self._parse_field(fields[4], 0, 6)

    @property
    def expression(self) -> str:
        return self._expression

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def matches(self, dt: datetime) -> bool:
        """Return ``True`` if the given datetime matches this cron expression."""
        return (
            dt.minute in self._minutes
            and dt.hour in self._hours
            and dt.day in self._days
            and dt.month in self._months
            and dt.weekday() in self._translate_weekday(self._weekdays)
        )

    def next_fire_time(self, after: Optional[float] = None) -> float:
        """Compute the next fire time (unix timestamp) after the given time.

        Args:
            after: Unix timestamp to compute from. Defaults to now.

        Returns:
            Unix timestamp of the next matching minute.
        """
        if after is None:
            after = time.time()

        dt = datetime.fromtimestamp(after, tz=timezone.utc).replace(second=0, microsecond=0)

        # Advance at least one minute
        dt = dt.replace(minute=dt.minute)
        from datetime import timedelta

        dt += timedelta(minutes=1)

        # Walk forward until we find a match, with a safety limit
        py_weekdays = self._translate_weekday(self._weekdays)
        for _ in range(525960):  # ~1 year of minutes
            if (
                dt.minute in self._minutes
                and dt.hour in self._hours
                and dt.day in self._days
                and dt.month in self._months
                and dt.weekday() in py_weekdays
            ):
                return dt.timestamp()
            dt += timedelta(minutes=1)

        raise RuntimeError(f"Could not find next fire time for {self._expression!r}")

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_field(field: str, lo: int, hi: int) -> Set[int]:
        """Parse a single cron field into a set of valid integers."""
        result: Set[int] = set()
        for part in field.split(","):
            part = part.strip()
            if "/" in part:
                base, step_str = part.split("/", 1)
                step = int(step_str)
                if step <= 0:
                    raise ValueError(f"Step must be positive, got {step}")
                if base == "*":
                    start, end = lo, hi
                elif "-" in base:
                    s, e = base.split("-", 1)
                    start, end = int(s), int(e)
                else:
                    start, end = int(base), hi
                result.update(range(start, end + 1, step))
            elif "-" in part:
                s, e = part.split("-", 1)
                start, end = int(s), int(e)
                if start > end:
                    raise ValueError(f"Invalid range: {start}-{end}")
                result.update(range(start, end + 1))
            elif part == "*":
                result.update(range(lo, hi + 1))
            else:
                val = int(part)
                if val < lo or val > hi:
                    raise ValueError(f"Value {val} out of range [{lo}, {hi}]")
                result.add(val)
        return result

    @staticmethod
    def _translate_weekday(cron_weekdays: Set[int]) -> Set[int]:
        """Translate cron weekday numbers (0=Sun) to Python weekday numbers (0=Mon)."""
        mapping = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
        return {mapping[d] for d in cron_weekdays}

    def __repr__(self) -> str:
        return f"CronExpr({self._expression!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CronExpr):
            return self._expression == other._expression
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._expression)
