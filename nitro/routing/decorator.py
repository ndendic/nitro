"""
@action Decorator - Mark entity methods for auto-routing

This module provides the @action decorator for marking entity methods
as HTTP endpoints that should be automatically routed.
"""

from functools import wraps
from typing import Optional, List, Type, Callable, Any
from inspect import iscoroutinefunction

from .metadata import (
    ActionMetadata,
    set_action_metadata,
    extract_parameters,
)


def action(
    method: str = "POST",
    path: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    # Future parameters (Phase 2.2+)
    requires_auth: bool = False,
    rate_limit: Optional[str] = None,
    cache_ttl: Optional[int] = None,
) -> Callable:
    """
    Decorator to mark entity methods for automatic HTTP routing.

    When an entity method is decorated with @action, it becomes an HTTP
    endpoint that is automatically registered when configure_nitro() is called.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH). Default: POST
        path: Custom URL path. If None, auto-generates /{entity}/{id}/{method_name}
        response_model: Pydantic model for response validation (OpenAPI)
        status_code: HTTP status code for successful responses. Default: 200
        tags: List of tags for OpenAPI documentation
        summary: Short description for OpenAPI
        description: Long description for OpenAPI (uses docstring if None)
        requires_auth: Whether authentication is required (Phase 2.2)
        rate_limit: Rate limit specification (Phase 2.3)
        cache_ttl: Cache TTL in seconds for GET requests (Phase 2.4)

    Returns:
        Decorated function with routing metadata attached

    Example:
        ```python
        class Counter(Entity):
            count: int = 0

            @action(method="POST")
            async def increment(self, amount: int = 1):
                '''Increment counter by amount.'''
                self.count += amount
                self.save()
                return {"count": self.count}

            @action(method="GET", summary="Get counter status")
            def status(self) -> dict:
                return {"count": self.count, "id": self.id}
        ```

    Usage:
        1. Decorate entity methods with @action
        2. Call configure_nitro(app) to register routes
        3. Routes auto-generated based on entity/method names
        4. Parameters auto-extracted from type hints

    Generated URLs:
        - Counter.increment() -> POST /counter/{id}/increment
        - Counter.status() -> GET /counter/{id}/status
        - Product.create() -> POST /product/create (class method, no {id})
    """

    def decorator(func: Callable) -> Callable:
        """Inner decorator that processes the function."""

        # Extract function metadata
        function_name = func.__name__
        is_async = iscoroutinefunction(func)
        parameters = extract_parameters(func)

        # Use function docstring as description if not provided
        func_description = description or func.__doc__

        # Create metadata object
        metadata = ActionMetadata(
            method=method,
            path=path,
            status_code=status_code,
            summary=summary or function_name.replace("_", " ").title(),
            description=func_description,
            tags=tags or [],
            response_model=response_model,
            function_name=function_name,
            entity_class_name="",  # Will be set during entity discovery
            is_async=is_async,
            parameters=parameters,
            requires_auth=requires_auth,
            rate_limit=rate_limit,
            cache_ttl=cache_ttl,
        )

        # Attach metadata to function
        set_action_metadata(func, metadata)

        # Return function unchanged (decorator doesn't modify behavior)
        # The function can still be called normally: counter.increment()
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper that preserves original function behavior."""
            return func(*args, **kwargs)

        # Preserve async nature
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                """Async wrapper that preserves original function behavior."""
                return await func(*args, **kwargs)

            # Copy metadata to async wrapper
            set_action_metadata(async_wrapper, metadata)
            return async_wrapper

        # Copy metadata to wrapper
        set_action_metadata(wrapper, metadata)
        return wrapper

    return decorator


# Convenience aliases for common HTTP methods
def get(
    path: Optional[str] = None,
    response_model: Optional[Type] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Convenience decorator for GET requests.

    Equivalent to @action(method="GET", ...)

    Example:
        ```python
        @get(summary="Get counter status")
        def status(self):
            return {"count": self.count}
        ```
    """
    return action(
        method="GET",
        path=path,
        response_model=response_model,
        summary=summary,
        description=description,
        **kwargs
    )


def post(
    path: Optional[str] = None,
    response_model: Optional[Type] = None,
    status_code: int = 200,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Convenience decorator for POST requests.

    Equivalent to @action(method="POST", ...)

    Example:
        ```python
        @post(status_code=201, summary="Create new counter")
        async def create(self):
            self.save()
            return {"id": self.id}
        ```
    """
    return action(
        method="POST",
        path=path,
        response_model=response_model,
        status_code=status_code,
        summary=summary,
        description=description,
        **kwargs
    )


def put(
    path: Optional[str] = None,
    response_model: Optional[Type] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Convenience decorator for PUT requests.

    Equivalent to @action(method="PUT", ...)

    Example:
        ```python
        @put(summary="Update counter value")
        def update(self, count: int):
            self.count = count
            self.save()
        ```
    """
    return action(
        method="PUT",
        path=path,
        response_model=response_model,
        summary=summary,
        description=description,
        **kwargs
    )


def delete(
    path: Optional[str] = None,
    status_code: int = 204,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Convenience decorator for DELETE requests.

    Equivalent to @action(method="DELETE", status_code=204, ...)

    Example:
        ```python
        @delete(summary="Delete counter")
        def remove(self):
            self.delete()
        ```
    """
    return action(
        method="DELETE",
        path=path,
        status_code=status_code,
        summary=summary,
        description=description,
        **kwargs
    )


# Export metadata class for type hints
__all__ = [
    "action",
    "get",
    "post",
    "put",
    "delete",
    "ActionMetadata",
]
