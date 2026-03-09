"""
Sanic adapter for the event-driven action system.

Registers 5 catch-all endpoints that dispatch to Blinker events.
"""
try:
    from sanic import Sanic, Request
    from sanic.response import json as sanic_json
    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False

from .catch_all import dispatch_action
from ..routing.registration import NotFoundError


def configure_nitro(app, prefix: str = ""):
    """
    Register catch-all endpoints on a Sanic app.

    This is the only setup needed. Entity actions are registered
    via __init_subclass__, standalone actions at decoration time.

    Args:
        app: Sanic application instance
        prefix: Optional URL prefix (e.g., "/api")
    """
    if not SANIC_AVAILABLE:
        raise ImportError("Sanic is required. Install with: pip install sanic")

    methods = ["get", "post", "put", "delete", "patch"]

    for method in methods:
        _register_catch_all(app, method, prefix)


def _register_catch_all(app, method: str, prefix: str):
    """Register a single catch-all endpoint for an HTTP method."""
    path = f"{prefix}/{method}/<action:path>"

    async def handler(request: Request, action: str):
        try:
            # Extract signals from request
            signals = await _extract_signals(request)

            # Sender from cookie or header — not from URL
            sender = (
                request.cookies.get("user_id")
                or request.headers.get("x-client-id")
                or "anonymous"
            )

            result = await dispatch_action(
                action_str=action,
                sender=sender,
                signals=signals,
                request=request,
            )

            if result is None:
                return sanic_json({"status": "ok"}, status=200)
            elif isinstance(result, dict):
                return sanic_json(result, status=200)
            else:
                return sanic_json({"result": result}, status=200)

        except NotFoundError as e:
            return sanic_json({"error": str(e)}, status=404)
        except TypeError as e:
            return sanic_json({"error": f"Invalid parameters: {e}"}, status=422)
        except ValueError as e:
            return sanic_json({"error": str(e)}, status=400)
        except Exception as e:
            return sanic_json({"error": f"Internal error: {e}"}, status=500)

    handler.__name__ = f"catch_all_{method}"
    app.add_route(handler, path, methods=[method.upper()])


async def _extract_signals(request: Request) -> dict:
    """Extract signal values from a Sanic request."""
    signals = {}

    # Query params
    if request.args:
        for key, values in request.args.items():
            signals[key] = values[0] if len(values) == 1 else values

    # Body params (for POST/PUT/PATCH)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            if request.json:
                signals.update(request.json)
        except Exception:
            pass

    return signals
