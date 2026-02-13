"""
Sanic Adapter - Auto-routing integration for Sanic

This module provides the SanicDispatcher class which extends NitroDispatcher
to automatically register @action decorated entity methods as Sanic routes.

DRAFT - Created by Arty for Nikola's review (2026-02-07)
NOT YET TESTED - Needs review before use

Usage:
    ```python
    from sanic import Sanic
    from nitro.adapters.sanic_adapter import configure_nitro
    from nitro import Entity, action

    class Counter(Entity, table=True):
        count: int = 0

        @action()
        async def increment(self, amount: int = 1):
            self.count += amount
            self.save()
            return {"count": self.count}

    app = Sanic("MyApp")
    configure_nitro(app)  # Auto-registers all routes
    ```

Generated routes:
    - POST /counter/<id>/increment?amount=1
    - Automatic 404 for missing entities
    - Automatic 422 for validation errors
"""

from typing import Type, List, Optional, Dict, Any, Callable
from inspect import signature, iscoroutinefunction
import asyncio

try:
    from sanic import Sanic
    from sanic.request import Request
    from sanic.response import json as sanic_json, JSONResponse
    from sanic.exceptions import NotFound, InvalidUsage, SanicException
    SANIC_AVAILABLE = True
except ImportError:
    SANIC_AVAILABLE = False
    Sanic = None
    Request = None

from ..routing import NitroDispatcher, ActionMetadata
from ..domain.entities.base_entity import Entity


class SanicDispatcher(NitroDispatcher):
    """
    Sanic-specific dispatcher for auto-routing.

    Extends NitroDispatcher to integrate with Sanic's routing system.

    Features:
    - Automatic route registration
    - Path/query/body parameter extraction
    - Async method support (Sanic is async-first)
    - Error handling (404, 422, 500)
    """

    def __init__(self, app: "Sanic", prefix: str = ""):
        """
        Initialize Sanic dispatcher.

        Args:
            app: Sanic application instance
            prefix: URL prefix for all routes (e.g., "/api/v1")
        """
        if not SANIC_AVAILABLE:
            raise ImportError(
                "Sanic is not installed. Install with: pip install sanic"
            )
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
        Register a single route with Sanic.

        Args:
            entity_class: The Entity class containing the method
            method: The @action decorated method
            metadata: Routing metadata from @action decorator
            entity_route_name: Custom entity route name from __route_name__ attribute
        """
        # Generate URL path - convert {id} to <id> for Sanic
        url_path = metadata.generate_url_path(self.prefix, entity_route_name)
        sanic_path = url_path.replace("{id}", "<id>")

        # Check if method requires entity ID in path
        has_id_param = "<id>" in sanic_path

        # Create route handler
        async def route_handler(request: Request, id: str = None):
            """Sanic route handler."""
            try:
                # Extract parameters from request
                params = await self._extract_sanic_parameters(
                    request,
                    method,
                    metadata,
                    id
                )

                # Dispatch to entity method
                result = await self.dispatch(entity_class, method, metadata, params)

                # Check if result is an error (contains "error" key with "status_code")
                if isinstance(result, dict) and "error" in result:
                    error_status = result["error"].get("status_code", 500)
                    return sanic_json(result, status=error_status)

                # Format response
                response_data = self.format_response(result, metadata)

                return sanic_json(response_data, status=metadata.status_code)

            except InvalidUsage as e:
                # 422 Unprocessable Entity (validation error)
                error = self.format_error(422, str(e), "ValidationError")
                return sanic_json(error, status=422)
            except NotFound as e:
                # 404 Not Found
                error = self.format_error(404, str(e), "NotFound")
                return sanic_json(error, status=404)
            except SanicException:
                # Re-raise Sanic exceptions
                raise
            except ValueError as e:
                # 422 Validation error
                error = self.format_error(422, str(e), "ValidationError")
                return sanic_json(error, status=422)
            except Exception as e:
                # 500 Internal Server Error
                error = self.format_error(500, str(e), "InternalServerError")
                return sanic_json(error, status=500)

        # Set handler name for Sanic (must be unique)
        handler_name = f"{entity_class.__name__}_{metadata.function_name}"
        route_handler.__name__ = handler_name

        # Register with Sanic
        # Note: Sanic uses lowercase method names
        http_method = metadata.method.lower()
        
        self.app.add_route(
            handler=route_handler,
            uri=sanic_path,
            methods=[metadata.method],  # Sanic accepts uppercase
            name=handler_name
        )

    async def _extract_sanic_parameters(
        self,
        request: Request,
        method: Callable,
        metadata: ActionMetadata,
        path_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from Sanic request.

        Extraction order:
        1. Path parameters (id)
        2. Query parameters
        3. JSON body (overrides query)

        Args:
            request: Sanic Request object
            method: The action method to extract parameters for
            metadata: Action metadata with parameter definitions
            path_id: Entity ID from path parameter

        Returns:
            Dictionary in the format expected by base dispatcher
        """
        # Build request_data structure for base dispatcher
        request_data = {
            "path": {"id": path_id} if path_id else {},
            "query": dict(request.args),  # Sanic uses .args for query params
            "body": {}
        }

        # Flatten query params (Sanic returns lists)
        for key, value in request_data["query"].items():
            if isinstance(value, list) and len(value) == 1:
                request_data["query"][key] = value[0]

        # Add body params if available
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.content_type or ""
            if "application/json" in content_type:
                try:
                    body = request.json
                    if isinstance(body, dict):
                        request_data["body"] = body
                except Exception:
                    pass  # Empty or invalid JSON

        # Use base dispatcher's parameter extraction
        return request_data

    def register_all_routes(self) -> None:
        """
        Register all discovered routes with Sanic.

        Called by configure() after entity discovery.
        """
        for entity_class, actions in self.routes.items():
            for method_name, (method, metadata) in actions.items():
                self.register_route(entity_class, method, metadata)


def configure_nitro(
    app: "Sanic",
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> SanicDispatcher:
    """
    Configure Nitro auto-routing for Sanic application.

    This is the main entry point for integrating Nitro with Sanic.
    It discovers all Entity subclasses with @action methods and
    automatically registers them as Sanic routes.

    Args:
        app: Sanic application instance
        entities: Optional list of specific entities to register
                 (None = auto-discover all)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Whether to auto-discover all Entity subclasses
                      (default: True)

    Returns:
        Configured SanicDispatcher instance

    Example:
        ```python
        from sanic import Sanic
        from nitro.adapters.sanic_adapter import configure_nitro

        app = Sanic("MyApp")
        configure_nitro(app)  # Auto-discovers and registers all entities
        ```

    Example with explicit entities:
        ```python
        configure_nitro(
            app,
            entities=[Counter, Product, Order],
            prefix="/api/v1"
        )
        ```

    Raises:
        ValueError: If URL conflicts are detected between routes
        ImportError: If Sanic is not installed
    """
    if not SANIC_AVAILABLE:
        raise ImportError(
            "Sanic is not installed. Install with: pip install sanic"
        )

    # Create dispatcher
    dispatcher = SanicDispatcher(app, prefix=prefix)

    # Configure with Entity base class
    dispatcher.configure(
        entity_base_class=Entity,
        entities=entities,
        auto_discover=auto_discover
    )

    # Register all routes
    dispatcher.register_all_routes()

    return dispatcher
