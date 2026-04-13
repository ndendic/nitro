"""
API response models for standardized envelope formatting.
"""

from __future__ import annotations

import json
import math
from typing import Any, List, Optional

from pydantic import BaseModel, model_validator


class ErrorDetail(BaseModel):
    """Structured error information."""

    message: str
    code: Optional[str] = None
    field: Optional[str] = None


class PaginationMeta(BaseModel):
    """Pagination metadata with computed total_pages."""

    total: int
    page: int
    page_size: int
    total_pages: int = 0

    @model_validator(mode="after")
    def compute_total_pages(self) -> "PaginationMeta":
        if self.page_size > 0:
            self.total_pages = math.ceil(self.total / self.page_size)
        else:
            self.total_pages = 0
        return self


class _ApiResponseBase(BaseModel):
    """Internal base — holds the fields without name collision."""

    data: Any = None
    meta: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None
    success: bool = True

    # ------------------------------------------------------------------ #
    # Serialisation helpers
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        """Return the response as a plain dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Return the response as a JSON string."""
        return self.model_dump_json()


def _success(
    cls: type,
    data: Any,
    meta: Optional[dict] = None,
) -> "_ApiResponseBase":
    """Build a success response."""
    return cls(data=data, meta=meta, errors=None, success=True)


def _error(
    cls: type,
    message: str,
    code: Optional[str] = None,
    details: Optional[List[ErrorDetail]] = None,
) -> "_ApiResponseBase":
    """Build an error response."""
    error_list = details or [ErrorDetail(message=message, code=code)]
    return cls(data=None, meta=None, errors=error_list, success=False)


def _paginated(
    cls: type,
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> "_ApiResponseBase":
    """Build a paginated response with meta."""
    pagination = PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
    )
    return cls(
        data=items,
        meta=pagination.model_dump(),
        errors=None,
        success=True,
    )


class _ApiResponseMeta(type(_ApiResponseBase)):
    """Metaclass that injects named factory classmethods after Pydantic setup."""

    def __getattr__(cls, name: str) -> Any:
        if name == "success":
            return lambda data, meta=None: _success(cls, data, meta)
        if name == "error":
            return lambda message, code=None, details=None: _error(
                cls, message, code, details
            )
        if name == "paginated":
            return lambda items, total, page, page_size: _paginated(
                cls, items, total, page, page_size
            )
        raise AttributeError(name)


class ApiResponse(_ApiResponseBase, metaclass=_ApiResponseMeta):
    """Standard API response envelope.

    Instantiate via the factory class-methods::

        ApiResponse.success(data, meta=None)
        ApiResponse.error(message, code=None, details=None)
        ApiResponse.paginated(items, total, page, page_size)

    Direct construction is also supported::

        ApiResponse(data=..., errors=None, success=True)
    """
