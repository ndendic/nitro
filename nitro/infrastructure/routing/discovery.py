"""
Entity and Action Discovery - Find entities and their @action methods

This module provides utilities for discovering Entity subclasses and their
@action decorated methods for auto-routing.
"""

from typing import List, Type, Dict, Callable, Tuple, Any
from inspect import getmembers, ismethod, isfunction

from .metadata import has_action_metadata, get_action_metadata, ActionMetadata


def discover_entity_subclasses(base_class: Type) -> List[Type]:
    """
    Recursively discover all subclasses of a base class.

    This function finds all Entity subclasses that have been imported
    and are available in the current Python runtime.

    Args:
        base_class: The base class to find subclasses of (typically Entity)

    Returns:
        List of all subclass types, including nested subclasses

    Example:
        >>> from nitro import Entity
        >>> class Counter(Entity):
        ...     count: int = 0
        >>> class Product(Entity):
        ...     name: str = ""
        >>> entities = discover_entity_subclasses(Entity)
        >>> Counter in entities
        True
        >>> Product in entities
        True

    Note:
        - Only discovers classes that have been imported
        - Returns classes in arbitrary order
        - Includes abstract classes
        - Does NOT include the base class itself
    """
    subclasses = []

    def _recurse(cls):
        """Recursively collect subclasses."""
        for subclass in cls.__subclasses__():
            subclasses.append(subclass)
            _recurse(subclass)

    _recurse(base_class)
    return subclasses


def discover_action_methods(
    entity_class: Type,
    include_inherited: bool = True
) -> Dict[str, Tuple[Callable, ActionMetadata]]:
    """
    Discover all @action decorated methods in an entity class.

    Scans the entity class for methods decorated with @action and returns
    their metadata. This is used by dispatchers to auto-register routes.

    Args:
        entity_class: The Entity class to scan for @action methods
        include_inherited: Whether to include methods from parent classes

    Returns:
        Dictionary mapping method names to (method, metadata) tuples

    Example:
        >>> class Counter(Entity):
        ...     @action(method="POST")
        ...     async def increment(self, amount: int = 1):
        ...         self.count += amount
        ...
        ...     @action(method="GET")
        ...     def status(self):
        ...         return {"count": self.count}
        >>>
        >>> actions = discover_action_methods(Counter)
        >>> "increment" in actions
        True
        >>> "status" in actions
        True
        >>> actions["increment"][1].method
        'POST'
        >>> actions["status"][1].method
        'GET'

    Note:
        - Only returns methods with @action decorator
        - Includes both sync and async methods
        - Metadata includes HTTP method, path, parameters, etc.
        - Sets entity_class_name in metadata if not already set
    """
    actions = {}

    # Get all members of the class
    # We need to check both the class and its instances
    for name, method in getmembers(entity_class):
        # Skip private/magic methods
        if name.startswith("_"):
            continue

        # Skip if not callable
        if not callable(method):
            continue

        # Check if method has @action metadata
        if has_action_metadata(method):
            metadata = get_action_metadata(method)

            # Set entity class name if not already set
            if not metadata.entity_class_name:
                metadata.entity_class_name = entity_class.__name__

            actions[name] = (method, metadata)

    return actions


def discover_all_routes(
    base_class: Type,
    entities: List[Type] = None
) -> Dict[Type, Dict[str, Tuple[Callable, ActionMetadata]]]:
    """
    Discover all routes from all entities.

    This is a convenience function that combines entity discovery and
    action discovery into a single operation.

    Args:
        base_class: The base Entity class
        entities: Optional list of specific entities to scan.
                  If None, auto-discovers all subclasses.

    Returns:
        Dictionary mapping entity classes to their action methods

    Example:
        >>> from nitro import Entity
        >>> routes = discover_all_routes(Entity)
        >>> Counter in routes
        True
        >>> "increment" in routes[Counter]
        True

    Note:
        - Combines discover_entity_subclasses() and discover_action_methods()
        - Only includes entities that have at least one @action method
        - Useful for bulk route registration
    """
    # Discover entities
    if entities is None:
        entities = discover_entity_subclasses(base_class)

    # Discover actions for each entity
    all_routes = {}
    for entity_class in entities:
        actions = discover_action_methods(entity_class)
        if actions:  # Only include if entity has actions
            all_routes[entity_class] = actions

    return all_routes


def validate_action_uniqueness(
    routes: Dict[Type, Dict[str, Tuple[Callable, ActionMetadata]]],
    prefix: str = ""
) -> List[str]:
    """
    Validate that all generated URLs are unique.

    Checks for URL conflicts that would cause routing issues.
    Respects __route_name__ attribute for custom entity route names.

    Args:
        routes: Routes dictionary from discover_all_routes()
        prefix: URL prefix to apply when checking

    Returns:
        List of error messages for conflicts (empty if no conflicts)

    Example:
        >>> routes = discover_all_routes(Entity)
        >>> errors = validate_action_uniqueness(routes)
        >>> if errors:
        ...     for error in errors:
        ...         print(f"ERROR: {error}")
    """
    errors = []
    seen_urls = {}

    for entity_class, actions in routes.items():
        # Check for custom entity route name
        entity_route_name = getattr(entity_class, '__route_name__', None)

        for method_name, (method, metadata) in actions.items():
            url = metadata.generate_url_path(prefix=prefix, entity_name_override=entity_route_name)
            http_method = metadata.method

            # URL + HTTP method combination must be unique
            route_key = (http_method, url)

            if route_key in seen_urls:
                prev_entity, prev_method = seen_urls[route_key]
                errors.append(
                    f"URL conflict: {http_method} {url} is used by both "
                    f"{prev_entity.__name__}.{prev_method} and "
                    f"{entity_class.__name__}.{method_name}"
                )
            else:
                seen_urls[route_key] = (entity_class, method_name)

    return errors


__all__ = [
    "discover_entity_subclasses",
    "discover_action_methods",
    "discover_all_routes",
    "validate_action_uniqueness",
]
