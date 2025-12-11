"""
Flask Adapter - Auto-routing integration for Flask

This module provides the FlaskDispatcher class which extends NitroDispatcher
to automatically register @action decorated entity methods as Flask routes.

Usage:
    ```python
    from flask import Flask
    from nitro.adapters.flask import configure_nitro
    from nitro import Entity, action

    class Counter(Entity, table=True):
        count: int = 0

        @action()
        def increment(self, amount: int = 1):
            self.count += amount
            self.save()
            return {"count": self.count}

    app = Flask(__name__)
    configure_nitro(app)  # Auto-registers all routes
    ```

Generated routes:
    - POST /counter/{id}/increment?amount=1
    - Automatic 404 for missing entities
    - Automatic 422 for validation errors
"""

from typing import Type, List, Optional, Dict, Any, Callable
from flask import Flask, request, jsonify
from inspect import signature, iscoroutinefunction
import asyncio

from ..infrastructure.routing import NitroDispatcher, ActionMetadata
from ..domain.entities.base_entity import Entity


class FlaskDispatcher(NitroDispatcher):
    """
    Flask-specific dispatcher for auto-routing.

    Extends NitroDispatcher to integrate with Flask's routing system.

    Features:
    - Automatic route registration
    - Path/query/body parameter extraction
    - Async/sync method support
    - Error handling (404, 422, 500)
    """

    def __init__(self, app: Flask, prefix: str = ""):
        """
        Initialize Flask dispatcher.

        Args:
            app: Flask application instance
            prefix: URL prefix for all routes (e.g., "/api/v1")
        """
        super().__init__(prefix)
        self.app = app

    def register_route(
        self,
        entity_class: Type[Entity],
        method: Callable,
        metadata: ActionMetadata,
        entity_route_name: Optional[str] = None
    ) -> None:
        """
        Register a single route with Flask.

        Args:
            entity_class: The Entity class containing the method
            method: The @action decorated method
            metadata: Routing metadata from @action decorator
            entity_route_name: Custom entity route name from __route_name__ attribute
        """
        # Generate URL path (Flask uses <id> not {id})
        url_path = metadata.generate_url_path(self.prefix, entity_route_name)
        flask_url_path = url_path.replace("{id}", "<id>")

        # Create route handler
        def route_handler(id=None):
            """Flask route handler."""
            try:
                # Extract parameters from Flask request
                params = self._extract_flask_parameters(
                    request,
                    method,
                    metadata,
                    id
                )

                # Dispatch to entity method (handle both sync and async)
                if metadata.is_async:
                    # Run async method in event loop
                    result = asyncio.run(
                        self.dispatch(entity_class, method, metadata, params)
                    )
                else:
                    # Sync dispatch - need to create coroutine and run it
                    result = asyncio.run(
                        self.dispatch(entity_class, method, metadata, params)
                    )

                # Check if result is an error
                if isinstance(result, dict) and "error" in result:
                    error_status = result["error"].get("status_code", 500)
                    return jsonify(result), error_status

                # Format response
                response_data = self.format_response(result, metadata)
                return jsonify(response_data), metadata.status_code

            except ValueError as e:
                # 422 Unprocessable Entity (validation error)
                error = self.format_error(422, str(e), "ValidationError")
                return jsonify(error), 422
            except Exception as e:
                # 500 Internal Server Error
                error = self.format_error(500, str(e), "InternalServerError")
                return jsonify(error), 500

        # Create unique endpoint name (Flask requires unique names)
        endpoint_name = f"{entity_class.__name__}_{metadata.function_name}"

        # Register with Flask
        self.app.add_url_rule(
            flask_url_path,
            endpoint=endpoint_name,
            view_func=route_handler,
            methods=[metadata.method]
        )

    def _extract_flask_parameters(
        self,
        request,
        method: Callable,
        metadata: ActionMetadata,
        path_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from Flask request.

        Extraction order:
        1. Path parameters (id)
        2. Query parameters
        3. JSON body (overrides query)

        Args:
            request: Flask request object
            method: The action method to extract parameters for
            metadata: Action metadata with parameter definitions
            path_id: Entity ID from path parameter

        Returns:
            Dictionary in the format expected by base dispatcher
        """
        # Build request_data structure for base dispatcher
        request_data = {
            "path": {"id": path_id} if path_id else {},
            "query": dict(request.args),
            "body": {}
        }

        # Add body params if available
        if request.method in ["POST", "PUT", "PATCH"]:
            if request.is_json:
                try:
                    body = request.get_json()
                    if isinstance(body, dict):
                        request_data["body"] = body
                except Exception:
                    pass  # Empty or invalid JSON

        # Use base dispatcher's parameter extraction
        return request_data

    def register_all_routes(self) -> None:
        """
        Register all discovered routes with Flask.

        Called by configure() after entity discovery.
        """
        for entity_class, actions in self.routes.items():
            for method_name, (method, metadata) in actions.items():
                self.register_route(entity_class, method, metadata)


def configure_nitro(
    app: Flask,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FlaskDispatcher:
    """
    Configure Nitro auto-routing for Flask application.

    This is the main entry point for integrating Nitro with Flask.
    It discovers all Entity subclasses with @action methods and
    automatically registers them as Flask routes.

    Args:
        app: Flask application instance
        entities: Optional list of specific entities to register
                 (None = auto-discover all)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Whether to auto-discover all Entity subclasses
                      (default: True)

    Returns:
        Configured FlaskDispatcher instance

    Example:
        ```python
        from flask import Flask
        from nitro.adapters.flask import configure_nitro

        app = Flask(__name__)
        configure_nitro(app)  # Auto-discovers and registers all entities
        ```
    """
    from ..domain.entities.base_entity import Entity as DefaultEntity

    # Create dispatcher
    dispatcher = FlaskDispatcher(app, prefix)

    # Configure with entities
    dispatcher.configure(
        entity_base_class=DefaultEntity,
        entities=entities,
        auto_discover=auto_discover
    )

    return dispatcher
