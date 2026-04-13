"""Entity serialization — convert entities to dicts with field selection."""
from __future__ import annotations

from typing import Any, Optional

from nitro.html.components.model_views.fields import get_model_fields


def serialize_entity(
    entity,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Serialize an entity to a dict with optional field filtering.

    Args:
        entity: Entity instance to serialize.
        include: If set, only these fields are included.
        exclude: Fields to exclude from output.

    Returns:
        Dictionary of field name → value.
    """
    all_fields = get_model_fields(entity.__class__)
    # Always include 'id' even if not in model_fields
    field_names = {"id"} | set(all_fields.keys())

    if include:
        field_names = field_names & set(include)
    if exclude:
        field_names = field_names - set(exclude)

    result = {}
    for name in sorted(field_names):
        value = getattr(entity, name, None)
        # Convert non-JSON-serializable types
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        result[name] = value

    return result


def serialize_many(
    entities: list,
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Serialize a list of entities."""
    return [serialize_entity(e, include=include, exclude=exclude) for e in entities]
