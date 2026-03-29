"""
Starlette adapter for the event-driven action system.

Registers 5 catch-all endpoints that dispatch to Blinker events.
"""
try:
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False

from .catch_all import dispatch_action
from ..routing.registration import NotFoundError


def configure_nitro(app, prefix: str = ""):
    """
    Register catch-all endpoints on a Starlette app.

    This is the only setup needed. Entity actions are registered
    via __init_subclass__, standalone actions at decoration time.

    Args:
        app: Starlette application instance
        prefix: Optional URL prefix (e.g., "/api")
    """
    if not STARLETTE_AVAILABLE:
        raise ImportError("Starlette is required. Install with: pip install starlette")

    methods = ["get", "post", "put", "delete", "patch"]

    for method in methods:
        _register_catch_all(app, method, prefix)


def _register_catch_all(app, method: str, prefix: str):
    """Register a single catch-all endpoint for an HTTP method."""
    path = f"{prefix}/{method}/{{action:path}}"

    async def handler(request: Request) -> JSONResponse:
        try:
            action = request.path_params["action"]

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
                return JSONResponse({"status": "ok"}, status_code=200)
            elif isinstance(result, dict):
                return JSONResponse(result, status_code=200)
            else:
                return JSONResponse({"result": result}, status_code=200)

        except NotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)
        except TypeError as e:
            return JSONResponse({"error": f"Invalid parameters: {e}"}, status_code=422)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return JSONResponse({"error": f"Internal error: {e}"}, status_code=500)

    handler.__name__ = f"catch_all_{method}"
    app.routes.append(Route(path, handler, methods=[method.upper()]))


async def _extract_signals(request: Request) -> dict:
    """Extract signal values from a Starlette request."""
    signals = {}

    # Query params
    if request.query_params:
        for key in request.query_params:
            values = request.query_params.getlist(key)
            signals[key] = values[0] if len(values) == 1 else values

    # Body params (for POST/PUT/PATCH)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
            if body:
                signals.update(body)
        except Exception:
            pass

    return signals
