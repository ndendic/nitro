from __future__ import annotations

import functools
import inspect
import logging as _logging
import time
from typing import Any, Callable


def log_action(
    level: str = "INFO",
    include_args: bool = False,
) -> Callable:
    """Decorator that logs entry, exit and errors for a function or method.

    Works with both sync and async callables.

    Args:
        level: Logging level name (e.g. "INFO", "DEBUG").
        include_args: When True, include positional and keyword arguments in
            the entry log record.
    """
    log_level = getattr(_logging, level.upper(), _logging.INFO)

    def decorator(func: Callable) -> Callable:
        logger = _logging.getLogger(f"nitro.{func.__module__}")
        func_name = func.__qualname__

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                extra: dict[str, Any] = {"func": func_name}
                if include_args:
                    extra["args"] = repr(args)
                    extra["kwargs"] = repr(kwargs)
                logger.log(log_level, f"Executing {func_name}", extra=extra)
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = round((time.time() - start) * 1000, 2)
                    logger.log(
                        log_level,
                        f"Completed {func_name}",
                        extra={"func": func_name, "duration_ms": duration_ms},
                    )
                    return result
                except Exception as exc:
                    duration_ms = round((time.time() - start) * 1000, 2)
                    logger.error(
                        f"Failed {func_name}",
                        extra={"func": func_name, "duration_ms": duration_ms},
                        exc_info=exc,
                    )
                    raise

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                extra: dict[str, Any] = {"func": func_name}
                if include_args:
                    extra["args"] = repr(args)
                    extra["kwargs"] = repr(kwargs)
                logger.log(log_level, f"Executing {func_name}", extra=extra)
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = round((time.time() - start) * 1000, 2)
                    logger.log(
                        log_level,
                        f"Completed {func_name}",
                        extra={"func": func_name, "duration_ms": duration_ms},
                    )
                    return result
                except Exception as exc:
                    duration_ms = round((time.time() - start) * 1000, 2)
                    logger.error(
                        f"Failed {func_name}",
                        extra={"func": func_name, "duration_ms": duration_ms},
                        exc_info=exc,
                    )
                    raise

            return sync_wrapper

    return decorator
