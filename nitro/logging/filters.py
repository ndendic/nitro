from __future__ import annotations

import logging as _logging


class CorrelationFilter(_logging.Filter):
    """Inject the current correlation_id into every log record.

    This allows formatters that reference ``record.correlation_id`` to work
    without fetching the context var themselves.
    """

    def filter(self, record: _logging.LogRecord) -> bool:  # noqa: A003
        from nitro.logging.context import correlation_id
        record.correlation_id = correlation_id()
        return True
