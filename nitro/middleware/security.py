"""
Security headers middleware.

Adds common security headers to every response to protect against
clickjacking, content-type sniffing, XSS, and other browser-level
attacks.
"""

from __future__ import annotations

from typing import Optional

from .base import MiddlewareContext, MiddlewareInterface


class SecurityMiddleware(MiddlewareInterface):
    """Add security headers to every response.

    All headers are configurable.  Set a header value to ``None`` to
    skip it entirely.

    Args:
        content_security_policy: CSP header value.  ``None`` to skip.
        x_frame_options: Frame embedding policy (``"DENY"`` or
            ``"SAMEORIGIN"``).  ``None`` to skip.
        x_content_type_options: Prevents MIME-sniffing.  Default
            ``"nosniff"``.
        strict_transport_security: HSTS header value.  ``None`` to skip
            (only useful over HTTPS).
        referrer_policy: Controls the Referer header.
        permissions_policy: Permissions-Policy header.  ``None`` to skip.
        x_xss_protection: Legacy XSS filter header.  ``"0"`` disables
            the filter (modern recommendation).

    Example::

        SecurityMiddleware(
            content_security_policy="default-src 'self'",
            strict_transport_security="max-age=31536000; includeSubDomains",
        )
    """

    def __init__(
        self,
        content_security_policy: Optional[str] = None,
        x_frame_options: Optional[str] = "DENY",
        x_content_type_options: Optional[str] = "nosniff",
        strict_transport_security: Optional[str] = None,
        referrer_policy: Optional[str] = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None,
        x_xss_protection: Optional[str] = "0",
    ) -> None:
        self._headers: dict[str, str] = {}
        _mapping = {
            "Content-Security-Policy": content_security_policy,
            "X-Frame-Options": x_frame_options,
            "X-Content-Type-Options": x_content_type_options,
            "Strict-Transport-Security": strict_transport_security,
            "Referrer-Policy": referrer_policy,
            "Permissions-Policy": permissions_policy,
            "X-XSS-Protection": x_xss_protection,
        }
        for header, value in _mapping.items():
            if value is not None:
                self._headers[header] = value

    def after_response(self, ctx: MiddlewareContext) -> MiddlewareContext:
        # Security headers are set in after_response so they apply to
        # all responses, including error responses.
        for header, value in self._headers.items():
            # Don't overwrite headers already set by the handler
            if header not in ctx.headers:
                ctx.headers[header] = value
        return ctx
