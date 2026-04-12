"""
Nitro Auth — Framework-agnostic authentication decorators.

These decorators work with any async Python web framework (Sanic, FastAPI, etc.)
by extracting tokens from common locations without importing framework-specific code.

Usage pattern:

    auth = AuthService(secret="my-secret")

    @require_auth(auth)
    async def protected_view(request, current_user: TokenPayload):
        return {"user": current_user.sub}

    @require_auth(auth)
    @require_role("admin")
    async def admin_view(request, current_user: TokenPayload):
        return {"ok": True}
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Optional

from .service import AuthService, TokenPayload


class AuthError(Exception):
    """Raised when authentication or authorisation fails.

    Attributes:
        message: Human-readable error description.
        status_code: Suggested HTTP status code (401 or 403).
    """

    def __init__(self, message: str = "Authentication required", status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def require_auth(
    auth_service: AuthService,
    token_extractor: Optional[Callable] = None,
):
    """Decorator that requires a valid authentication token.

    Injects ``current_user: TokenPayload`` into the wrapped function's kwargs.

    Token resolution order (when no custom extractor is provided):
    1. ``Authorization: Bearer <token>`` header
    2. ``auth_token`` cookie
    3. ``auth_token`` key in a ``signals`` kwarg dict (Datastar support)

    Args:
        auth_service: The AuthService instance used to verify tokens.
        token_extractor: Optional callable ``(request) -> str | None`` that
            returns the raw token string from the request object.

    Raises:
        AuthError(401): If no token is present or the token is invalid/expired.

    Example::

        auth = AuthService(secret="s3cr3t")

        @require_auth(auth)
        async def my_view(request, current_user: TokenPayload):
            return {"sub": current_user.sub}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Locate the request object — first positional arg after self (args[1])
            # or the sole positional arg (args[0]) for standalone handlers.
            request = kwargs.get("request") or (
                args[1] if len(args) > 1 else args[0] if args else None
            )

            token: Optional[str] = None

            if token_extractor is not None:
                token = token_extractor(request)
            else:
                # 1. Authorization: Bearer <token>
                auth_header: str = (
                    getattr(request, "headers", {}).get("authorization", "") or ""
                )
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]

                # 2. Cookie
                if not token:
                    cookies: dict = getattr(request, "cookies", {}) or {}
                    token = cookies.get("auth_token")

                # 3. Datastar signals dict
                if not token:
                    signals = kwargs.get("signals", {})
                    if isinstance(signals, dict):
                        token = signals.get("auth_token")

            if not token:
                raise AuthError("No authentication token provided", 401)

            payload = auth_service.decode_token(token)
            if payload is None:
                raise AuthError("Invalid or expired token", 401)

            kwargs["current_user"] = payload
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(*roles: str, auth_service: Optional[AuthService] = None):
    """Decorator that requires the user to hold at least one of the listed roles.

    Must be applied *after* ``@require_auth`` (i.e. closer to the function body)
    so that ``current_user`` is already present in kwargs.

    Args:
        *roles: One or more role names; the user needs to match at least one.
        auth_service: Unused; kept for API consistency / future extensions.

    Raises:
        AuthError(401): If ``current_user`` is missing (no auth decorator above).
        AuthError(403): If the user does not hold any of the required roles.

    Example::

        @require_auth(auth)
        @require_role("admin", "editor")
        async def editor_view(request, current_user: TokenPayload):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user: Optional[TokenPayload] = kwargs.get("current_user")
            if current_user is None:
                raise AuthError("Authentication required", 401)
            if not any(role in current_user.roles for role in roles):
                raise AuthError(
                    f"Requires one of roles: {', '.join(roles)}", 403
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
