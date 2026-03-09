"""
Nitro Event-Driven Routing System.

Decorators register Blinker event handlers. The action() helper
generates Datastar action strings. Framework adapters provide
catch-all endpoints.
"""
from .decorator import action as action_decorator, get, post, put, delete
from .metadata import ActionMetadata, get_action_metadata, has_action_metadata
from .actions import ActionRef, parse_action
from .action_helper import action
from .registration import register_entity_actions, NotFoundError

__all__ = [
    # Decorators
    "get", "post", "put", "delete",
    # action() helper (frontend string generator)
    "action",
    # Metadata
    "ActionMetadata", "get_action_metadata", "has_action_metadata",
    # Action parsing
    "ActionRef", "parse_action",
    # Registration (used by Entity.__init_subclass__)
    "register_entity_actions",
    # Errors
    "NotFoundError",
]
