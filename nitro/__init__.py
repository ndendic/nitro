# Re-export everything from rusty-tags core
__version__ = "0.1.0"

# Import Nitro-specific components
from nitro.utils import show, AttrDict, uniq
from nitro.infrastructure.events.events import *  # noqa: F403
from nitro.infrastructure.events.client import Client
from nitro.infrastructure.html import *  # noqa: F403
from nitro.infrastructure.html.datastar import *  # noqa: F403

# Phase 2: Auto-routing exports
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action, get, post, put, delete, ActionMetadata

__author__ = "Nikola Dendic"
__description__ = "Abstraction layers for Python web development."

__all__ = [
    # Core
    "Entity",
    # Routing decorators
    "action",
    "get",
    "post",
    "put",
    "delete",
    "ActionMetadata",
    # Utils
    "show",
    "AttrDict",
    "uniq",
    "Client",
]
