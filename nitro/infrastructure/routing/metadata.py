"""
Action Metadata - Storage and retrieval for @action decorator metadata

This module provides the ActionMetadata class and helper functions for
storing and retrieving routing information from decorated methods.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Type, Any, Callable
from inspect import signature, Parameter


@dataclass
class ActionMetadata:
    """
    Metadata for an @action decorated entity method.

    Stores all routing information needed to generate HTTP endpoints.
    """

    # HTTP configuration
    method: str = "POST"  # GET, POST, PUT, DELETE, PATCH
    path: Optional[str] = None  # Custom URL path (None = auto-generate)
    status_code: int = 200  # Default success status code

    # OpenAPI documentation
    summary: Optional[str] = None  # Short description
    description: Optional[str] = None  # Long description
    tags: List[str] = field(default_factory=list)  # OpenAPI tags
    response_model: Optional[Type] = None  # Pydantic response model

    # Internal metadata
    function_name: str = ""  # Original method name
    entity_class_name: str = ""  # Entity class name
    is_async: bool = False  # Whether method is async
    parameters: dict = field(default_factory=dict)  # Parameter signatures

    # Advanced options (future use)
    requires_auth: bool = False  # Authentication required (Phase 2.2)
    rate_limit: Optional[str] = None  # Rate limit spec (Phase 2.3)
    cache_ttl: Optional[int] = None  # Cache TTL for GET (Phase 2.4)

    def __post_init__(self):
        """Validate metadata after initialization."""
        # Normalize HTTP method to uppercase
        self.method = self.method.upper()

        # Validate HTTP method
        valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}
        if self.method not in valid_methods:
            raise ValueError(
                f"Invalid HTTP method: {self.method}. "
                f"Must be one of {valid_methods}"
            )

        # Validate status code
        if not (100 <= self.status_code < 600):
            raise ValueError(
                f"Invalid status code: {self.status_code}. "
                f"Must be between 100 and 599"
            )

    def generate_url_path(
        self,
        prefix: str = "",
        entity_name_override: Optional[str] = None
    ) -> str:
        """
        Generate URL path for this action.

        Args:
            prefix: URL prefix (e.g., "/api/v1")
            entity_name_override: Custom entity name (e.g., "users" instead of "user")

        Returns:
            Generated URL path

        Examples:
            Counter.increment -> "/counter/{id}/increment"
            Product.search -> "/product/search" (class method, no {id})
            With override: "/users/{id}/activate" (entity_name_override="users")
            With custom path: @action(path="/add") -> "/counter/{id}/add"
        """
        # Get entity name (custom or default)
        entity_name = (entity_name_override or self.entity_class_name).lower()

        # Check if method requires instance (has 'self' parameter)
        requires_id = "self" in self.parameters

        # Determine the action segment (custom path or method name)
        if self.path:
            # Check if this is an absolute custom path (contains multiple segments or /)
            # Absolute path: "/custom/path" or "/api/custom"
            # Relative path: "add", "/add" (single segment after /)
            path_parts = self.path.strip('/').split('/')

            if len(path_parts) > 1:
                # Multiple segments = absolute custom path, use as-is
                custom_path = self.path if self.path.startswith('/') else f'/{self.path}'
                return f"{prefix}{custom_path}" if prefix else custom_path
            else:
                # Single segment = replace action name only
                action_segment = path_parts[0]
        else:
            # Use method name
            action_segment = self.function_name

        # Build final path with entity name
        if requires_id:
            path = f"/{entity_name}/{{id}}/{action_segment}"
        else:
            # Class method - no {id} in path
            path = f"/{entity_name}/{action_segment}"

        # Add prefix if provided
        return f"{prefix}{path}" if prefix else path

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ActionMetadata("
            f"method={self.method}, "
            f"path={self.path or 'auto'}, "
            f"function={self.entity_class_name}.{self.function_name})"
        )


# Attribute name for storing metadata on decorated functions
_NITRO_ACTION_METADATA_ATTR = "_nitro_action_metadata"


def set_action_metadata(func: Callable, metadata: ActionMetadata) -> None:
    """
    Store action metadata on a function.

    Args:
        func: Function to attach metadata to
        metadata: ActionMetadata instance
    """
    setattr(func, _NITRO_ACTION_METADATA_ATTR, metadata)


def get_action_metadata(func: Callable) -> Optional[ActionMetadata]:
    """
    Retrieve action metadata from a function.

    Args:
        func: Function to retrieve metadata from

    Returns:
        ActionMetadata if present, None otherwise
    """
    return getattr(func, _NITRO_ACTION_METADATA_ATTR, None)


def has_action_metadata(func: Callable) -> bool:
    """
    Check if a function has action metadata.

    Args:
        func: Function to check

    Returns:
        True if function has @action metadata, False otherwise
    """
    return hasattr(func, _NITRO_ACTION_METADATA_ATTR)


def extract_parameters(func: Callable) -> dict:
    """
    Extract parameter information from a function signature.

    Args:
        func: Function to analyze

    Returns:
        Dictionary mapping parameter names to their annotations

    Example:
        def increment(self, amount: int = 1, notify: bool = False):
            ...

        Returns:
            {
                "self": {"annotation": None, "default": Parameter.empty},
                "amount": {"annotation": int, "default": 1},
                "notify": {"annotation": bool, "default": False}
            }
    """
    sig = signature(func)
    params = {}

    for param_name, param in sig.parameters.items():
        params[param_name] = {
            "annotation": param.annotation if param.annotation != Parameter.empty else None,
            "default": param.default if param.default != Parameter.empty else None,
            "kind": param.kind.name,  # POSITIONAL_OR_KEYWORD, KEYWORD_ONLY, etc.
        }

    return params
