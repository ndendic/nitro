"""
nitro.middleware — Framework-agnostic middleware pipeline for the Nitro framework.

Provides:
- MiddlewareInterface : Abstract base for middleware components
- Pipeline            : Composable middleware chain with before/after hooks
- CORSMiddleware      : Cross-origin resource sharing headers
- SecurityMiddleware  : Security headers (CSP, HSTS, X-Frame-Options, etc.)
- LoggingMiddleware   : Structured request/response logging
- TimingMiddleware    : Request duration tracking with configurable thresholds

Sanic integration:
- sanic_middleware     : Apply a Pipeline to a Sanic app as request/response middleware

Quick start::

    from nitro.middleware import Pipeline, CORSMiddleware, SecurityMiddleware

    pipeline = Pipeline(
        CORSMiddleware(allow_origins=["https://example.com"]),
        SecurityMiddleware(),
    )

    # With Sanic
    from nitro.middleware import sanic_middleware
    sanic_middleware(app, pipeline)

Standalone usage::

    pipeline = Pipeline(CORSMiddleware(), TimingMiddleware())

    # Manual invocation (framework-agnostic)
    ctx = pipeline.before(request_dict)
    # ... handler runs ...
    ctx = pipeline.after(ctx, response_dict)
"""

from .base import MiddlewareInterface, MiddlewareContext
from .pipeline import Pipeline
from .cors import CORSMiddleware
from .security import SecurityMiddleware
from .logging_mw import LoggingMiddleware
from .timing import TimingMiddleware
from .sanic_integration import sanic_middleware

__all__ = [
    "MiddlewareInterface",
    "MiddlewareContext",
    "Pipeline",
    "CORSMiddleware",
    "SecurityMiddleware",
    "LoggingMiddleware",
    "TimingMiddleware",
    "sanic_middleware",
]
