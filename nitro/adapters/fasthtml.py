"""
FastHTML Adapter - Auto-routing integration for FastHTML

This module provides the FastHTMLDispatcher class which extends NitroDispatcher
to automatically register @action decorated entity methods as FastHTML routes.

Usage:
    ```python
    from fasthtml.common import *
    from nitro.adapters.fasthtml import configure_nitro
    from nitro import Entity, action

    class Counter(Entity, table=True):
        count: int = 0

        @action()
        def increment(self, amount: int = 1):
            self.count += amount
            self.save()
            return {"count": self.count}

    app, rt = fast_app()
    configure_nitro(rt)  # Auto-registers all routes
    ```

Generated routes:
    - POST /counter/{id}/increment?amount=1
    - Automatic 404 for missing entities
    - Automatic 422 for validation errors
"""

from typing import Type, List, Optional, Dict, Any, Callable
from inspect import signature, iscoroutinefunction
import asyncio

from starlette.responses import JSONResponse

from ..infrastructure.routing import NitroDispatcher, ActionMetadata
from ..domain.entities.base_entity import Entity


class FastHTMLDispatcher(NitroDispatcher):
    """
    FastHTML-specific dispatcher for auto-routing.

    Extends NitroDispatcher to integrate with FastHTML's routing system.

    Features:
    - Automatic route registration
    - Path/query/body parameter extraction
    - Async/sync method support
    - Error handling (404, 422, 500)
    """

    def __init__(self, rt: Any, prefix: str = ""):
        """
        Initialize FastHTML dispatcher.

        Args:
            rt: FastHTML route decorator (from fast_app())
            prefix: URL prefix for all routes (e.g., "/api/v1")
        """
        super().__init__(prefix)
        self.rt = rt
        self.app = getattr(rt, 'app', None)  # Get app if available

    def register_route(
        self,
        entity_class: Type[Entity],
        method: Callable,
        metadata: ActionMetadata,
        entity_route_name: Optional[str] = None
    ) -> None:
        """
        Register a single route with FastHTML.

        Args:
            entity_class: The Entity class containing the method
            method: The @action decorated method
            metadata: Routing metadata from @action decorator
            entity_route_name: Custom entity route name from __route_name__ attribute
        """
        # Generate URL path (FastHTML uses {id} notation like FastAPI)
        url_path = metadata.generate_url_path(self.prefix, entity_route_name)

        # Create route handler
        async def route_handler(request, id: str = None):
            """FastHTML route handler."""
            try:
                # Extract parameters from FastHTML request
                params = await self._extract_fasthtml_parameters(
                    request,
                    method,
                    metadata,
                    id
                )

                # Dispatch to entity method
                result = await self.dispatch(entity_class, method, metadata, params)

                # Check if result is an error
                if isinstance(result, dict) and "error" in result:
                    error_status = result["error"].get("status_code", 500)
                    # Return JSON response for API endpoints
                    return JSONResponse(content=result, status_code=error_status)

                # Format response
                response_data = self.format_response(result, metadata)
                return JSONResponse(content=response_data, status_code=metadata.status_code)

            except ValueError as e:
                # 422 Unprocessable Entity (validation error)
                error = self.format_error(422, str(e), "ValidationError")
                return JSONResponse(content=error, status_code=422)
            except Exception as e:
                # 500 Internal Server Error
                error = self.format_error(500, str(e), "InternalServerError")
                return JSONResponse(content=error, status_code=500)

        # Determine HTTP methods for FastHTML
        http_method = metadata.method.upper()

        # Register with FastHTML using the route decorator
        # FastHTML's rt() decorator syntax: @rt("/path", methods=["GET"])
        if http_method == "GET":
            self.rt(url_path)(route_handler)
        else:
            # For POST, PUT, DELETE, etc.
            self.rt(url_path, methods=[http_method])(route_handler)

    async def _extract_fasthtml_parameters(
        self,
        request,
        method: Callable,
        metadata: ActionMetadata,
        path_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from FastHTML request.

        Extraction order:
        1. Path parameters (id)
        2. Query parameters
        3. Form/JSON body (overrides query)

        Args:
            request: FastHTML request object
            method: The action method to extract parameters for
            metadata: Action metadata with parameter definitions
            path_id: Entity ID from path parameter

        Returns:
            Dictionary in the format expected by base dispatcher
        """
        # Build request_data structure for base dispatcher
        request_data = {
            "path": {"id": path_id} if path_id else {},
            "query": {},
            "body": {}
        }

        # Extract query parameters
        if hasattr(request, 'query_params'):
            request_data["query"] = dict(request.query_params)
        elif hasattr(request, 'args'):
            request_data["query"] = dict(request.args)

        # Extract body parameters (for POST/PUT/PATCH)
        http_method = getattr(request, 'method', 'GET').upper()
        if http_method in ["POST", "PUT", "PATCH"]:
            # Try JSON first
            if hasattr(request, 'json'):
                try:
                    body = await request.json() if iscoroutinefunction(request.json) else request.json()
                    if isinstance(body, dict):
                        request_data["body"] = body
                except:
                    pass

            # Try form data
            if not request_data["body"] and hasattr(request, 'form'):
                try:
                    form = await request.form() if iscoroutinefunction(request.form) else request.form()
                    if isinstance(form, dict):
                        request_data["body"] = dict(form)
                except:
                    pass

        return request_data

    def register_all_routes(self) -> None:
        """
        Register all discovered routes with FastHTML.

        Called by configure() after entity discovery.
        """
        for entity_class, actions in self.routes.items():
            for method_name, (method, metadata) in actions.items():
                self.register_route(entity_class, method, metadata)


def configure_nitro(
    rt: Any,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FastHTMLDispatcher:
    """
    Configure Nitro auto-routing for FastHTML application.

    This is the main entry point for integrating Nitro with FastHTML.
    It discovers all Entity subclasses with @action methods and
    automatically registers them as FastHTML routes.

    Args:
        rt: FastHTML route decorator (from fast_app())
        entities: Optional list of specific entities to register
                 (None = auto-discover all)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Whether to auto-discover all Entity subclasses
                      (default: True)

    Returns:
        Configured FastHTMLDispatcher instance

    Example:
        ```python
        from fasthtml.common import *
        from nitro.adapters.fasthtml import configure_nitro

        app, rt = fast_app()
        configure_nitro(rt)  # Auto-discovers and registers all entities
        ```
    """
    from ..domain.entities.base_entity import Entity as DefaultEntity

    # Create dispatcher
    dispatcher = FastHTMLDispatcher(rt, prefix)

    # Configure with entities
    dispatcher.configure(
        entity_base_class=DefaultEntity,
        entities=entities,
        auto_discover=auto_discover
    )

    return dispatcher
