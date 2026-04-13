"""
API error classes and conversion helpers.
"""

from __future__ import annotations

from typing import Any, List, Optional

from .responses import ApiResponse, ErrorDetail


# ------------------------------------------------------------------ #
# Exception hierarchy
# ------------------------------------------------------------------ #


class ApiError(Exception):
    """Base exception for all API errors."""

    status_code: int = 500
    default_code: str = "internal_error"

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[List[ErrorDetail]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        if status_code is not None:
            self.status_code = status_code
        self.details = details


class NotFoundError(ApiError):
    """404 Not Found."""

    status_code = 404
    default_code = "not_found"


class ValidationError(ApiError):
    """422 Unprocessable Entity — field-level validation errors."""

    status_code = 422
    default_code = "validation_error"

    def __init__(
        self,
        message: str = "Validation failed",
        code: Optional[str] = None,
        field_errors: Optional[List[ErrorDetail]] = None,
    ) -> None:
        super().__init__(message=message, code=code, details=field_errors)


class AuthenticationError(ApiError):
    """401 Unauthorized."""

    status_code = 401
    default_code = "authentication_required"


class ForbiddenError(ApiError):
    """403 Forbidden."""

    status_code = 403
    default_code = "forbidden"


class ConflictError(ApiError):
    """409 Conflict."""

    status_code = 409
    default_code = "conflict"


class RateLimitError(ApiError):
    """429 Too Many Requests."""

    status_code = 429
    default_code = "rate_limit_exceeded"


# ------------------------------------------------------------------ #
# Conversion helpers
# ------------------------------------------------------------------ #


def error_handler(exception: ApiError) -> ApiResponse:
    """Convert any ApiError into an ApiResponse."""
    details = exception.details or [
        ErrorDetail(message=exception.message, code=exception.code)
    ]
    return ApiResponse(data=None, meta=None, errors=details, success=False)


def from_pydantic_error(exc: Any) -> ApiResponse:
    """Convert a Pydantic ValidationError into an ApiResponse.

    Works with pydantic.ValidationError instances. Each error in
    ``exc.errors()`` is mapped to an ErrorDetail with the field path
    encoded in ``field``.
    """
    details: List[ErrorDetail] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field = ".".join(str(p) for p in loc) if loc else None
        details.append(
            ErrorDetail(
                message=err.get("msg", "validation error"),
                code=err.get("type"),
                field=field,
            )
        )
    return ApiResponse(data=None, meta=None, errors=details, success=False)
