"""
Flask adapter for the event-driven action system.

Registers 5 catch-all endpoints that dispatch to Blinker events.
"""
import asyncio

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from .catch_all import dispatch_action
from ..routing.registration import NotFoundError


def configure_nitro(app, prefix: str = ""):
    """
    Register catch-all endpoints on a Flask app.

    This is the only setup needed. Entity actions are registered
    via __init_subclass__, standalone actions at decoration time.

    Args:
        app: Flask application instance
        prefix: Optional URL prefix (e.g., "/api")
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required. Install with: pip install flask")

    methods = ["get", "post", "put", "delete", "patch"]

    for method in methods:
        _register_catch_all(app, method, prefix)


def _register_catch_all(app, method: str, prefix: str):
    """Register a single catch-all endpoint for an HTTP method."""
    path = f"{prefix}/{method}/<path:action>"

    def handler(action: str):
        try:
            # Extract signals from request
            signals = _extract_signals()

            # Sender from cookie or header — not from URL
            sender = (
                request.cookies.get("user_id")
                or request.headers.get("x-client-id")
                or "anonymous"
            )

            # Run async dispatch_action from sync Flask context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        dispatch_action(
                            action_str=action,
                            sender=sender,
                            signals=signals,
                            request=request,
                        ),
                    ).result()
            else:
                result = asyncio.run(
                    dispatch_action(
                        action_str=action,
                        sender=sender,
                        signals=signals,
                        request=request,
                    )
                )

            if result is None:
                return jsonify({"status": "ok"}), 200
            elif isinstance(result, dict):
                return jsonify(result), 200
            else:
                return jsonify({"result": result}), 200

        except NotFoundError as e:
            return jsonify({"error": str(e)}), 404
        except TypeError as e:
            return jsonify({"error": f"Invalid parameters: {e}"}), 422
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Internal error: {e}"}), 500

    handler.__name__ = f"catch_all_{method}"
    app.add_url_rule(path, endpoint=f"catch_all_{method}", view_func=handler, methods=[method.upper()])


def _extract_signals() -> dict:
    """Extract signal values from a Flask request."""
    signals = {}

    # Query params
    if request.args:
        for key in request.args:
            values = request.args.getlist(key)
            signals[key] = values[0] if len(values) == 1 else values

    # Body params (for POST/PUT/PATCH)
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = request.get_json(silent=True)
            if body:
                signals.update(body)
        except Exception:
            pass

    return signals
