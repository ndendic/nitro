"""
Content negotiation for API responses.

All helpers are framework-agnostic: they operate on any object that
exposes a ``headers`` dict-like attribute (duck typing).
"""

from __future__ import annotations

import json
from typing import Any, Callable, Optional

from .responses import ApiResponse


def wants_json(request: Any) -> bool:
    """Return True when the request prefers a JSON response.

    Checks the ``Accept`` header for ``application/json``.
    Defaults to False when the header is absent or set to ``*/*`` /
    ``text/html``.
    """
    accept = ""
    headers = getattr(request, "headers", {})
    if isinstance(headers, dict):
        # Case-insensitive lookup
        for key, value in headers.items():
            if key.lower() == "accept":
                accept = value
                break
    else:
        accept = str(headers.get("accept", "") or headers.get("Accept", ""))

    return "application/json" in accept


def json_response(data: Any, status: int = 200) -> dict:
    """Build a framework-agnostic JSON response descriptor.

    Returns a plain dict with ``status`` and ``body`` keys so that
    any framework adapter can turn it into a real HTTP response.
    """
    if isinstance(data, ApiResponse):
        body = data.to_json()
    else:
        body = json.dumps(data)
    return {"status": status, "body": body, "content_type": "application/json"}


def negotiate(
    request: Any,
    data: Any,
    html_renderer: Optional[Callable[[Any], Any]] = None,
) -> Any:
    """Return a JSON or HTML response based on the request's Accept header.

    - ``application/json`` → returns :func:`json_response` dict
    - ``text/html`` (or no preference) → calls ``html_renderer(data)`` when
      provided, otherwise falls back to :func:`json_response`
    """
    if wants_json(request):
        if not isinstance(data, ApiResponse):
            data = ApiResponse.success(data)
        return json_response(data)

    if html_renderer is not None:
        return html_renderer(data)

    # No renderer provided — fall back to JSON
    if not isinstance(data, ApiResponse):
        data = ApiResponse.success(data)
    return json_response(data)


class NegotiatedResponse:
    """Helper that pairs data with an optional HTML renderer.

    Designed for use inside entity methods or view handlers where the
    same data might be rendered as HTML or JSON depending on the caller.

    Usage::

        class ProductView:
            def detail(self, request, product):
                def render_html(data):
                    return ProductCard(data)

                return NegotiatedResponse(product, html_renderer=render_html).resolve(request)
    """

    def __init__(
        self,
        data: Any,
        html_renderer: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        self.data = data
        self.html_renderer = html_renderer

    def resolve(self, request: Any) -> Any:
        """Negotiate and return the appropriate response for *request*."""
        return negotiate(request, self.data, self.html_renderer)
