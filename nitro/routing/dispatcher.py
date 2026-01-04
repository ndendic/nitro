"""
Nitro Dispatcher - Framework-agnostic base class for auto-routing

This module provides the NitroDispatcher base class that framework adapters
(FastAPI, Flask, FastHTML, etc.) can extend to implement auto-routing.
"""

from typing import Type, List, Dict, Any, Optional, Callable, Tuple
from abc import ABC, abstractmethod
import json
from inspect import signature, Parameter

from .metadata import ActionMetadata, get_action_metadata
from .discovery import (
    discover_entity_subclasses,
    discover_action_methods,
    discover_all_routes,
    validate_action_uniqueness,
)


class NitroDispatcher(ABC):
    """
    Base dispatcher for framework-agnostic auto-routing.

    This abstract base class provides common routing logic that can be
    extended by framework-specific adapters (FastAPI, Flask, etc.).

    The dispatcher:
    1. Discovers entities and their @action methods
    2. Generates URL patterns
    3. Extracts and validates parameters
    4. Formats responses
    5. Handles errors consistently

    Framework adapters only need to:
    - Implement register_route() for their specific framework
    - Optionally override extract_parameters() for framework-specific features

    Example:
        ```python
        class FastAPIDispatcher(NitroDispatcher):
            def __init__(self, app: FastAPI, prefix: str = ""):
                super().__init__(prefix)
                self.app = app

            def register_route(self, entity_class, method, metadata):
                # FastAPI-specific route registration
                @self.app.api_route(
                    metadata.generate_url_path(self.prefix),
                    methods=[metadata.method]
                )
                async def handler(**kwargs):
                    return await self.dispatch(entity_class, method, kwargs)
        ```
    """

    def __init__(self, prefix: str = ""):
        """
        Initialize the dispatcher.

        Args:
            prefix: URL prefix for all routes (e.g., "/api/v1")
        """
        self.prefix = prefix
        self.routes: Dict[Type, Dict[str, Tuple[Callable, ActionMetadata]]] = {}
        self.entity_base_class: Optional[Type] = None

    def configure(
        self,
        entity_base_class: Type,
        entities: Optional[List[Type]] = None,
        auto_discover: bool = True,
    ) -> None:
        """
        Configure the dispatcher with entities to route.

        Args:
            entity_base_class: Base Entity class (for auto-discovery)
            entities: Optional list of specific entities to register
            auto_discover: Whether to auto-discover all Entity subclasses

        Raises:
            ValueError: If URL conflicts are detected
        """
        self.entity_base_class = entity_base_class

        # Discover routes
        if auto_discover:
            self.routes = discover_all_routes(entity_base_class, entities)
        elif entities:
            # Manual entity list
            for entity_class in entities:
                actions = discover_action_methods(entity_class)
                if actions:
                    self.routes[entity_class] = actions

        # Validate no URL conflicts
        errors = validate_action_uniqueness(self.routes, self.prefix)
        if errors:
            raise ValueError(
                f"URL conflicts detected:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        # Register routes with the framework
        self._register_all_routes()

    def _register_all_routes(self) -> None:
        """Register all discovered routes with the framework."""
        for entity_class, actions in self.routes.items():
            # Check for custom entity route name
            entity_route_name = getattr(entity_class, '__route_name__', None)

            for method_name, (method, metadata) in actions.items():
                self.register_route(entity_class, method, metadata, entity_route_name)

    @abstractmethod
    def register_route(
        self,
        entity_class: Type,
        method: Callable,
        metadata: ActionMetadata,
        entity_route_name: Optional[str] = None
    ) -> None:
        """
        Register a single route with the framework.

        This is the only method that MUST be implemented by framework adapters.

        Args:
            entity_class: The Entity class
            method: The @action decorated method
            metadata: ActionMetadata with routing information
            entity_route_name: Custom entity route name from __route_name__ attribute

        Example:
            ```python
            def register_route(self, entity_class, method, metadata, entity_route_name=None):
                url = metadata.generate_url_path(self.prefix, entity_route_name)
                self.app.add_route(url, self._create_handler(...))
            ```
        """
        pass

    async def dispatch(
        self,
        entity_class: Type,
        method: Callable,
        metadata: ActionMetadata,
        request_data: Dict[str, Any]
    ) -> Any:
        """
        Dispatch a request to an entity method.

        This is the main entry point for handling requests. It:
        1. Extracts entity ID from path
        2. Loads entity from repository
        3. Extracts method parameters
        4. Calls the method
        5. Formats the response

        Args:
            entity_class: The Entity class
            method: The method to call
            metadata: ActionMetadata for the method
            request_data: Dictionary with path params, query params, body

        Returns:
            Formatted response (format depends on framework)

        Raises:
            EntityNotFoundError: If entity ID not found
            ParameterValidationError: If parameters are invalid
        """
        try:
            # Extract entity ID if required
            entity_id = request_data.get("path", {}).get("id")

            # Load entity if method requires instance
            if "self" in metadata.parameters:
                if not entity_id:
                    return self.format_error(
                        status_code=400,
                        message="Entity ID required in path",
                        error_type="missing_entity_id"
                    )

                # Get entity from repository
                entity = entity_class.get(entity_id)
                if not entity:
                    return self.format_error(
                        status_code=404,
                        message=f"{entity_class.__name__} with id '{entity_id}' not found",
                        error_type="entity_not_found"
                    )

                # Extract method parameters (excluding 'self')
                method_params = self.extract_method_parameters(
                    method,
                    metadata,
                    request_data
                )

                # Call instance method
                if metadata.is_async:
                    result = await method(entity, **method_params)
                else:
                    result = method(entity, **method_params)
            else:
                # Class method - no entity loading needed
                method_params = self.extract_method_parameters(
                    method,
                    metadata,
                    request_data
                )

                # Call class method
                if metadata.is_async:
                    result = await method(**method_params)
                else:
                    result = method(**method_params)

            # Format response
            return self.format_response(result, metadata)

        except TypeError as e:
            # Parameter validation error
            return self.format_error(
                status_code=422,
                message=f"Invalid parameters: {str(e)}",
                error_type="validation_error"
            )
        except Exception as e:
            # Unexpected error
            return self.format_error(
                status_code=500,
                message=f"Internal server error: {str(e)}",
                error_type="internal_error"
            )

    def extract_method_parameters(
        self,
        method: Callable,
        metadata: ActionMetadata,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and validate parameters for a method call.

        Combines path parameters, query parameters, and body parameters
        according to the method signature.

        Args:
            method: The method to extract parameters for
            metadata: ActionMetadata with parameter info
            request_data: Dictionary with 'path', 'query', 'body' keys

        Returns:
            Dictionary of validated parameters ready for method call

        Example:
            >>> request_data = {
            ...     "path": {"id": "counter-1"},
            ...     "query": {"amount": "5"},
            ...     "body": {"notify": True}
            ... }
            >>> params = extract_method_parameters(increment, metadata, request_data)
            >>> params
            {'amount': 5, 'notify': True}
        """
        params = {}

        # Get parameter definitions from metadata
        param_defs = metadata.parameters

        # Extract from path, query, and body
        path_params = request_data.get("path", {})
        query_params = request_data.get("query", {})
        body_params = request_data.get("body", {})

        # Combine all sources (body takes precedence over query)
        all_params = {**query_params, **body_params, **path_params}

        # Validate and convert types for each parameter
        for param_name, param_info in param_defs.items():
            # Skip 'self' parameter
            if param_name == "self":
                continue

            # Check if parameter provided
            if param_name in all_params:
                value = all_params[param_name]

                # Type conversion based on annotation
                annotation = param_info.get("annotation")
                if annotation:
                    try:
                        # Convert string to correct type
                        if annotation == int:
                            value = int(value)
                        elif annotation == float:
                            value = float(value)
                        elif annotation == bool:
                            # Handle bool specially (query params are strings)
                            if isinstance(value, str):
                                value = value.lower() in ("true", "1", "yes")
                        # For other types, trust the input
                    except (ValueError, TypeError) as e:
                        raise TypeError(
                            f"Parameter '{param_name}' must be {annotation.__name__}, "
                            f"got '{value}'"
                        )

                params[param_name] = value

            elif param_info.get("default") is not None:
                # Use default value
                params[param_name] = param_info["default"]
            elif param_info.get("kind") != "KEYWORD_ONLY":
                # Required parameter missing
                raise TypeError(f"Required parameter '{param_name}' is missing")

        return params

    def format_response(self, result: Any, metadata: ActionMetadata) -> Any:
        """
        Format a method's return value as an HTTP response.

        Args:
            result: Return value from the entity method
            metadata: ActionMetadata for the method

        Returns:
            Formatted response (framework-specific)

        Default behavior:
        - None -> {"status": "success"} with status_code from metadata
        - dict -> Return as-is (JSON)
        - Entity -> Serialize via model_dump()
        - List[Entity] -> Serialize each
        - Other -> {"result": value}
        """
        if result is None:
            return {
                "status": "success",
                "message": f"{metadata.function_name} completed"
            }

        if isinstance(result, dict):
            return result

        # Check if result has model_dump (Pydantic model)
        if hasattr(result, "model_dump"):
            return result.model_dump()

        # Check if result is a list of models
        if isinstance(result, list) and len(result) > 0:
            if hasattr(result[0], "model_dump"):
                return [item.model_dump() for item in result]

        # Default: wrap in result object
        return {"result": result}

    def format_error(
        self,
        status_code: int,
        message: str,
        error_type: str,
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Format an error response consistently.

        Args:
            status_code: HTTP status code (404, 422, 500, etc.)
            message: Human-readable error message
            error_type: Error type identifier
            details: Optional additional error details

        Returns:
            Error response dictionary

        Example:
            >>> error = format_error(404, "Counter not found", "entity_not_found")
            >>> error
            {
                "error": {
                    "type": "entity_not_found",
                    "message": "Counter not found",
                    "status_code": 404
                }
            }
        """
        error_response = {
            "error": {
                "type": error_type,
                "message": message,
                "status_code": status_code
            }
        }

        if details:
            error_response["error"]["details"] = details

        return error_response

    def get_routes_summary(self) -> List[Dict[str, Any]]:
        """
        Get a summary of all registered routes.

        Useful for debugging and documentation.

        Returns:
            List of route information dictionaries

        Example:
            >>> dispatcher.configure(Entity)
            >>> summary = dispatcher.get_routes_summary()
            >>> for route in summary:
            ...     print(f"{route['method']} {route['url']}")
            POST /counter/{id}/increment
            GET /counter/{id}/status
        """
        routes_summary = []

        for entity_class, actions in self.routes.items():
            for method_name, (method, metadata) in actions.items():
                routes_summary.append({
                    "entity": entity_class.__name__,
                    "method": metadata.method,
                    "url": metadata.generate_url_path(self.prefix),
                    "function": method_name,
                    "async": metadata.is_async,
                    "summary": metadata.summary,
                })

        return routes_summary


__all__ = ["NitroDispatcher"]
