from __future__ import annotations

import logging as _logging
from typing import Optional

from nitro.logging.filters import CorrelationFilter
from nitro.logging.formatters import JsonFormatter, PrettyFormatter

# Track whether the nitro logger has been explicitly configured
_configured: bool = False


def configure_logging(
    level: str = "INFO",
    json_output: bool = True,
    pretty: bool = False,
    logger_name: str = "nitro",
) -> _logging.Logger:
    """Configure the root Nitro logger.

    Args:
        level: Logging level string (e.g. "INFO", "DEBUG").
        json_output: Emit JSON log records (default True).
        pretty: Emit human-readable coloured output.  Overrides *json_output*.
        logger_name: Root logger name (default "nitro").

    Returns:
        The configured :class:`logging.Logger`.
    """
    global _configured

    logger = _logging.getLogger(logger_name)
    log_level = getattr(_logging, level.upper(), _logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicate output on re-configuration
    logger.handlers.clear()

    # Choose formatter
    if pretty:
        formatter: _logging.Formatter = PrettyFormatter()
    elif json_output:
        formatter = JsonFormatter()
    else:
        formatter = _logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler = _logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())

    logger.addHandler(handler)
    logger.propagate = False

    _configured = True
    return logger


def get_logger(name: str) -> _logging.Logger:
    """Return a child logger under the ``nitro`` namespace.

    If :func:`configure_logging` has not been called yet, it is invoked with
    default settings so the returned logger is immediately usable.

    Args:
        name: Sub-logger name.  The returned logger is named ``nitro.<name>``.
    """
    global _configured
    if not _configured:
        configure_logging()
    return _logging.getLogger(f"nitro.{name}")
