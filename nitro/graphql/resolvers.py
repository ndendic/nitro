"""Auto-generated resolvers from Entity CRUD operations.

This module builds Query and Mutation resolver dicts from Entity classes,
delegating to Entity methods (``.get()``, ``.all()``, ``.filter()``,
``.save()``, ``.delete()``).

Resolver signature: ``resolver(root, info, **kwargs) -> Any``

Public API
----------
build_resolvers(entity_classes) -> ResolverMap
    Build a complete resolver map for the given entity classes.

ResolverMap
    TypedDict-like dict ``{"Query": {...}, "Mutation": {...}}``.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Type


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

ResolverMap = Dict[str, Dict[str, Any]]
"""Nested dict: ``{TypeName: {fieldName: callable}}``."""


# ---------------------------------------------------------------------------
# Entity serialization helper
# ---------------------------------------------------------------------------

def _entity_to_dict(entity: Any) -> dict[str, Any]:
    """Convert an Entity instance to a plain dict for GraphQL response."""
    if entity is None:
        return None  # type: ignore[return-value]
    try:
        return entity.model_dump()
    except AttributeError:
        # Fallback for non-Pydantic objects
        return {k: v for k, v in vars(entity).items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# Query resolver builders
# ---------------------------------------------------------------------------

def _make_get_resolver(entity_class: type):
    """Build a resolver that fetches one entity by ID."""
    def resolve_get(root: Any, info: Any, id: str) -> Optional[dict]:
        entity = entity_class.get(id)
        return _entity_to_dict(entity) if entity is not None else None

    resolve_get.__name__ = f"resolve_{entity_class.__name__}_get"
    return resolve_get


def _make_list_resolver(entity_class: type):
    """Build a resolver that returns all entities."""
    def resolve_list(root: Any, info: Any) -> list[dict]:
        entities = entity_class.all()
        return [_entity_to_dict(e) for e in entities]

    resolve_list.__name__ = f"resolve_{entity_class.__name__}_list"
    return resolve_list


# ---------------------------------------------------------------------------
# Mutation resolver builders
# ---------------------------------------------------------------------------

def _make_create_resolver(entity_class: type):
    """Build a resolver that creates a new entity."""
    def resolve_create(root: Any, info: Any, input: dict) -> dict:
        try:
            entity = entity_class(**input)
            entity.save()
            return _entity_to_dict(entity)
        except Exception as exc:
            raise GraphQLResolverError(f"Failed to create {entity_class.__name__}: {exc}") from exc

    resolve_create.__name__ = f"resolve_{entity_class.__name__}_create"
    return resolve_create


def _make_update_resolver(entity_class: type):
    """Build a resolver that updates an existing entity."""
    def resolve_update(root: Any, info: Any, id: str, input: dict) -> Optional[dict]:
        entity = entity_class.get(id)
        if entity is None:
            return None
        try:
            for key, value in input.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            entity.save()
            return _entity_to_dict(entity)
        except Exception as exc:
            raise GraphQLResolverError(f"Failed to update {entity_class.__name__}: {exc}") from exc

    resolve_update.__name__ = f"resolve_{entity_class.__name__}_update"
    return resolve_update


def _make_delete_resolver(entity_class: type):
    """Build a resolver that deletes an entity by ID."""
    def resolve_delete(root: Any, info: Any, id: str) -> bool:
        entity = entity_class.get(id)
        if entity is None:
            return False
        try:
            entity.delete()
            return True
        except Exception as exc:
            raise GraphQLResolverError(f"Failed to delete {entity_class.__name__}: {exc}") from exc

    resolve_delete.__name__ = f"resolve_{entity_class.__name__}_delete"
    return resolve_delete


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class GraphQLResolverError(Exception):
    """Raised when a resolver encounters a domain error."""


# ---------------------------------------------------------------------------
# Public: build resolver map
# ---------------------------------------------------------------------------

def build_resolvers(entity_classes: Sequence[type]) -> ResolverMap:
    """Build a complete resolver map for the given entity classes.

    Returns a nested dict:
    ::

        {
            "Query": {
                "product":  <get resolver>,
                "products": <list resolver>,
                ...
            },
            "Mutation": {
                "createProduct": <create resolver>,
                "updateProduct": <update resolver>,
                "deleteProduct": <delete resolver>,
                ...
            },
        }

    Args:
        entity_classes: Sequence of Entity subclasses.

    Returns:
        ResolverMap dict.
    """
    query_resolvers: dict[str, Any] = {}
    mutation_resolvers: dict[str, Any] = {}

    for cls in entity_classes:
        type_name = cls.__name__
        query_one = type_name[0].lower() + type_name[1:]
        query_list = query_one + "s"

        query_resolvers[query_one] = _make_get_resolver(cls)
        query_resolvers[query_list] = _make_list_resolver(cls)

        create_name = f"create{type_name}"
        update_name = f"update{type_name}"
        delete_name = f"delete{type_name}"

        mutation_resolvers[create_name] = _make_create_resolver(cls)
        mutation_resolvers[update_name] = _make_update_resolver(cls)
        mutation_resolvers[delete_name] = _make_delete_resolver(cls)

    return {
        "Query": query_resolvers,
        "Mutation": mutation_resolvers,
    }
