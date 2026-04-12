"""
Nitro Routing System.

Decorators register handlers in a simple registry. The action() helper
generates Datastar action strings. Framework adapters provide
catch-all endpoints that dispatch to registered handlers.
"""
from .decorator import action as action_decorator, get, post, put, delete, patch
from .metadata import ActionMetadata, get_action_metadata, has_action_metadata
from .actions import ActionRef, parse_action
from .action_helper import action
from .registration import register_entity_actions, NotFoundError
from .registry import register_handler, get_handler, clear_handlers, list_handlers

__all__ = [
    # Decorators
    "get", "post", "put", "delete", "patch",
    # action() helper (frontend string generator)
    "action",
    # Metadata
    "ActionMetadata", "get_action_metadata", "has_action_metadata",
    # Action parsing
    "ActionRef", "parse_action",
    # Registration (used by Entity.__init_subclass__)
    "register_entity_actions",
    # Registry (handler lookup)
    "register_handler", "get_handler", "clear_handlers", "list_handlers",
    # Errors
    "NotFoundError",
]
