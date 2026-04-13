"""
nitro.sessions — Framework-agnostic server-side session management.

Provides:
- SessionInterface     : Abstract base for session backends
- MemorySessionStore   : In-process dict-based sessions with TTL
- CookieSessionStore   : Signed cookie-based sessions (no server storage)
- SessionMiddleware    : Middleware for auto-loading/saving sessions via cookies
- Flash                : Flash message helpers (one-time messages across requests)

Optional backends (requires extra dependencies):
- RedisSessionStore    : Redis-backed distributed sessions (pip install redis)

Sanic integration:
- sanic_sessions       : One-line setup for Sanic apps

Quick start::

    from nitro.sessions import MemorySessionStore, SessionMiddleware, sanic_sessions

    store = MemorySessionStore(ttl=3600)
    sanic_sessions(app, store, secret="change-me")

    # In handlers:
    async def index(request):
        session = request.ctx.session
        session["visits"] = session.get("visits", 0) + 1

        # Flash messages
        session.flash("Welcome back!", "success")
        messages = session.pop_flashes()

Cookie-based (no server storage)::

    from nitro.sessions import CookieSessionStore

    store = CookieSessionStore(secret="change-me", max_age=3600)
    sanic_sessions(app, store)

Redis backend::

    from nitro.sessions.redis_store import RedisSessionStore

    store = RedisSessionStore(url="redis://localhost:6379/0", ttl=3600)
    sanic_sessions(app, store, secret="change-me")
"""

from .base import SessionInterface, SessionData
from .memory_store import MemorySessionStore
from .cookie_store import CookieSessionStore
from .middleware import SessionMiddleware
from .sanic_integration import sanic_sessions

__all__ = [
    "SessionInterface",
    "SessionData",
    "MemorySessionStore",
    "CookieSessionStore",
    "SessionMiddleware",
    "sanic_sessions",
]

# RedisSessionStore is imported lazily to avoid hard dependency on the redis package.
# Import it explicitly when needed:
#
#   from nitro.sessions.redis_store import RedisSessionStore
