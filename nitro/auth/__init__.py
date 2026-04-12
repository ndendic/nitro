"""
nitro.auth — Framework-agnostic authentication for the Nitro framework.

Provides:
- AuthService     : HMAC-SHA256 token creation/verification + password hashing
- TokenPayload    : Pydantic model for decoded token data
- User            : SQLModel-backed user entity
- SessionStore    : In-memory server-side sessions with TTL
- Session         : Lightweight session object
- require_auth    : Decorator — injects current_user into handler kwargs
- require_role    : Decorator — enforces role-based access control
- AuthError       : Exception raised by decorators on auth failure

Quick start::

    from nitro.auth import AuthService, User, require_auth, require_role

    auth = AuthService(secret="change-me-in-production")

    # Register
    user = auth.register("alice@example.com", "s3cr3t", roles=["editor"])

    # Login
    result = auth.authenticate("alice@example.com", "s3cr3t")
    if result:
        user, access_token, refresh_token = result

    # Protect a route
    @require_auth(auth)
    @require_role("editor")
    async def create_post(request, current_user):
        ...
"""

from .service import AuthService, TokenPayload
from .models import User
from .sessions import SessionStore, Session
from .decorators import require_role, require_auth, AuthError

__all__ = [
    "AuthService",
    "TokenPayload",
    "User",
    "SessionStore",
    "Session",
    "require_auth",
    "require_role",
    "AuthError",
]
