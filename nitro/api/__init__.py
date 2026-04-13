"""
nitro.api — Standardized API response formatting for the Nitro framework.

Provides:
- ApiResponse        : Standard envelope (data, meta, errors, success flag)
- PaginationMeta     : Pagination metadata with computed total_pages
- ErrorDetail        : Structured per-field error info
- ApiError           : Base API exception with status_code
- NotFoundError      : 404
- ValidationError    : 422 with optional field-level details
- AuthenticationError: 401
- ForbiddenError     : 403
- ConflictError      : 409
- RateLimitError     : 429
- error_handler      : Convert ApiError → ApiResponse
- from_pydantic_error: Convert pydantic.ValidationError → ApiResponse
- negotiate          : Return JSON or HTML based on Accept header
- wants_json         : True when request prefers application/json
- json_response      : Framework-agnostic JSON response descriptor
- NegotiatedResponse : Helper class pairing data with an HTML renderer

Quick start::

    from nitro.api import ApiResponse, NotFoundError, error_handler

    # Success response
    resp = ApiResponse.success({"id": 1, "name": "Alice"})
    resp.to_dict()   # {'data': ..., 'meta': None, 'errors': None, 'success': True}
    resp.to_json()   # JSON string

    # Error response
    resp = ApiResponse.error("User not found", code="not_found")

    # Paginated response
    resp = ApiResponse.paginated(items=[...], total=100, page=1, page_size=20)
    # meta includes total_pages=5

    # Exception-based errors
    raise NotFoundError("Item 42 does not exist")

    # Convert exception to response
    try:
        raise NotFoundError("Item 42 does not exist")
    except ApiError as exc:
        resp = error_handler(exc)

    # Content negotiation
    from nitro.api import negotiate

    def my_handler(request, data):
        return negotiate(request, data, html_renderer=lambda d: MyComponent(d))
"""

from .responses import ApiResponse, PaginationMeta, ErrorDetail
from .errors import (
    ApiError,
    NotFoundError,
    ValidationError,
    AuthenticationError,
    ForbiddenError,
    ConflictError,
    RateLimitError,
    error_handler,
    from_pydantic_error,
)
from .negotiation import negotiate, wants_json, json_response, NegotiatedResponse

__all__ = [
    # Response models
    "ApiResponse",
    "PaginationMeta",
    "ErrorDetail",
    # Exceptions
    "ApiError",
    "NotFoundError",
    "ValidationError",
    "AuthenticationError",
    "ForbiddenError",
    "ConflictError",
    "RateLimitError",
    # Converters
    "error_handler",
    "from_pydantic_error",
    # Content negotiation
    "negotiate",
    "wants_json",
    "json_response",
    "NegotiatedResponse",
]
