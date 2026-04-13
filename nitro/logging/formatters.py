from __future__ import annotations

import json
import logging as _logging
import sys
import traceback
from datetime import datetime, timezone


# ANSI colour codes for terminal output
_COLOURS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}


def _supports_colour() -> bool:
    """Return True when stdout looks like a colour-capable terminal."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class JsonFormatter(_logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: _logging.LogRecord) -> str:  # noqa: A003
        # Resolve the correlation_id that CorrelationFilter may have attached
        cid = getattr(record, "correlation_id", None)
        if cid is None:
            from nitro.logging.context import correlation_id
            cid = correlation_id()

        payload: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": cid,
        }

        # Append exception traceback when present
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        elif record.exc_text:
            payload["exc"] = record.exc_text

        # Any extra fields set by the caller via LogRecord.__dict__
        _skip = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "correlation_id", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in _skip:
                payload[key] = value

        return json.dumps(payload, default=str)


class PrettyFormatter(_logging.Formatter):
    """Human-readable formatter for development use.

    Example output:
        [2026-04-13 15:00:00] INFO  [abc123] nitro.auth: User logged in
    """

    def format(self, record: _logging.LogRecord) -> str:  # noqa: A003
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        cid = getattr(record, "correlation_id", None)
        if cid is None:
            from nitro.logging.context import correlation_id
            cid = correlation_id()

        level = record.levelname.ljust(8)
        if _supports_colour():
            colour = _COLOURS.get(record.levelname, "")
            reset = _COLOURS["RESET"]
            level = f"{colour}{level}{reset}"

        line = f"[{ts}] {level} [{cid}] {record.name}: {record.getMessage()}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        elif record.exc_text:
            line += "\n" + record.exc_text

        return line
