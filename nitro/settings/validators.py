"""Reusable validation helpers for settings fields."""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlparse


def validate_range(
    value: int | float,
    *,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    name: str = "value",
) -> int | float:
    """Validate a numeric value is within a range.

    Usage in a Pydantic model_validator::

        @model_validator(mode="after")
        def check_port(self):
            validate_range(self.port, min_val=1, max_val=65535, name="port")
            return self

    Raises:
        ValueError: If the value is outside the specified range.
    """
    if min_val is not None and value < min_val:
        raise ValueError(f"{name} must be >= {min_val}, got {value}")
    if max_val is not None and value > max_val:
        raise ValueError(f"{name} must be <= {max_val}, got {value}")
    return value


def validate_url(
    value: str,
    *,
    schemes: tuple[str, ...] = ("http", "https", "postgresql", "sqlite", "redis"),
    name: str = "url",
) -> str:
    """Validate that a string is a well-formed URL with an allowed scheme.

    Usage::

        @model_validator(mode="after")
        def check_urls(self):
            validate_url(self.db_url, schemes=("postgresql", "sqlite"), name="db_url")
            return self

    Raises:
        ValueError: If the URL is malformed or uses a disallowed scheme.
    """
    try:
        parsed = urlparse(value)
    except Exception as e:
        raise ValueError(f"{name} is not a valid URL: {value!r}") from e
    if not parsed.scheme:
        raise ValueError(f"{name} must have a scheme (got {value!r})")
    if schemes and parsed.scheme not in schemes:
        raise ValueError(
            f"{name} scheme must be one of {schemes}, got {parsed.scheme!r}"
        )
    return value


def cross_validate(
    *fields: str,
    rule: Callable[..., bool],
    message: str,
) -> Callable[[Any], Any]:
    """Create a cross-field validator for use as a Pydantic model_validator.

    Returns a validator function that checks a condition across multiple fields.

    Usage::

        class MySettings(AppSettings):
            min_pool: int = 1
            max_pool: int = 10

            _check_pool = model_validator(mode="after")(
                cross_validate(
                    "min_pool", "max_pool",
                    rule=lambda min_pool, max_pool: min_pool <= max_pool,
                    message="min_pool must be <= max_pool",
                )
            )
    """

    def validator(self: Any) -> Any:
        values = [getattr(self, f) for f in fields]
        if not rule(*values):
            raise ValueError(message)
        return self

    return validator
