"""
Nitro Routing Infrastructure - Auto-routing for Entity Actions

This module provides the @action decorator and dispatcher system for
automatically generating HTTP routes from entity methods.

Phase 2.1: Auto-Magic Routing System
"""

from .decorator import action, ActionMetadata, get, post, put, delete
from .metadata import get_action_metadata, has_action_metadata
from .discovery import (
    discover_entity_subclasses,
    discover_action_methods,
    discover_all_routes,
    validate_action_uniqueness,
)
from .dispatcher import NitroDispatcher

__all__ = [
    # Decorators
    "action",
    "get",
    "post",
    "put",
    "delete",
    # Metadata
    "ActionMetadata",
    "get_action_metadata",
    "has_action_metadata",
    # Discovery
    "discover_entity_subclasses",
    "discover_action_methods",
    "discover_all_routes",
    "validate_action_uniqueness",
    # Dispatcher
    "NitroDispatcher",
]
