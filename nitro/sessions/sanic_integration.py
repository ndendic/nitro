"""
Sanic framework integration for nitro.sessions.

Provides one-line session setup for Sanic applications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import SessionInterface
from .cookie_store import CookieSessionStore
from .middleware import SessionConfig, SessionMiddleware

if TYPE_CHECKING:
    pass

try:
    from sanic import Sanic, Request

    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False


def sanic_sessions(
    app: "Sanic",
    store: SessionInterface,
    secret: str | None = None,
    config: SessionConfig | None = None,
    **cookie_kwargs: Any,
) -> SessionMiddleware:
    """Attach session middleware to a Sanic application.

    Registers ``on_request`` and ``on_response`` listeners that
    automatically load and save sessions via cookies.

    The session is accessible as ``request.ctx.session`` in handlers.

    Args:
        app: The Sanic application instance.
        store: A session backend (MemorySessionStore, CookieSessionStore, etc.).
        secret: Secret key (required for CookieSessionStore if not set at init).
        config: Optional SessionConfig for cookie behavior.
        **cookie_kwargs: Overrides for SessionConfig fields
            (e.g., cookie_name="sid", cookie_secure=True).

    Returns:
        The configured SessionMiddleware instance.

    Raises:
        ImportError: If Sanic is not installed.

    Example::

        from sanic import Sanic
        from nitro.sessions import MemorySessionStore, sanic_sessions

        app = Sanic("MyApp")
        store = MemorySessionStore(ttl=3600)
        sanic_sessions(app, store, secret="change-me")

        @app.get("/")
        async def index(request):
            session = request.ctx.session
            session["views"] = session.get("views", 0) + 1
            return text(f"Views: {session['views']}")
    """
    if not SANIC_AVAILABLE:
        raise ImportError("Sanic is required. Install with: pip install sanic")

    # Build config from defaults + overrides
    if config is None:
        config = SessionConfig(**cookie_kwargs)
    elif cookie_kwargs:
        for key, value in cookie_kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    mw = SessionMiddleware(store, config)

    @app.on_request
    async def session_load(request: Request):
        cookie_value = request.cookies.get(config.cookie_name)
        session = await mw.load_session(cookie_value)
        request.ctx.session = session

    @app.on_response
    async def session_save(request: Request, response):
        session = getattr(request.ctx, "session", None)
        if session is None:
            return response

        cookie_value = await mw.save_session(session)

        if cookie_value is None:
            # No changes
            return response

        if cookie_value == "":
            # Session invalidated — delete the cookie
            response.cookies.delete_cookie(
                config.cookie_name,
                path=config.cookie_path,
                domain=config.cookie_domain,
            )
        else:
            # Set/update cookie
            attrs = mw.build_cookie_attrs()
            response.cookies.add_cookie(
                config.cookie_name,
                cookie_value,
                **attrs,
            )

        return response

    return mw
