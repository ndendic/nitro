"""
Session middleware — loads sessions on request, saves on response.

Works with the nitro.middleware pipeline or standalone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .base import SessionData, SessionInterface, generate_session_id
from .cookie_store import CookieSessionStore


@dataclass
class SessionConfig:
    """Configuration for session middleware behavior.

    Attributes:
        cookie_name: Name of the session cookie (default: "nitro_session").
        cookie_path: Cookie path scope (default: "/").
        cookie_domain: Cookie domain (default: None — current domain).
        cookie_secure: Require HTTPS for the cookie (default: False).
        cookie_httponly: Block JavaScript access to the cookie (default: True).
        cookie_samesite: SameSite policy: "Lax", "Strict", or "None" (default: "Lax").
        cookie_max_age: Cookie max-age in seconds (default: None — session cookie).
    """

    cookie_name: str = "nitro_session"
    cookie_path: str = "/"
    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_httponly: bool = True
    cookie_samesite: str = "Lax"
    cookie_max_age: int | None = None


class SessionMiddleware:
    """Loads and persists sessions automatically around request handling.

    On request: reads the session cookie, loads session data from the store,
    and attaches a SessionData object to the request context.

    On response: if session was modified, saves to the store and sets
    the session cookie.

    Args:
        store: A session backend implementing SessionInterface.
        config: Optional SessionConfig for cookie settings.

    Example::

        from nitro.sessions import MemorySessionStore, SessionMiddleware

        store = MemorySessionStore(ttl=3600)
        mw = SessionMiddleware(store)
    """

    def __init__(
        self,
        store: SessionInterface,
        config: SessionConfig | None = None,
    ):
        self.store = store
        self.config = config or SessionConfig()

    async def load_session(self, cookie_value: str | None) -> SessionData:
        """Load a session from a cookie value.

        Args:
            cookie_value: The raw cookie value, or None if no cookie.

        Returns:
            A SessionData instance (new or loaded from store).
        """
        if cookie_value:
            if isinstance(self.store, CookieSessionStore):
                data = await self.store.load(cookie_value)
                if data is not None:
                    # For cookie sessions, use the cookie value as the session_id
                    return SessionData(cookie_value, data, is_new=False)
            else:
                data = await self.store.load(cookie_value)
                if data is not None:
                    return SessionData(cookie_value, data, is_new=False)

        # New session
        session_id = generate_session_id()
        return SessionData(session_id, is_new=True)

    async def save_session(self, session: SessionData) -> str | None:
        """Save a session and return the cookie value to set.

        Returns:
            The cookie value to set, or None if no cookie change needed.
            For invalidated sessions, returns empty string (signals deletion).
        """
        if session.is_invalidated:
            if not session.is_new:
                await self.store.delete(session.session_id)
            return ""  # Signal: delete the cookie

        if not session.modified and not session.is_new:
            return None  # No changes, no cookie update needed

        if isinstance(self.store, CookieSessionStore):
            # Encode data directly into cookie
            return self.store.encode(session.to_dict())
        else:
            await self.store.save(session.session_id, session.to_dict())
            return session.session_id

    def build_cookie_attrs(self, max_age: int | None = None) -> dict[str, Any]:
        """Build cookie attributes dict for the framework to set.

        Args:
            max_age: Override max-age (use 0 to delete the cookie).

        Returns:
            Dict of cookie attributes.
        """
        cfg = self.config
        attrs: dict[str, Any] = {
            "path": cfg.cookie_path,
            "httponly": cfg.cookie_httponly,
            "samesite": cfg.cookie_samesite,
        }
        if cfg.cookie_domain:
            attrs["domain"] = cfg.cookie_domain
        if cfg.cookie_secure:
            attrs["secure"] = True
        if max_age is not None:
            attrs["max_age"] = max_age
        elif cfg.cookie_max_age is not None:
            attrs["max_age"] = cfg.cookie_max_age
        return attrs
