"""Entity discovery for the admin panel."""
from __future__ import annotations

from typing import Type


def discover_entities(base_class=None) -> list[Type]:
    """Return all concrete Entity subclasses that have ``table=True``.

    Only includes classes that define their own table (have ``__tablename__``
    and are not abstract base classes).

    Args:
        base_class: Starting class for discovery. Defaults to
            ``nitro.domain.entities.base_entity.Entity``.

    Returns:
        Sorted list of entity classes (alphabetical by name).
    """
    if base_class is None:
        from nitro.domain.entities.base_entity import Entity
        base_class = Entity

    entities = []
    _collect_subclasses(base_class, entities)
    return sorted(entities, key=lambda c: c.__name__)


def _collect_subclasses(cls, result: list) -> None:
    """Recursively collect concrete table-backed subclasses."""
    for sub in cls.__subclasses__():
        # SQLModel sets __tablename__ on table=True classes
        if _is_table_entity(sub):
            result.append(sub)
        _collect_subclasses(sub, result)


def _is_table_entity(cls) -> bool:
    """Check if a class is a concrete table-backed entity."""
    # SQLModel table classes get a __tablename__ attribute
    has_table = hasattr(cls, "__tablename__") or getattr(
        cls, "__table__", None
    ) is not None
    # Skip classes that are clearly abstract (no own fields beyond Entity)
    return has_table
