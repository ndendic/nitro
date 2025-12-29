"""
FastAPI Adapter - Auto-routing integration for FastAPI

This module provides the FastAPIDispatcher class which extends NitroDispatcher
to automatically register @action decorated entity methods as FastAPI routes.

Usage:
    ```python
    from fastapi import FastAPI
    from nitro.adapters.fastapi import configure_nitro
    from nitro import Entity, action

    class Counter(Entity, table=True):
        count: int = 0

        @action()
        async def increment(self, amount: int = 1):
            self.count += amount
            self.save()
            return {"count": self.count}

    app = FastAPI()
    configure_nitro(app)  # Auto-registers all routes
    ```

Generated routes:
    - POST /counter/{id}/increment?amount=1
    - Automatic 404 for missing entities
    - Automatic 422 for validation errors
    - OpenAPI documentation
"""

from typing import Type, List, Optional, Dict, Any, Callable
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from inspect import signature, iscoroutinefunction
import asyncio

from ..infrastructure.routing import NitroDispatcher, ActionMetadata
from ..domain.entities.base_entity import Entity


class FastAPIDispatcher(NitroDispatcher):
    """
    FastAPI-specific dispatcher for auto-routing.

    Extends NitroDispatcher to integrate with FastAPI's routing system,
    dependency injection, and OpenAPI documentation generation.

    Features:
    - Automatic route registration
    - Path/query/body parameter extraction
    - OpenAPI schema generation
    - Async/sync method support
    - Error handling (404, 422, 500)
    """

    def __init__(self, app: FastAPI, prefix: str = ""):
        """
        Initialize FastAPI dispatcher.

        Args:
            app: FastAPI application instance
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
        Register a single route with FastAPI.

        Args:
            entity_class: The Entity class containing the method
            method: The @action decorated method
            metadata: Routing metadata from @action decorator
            entity_route_name: Custom entity route name from __route_name__ attribute
        """
        # Generate URL path
        url_path = metadata.generate_url_path(self.prefix, entity_route_name)

        # Check if method requires entity ID in path
        has_id_param = "{id}" in url_path

        # Create route handler
        async def route_handler(
            request: Request,
            id: Optional[str] = None  # Path parameter
        ):
            """FastAPI route handler."""
            try:
                # Extract parameters from request
                params = await self._extract_fastapi_parameters(
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
                    return JSONResponse(
                        content=result,
                        status_code=error_status
                    )

                # Format response
                response_data = self.format_response(result, metadata)

                return JSONResponse(
                    content=response_data,
                    status_code=metadata.status_code
                )

            except ValueError as e:
                # 422 Unprocessable Entity (validation error)
                error = self.format_error(422, str(e), "ValidationError")
                return JSONResponse(
                    content=error,
                    status_code=422
                )
            except HTTPException:
                # Re-raise FastAPI exceptions
                raise
            except Exception as e:
                # 500 Internal Server Error
                error = self.format_error(500, str(e), "InternalServerError")
                return JSONResponse(
                    content=error,
                    status_code=500
                )

        # Configure OpenAPI metadata
        operation_kwargs = {
            "path": url_path,
            "methods": [metadata.method],
            "summary": metadata.summary or f"{metadata.function_name}",
            "description": metadata.description or method.__doc__,
            "tags": metadata.tags or [entity_class.__name__],
            "status_code": metadata.status_code,
            "response_class": JSONResponse,
        }

        # Add response model if specified
        if metadata.response_model:
            operation_kwargs["response_model"] = metadata.response_model

        # Register with FastAPI
        self.app.add_api_route(
            endpoint=route_handler,
            **operation_kwargs
        )

    async def _extract_fastapi_parameters(
        self,
        request: Request,
        method: Callable,
        metadata: ActionMetadata,
        path_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract parameters from FastAPI request.

        Extraction order:
        1. Path parameters (id)
        2. Query parameters
        3. JSON body (overrides query)

        Args:
            request: FastAPI Request object
            method: The action method to extract parameters for
            metadata: Action metadata with parameter definitions
            path_id: Entity ID from path parameter

        Returns:
            Dictionary in the format expected by base dispatcher
        """
        # Build request_data structure for base dispatcher
        request_data = {
            "path": {"id": path_id} if path_id else {},
            "query": dict(request.query_params),
            "body": {}
        }

        # Add body params if available
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    body = await request.json()
                    if isinstance(body, dict):
                        request_data["body"] = body
                except Exception:
                    pass  # Empty or invalid JSON

        # Use base dispatcher's parameter extraction
        return request_data

    def register_all_routes(self) -> None:
        """
        Register all discovered routes with FastAPI.

        Called by configure() after entity discovery.
        """
        for entity_class, actions in self.routes.items():
            for method_name, (method, metadata) in actions.items():
                self.register_route(entity_class, method, metadata)


def configure_nitro(
    app: FastAPI,
    entities: Optional[List[Type[Entity]]] = None,
    prefix: str = "",
    auto_discover: bool = True
) -> FastAPIDispatcher:
    """
    Configure Nitro auto-routing for FastAPI application.

    This is the main entry point for integrating Nitro with FastAPI.
    It discovers all Entity subclasses with @action methods and
    automatically registers them as FastAPI routes.

    Args:
        app: FastAPI application instance
        entities: Optional list of specific entities to register
                 (None = auto-discover all)
        prefix: URL prefix for all routes (e.g., "/api/v1")
        auto_discover: Whether to auto-discover all Entity subclasses
                      (default: True)

    Returns:
        Configured FastAPIDispatcher instance

    Example:
        ```python
        from fastapi import FastAPI
        from nitro.adapters.fastapi import configure_nitro

        app = FastAPI(title="My App")
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
    """
    # Create dispatcher
    dispatcher = FastAPIDispatcher(app, prefix=prefix)

    # Configure with Entity base class
    dispatcher.configure(
        entity_base_class=Entity,
        entities=entities,
        auto_discover=auto_discover
    )

    # Register all routes
    dispatcher.register_all_routes()

    return dispatcher
