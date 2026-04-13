"""
Entity factory for generating test data.

Provides EntityFactory — a generic factory for any Pydantic/SQLModel-based
Entity subclass. Auto-generates sensible random values for common field types
using only stdlib (random + uuid + datetime). Respects Pydantic defaults when
present; only generates values for fields that have no default.
"""

import random
import string
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def _random_email() -> str:
    return f"{_random_string(6)}@{_random_string(4)}.com"


def _generate_for_type(annotation: Any) -> Any:
    """
    Return a sensible random value for a Python type annotation.

    Handles: str, int, float, bool, datetime, Optional[X].
    Falls back to None for unknown types.
    """
    import types
    import typing

    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", ())

    # Optional[X] / Union[X, None]
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if non_none:
            return _generate_for_type(non_none[0])
        return None

    # Resolve plain type
    target = origin if origin not in (None,) else annotation

    if target is str:
        return _random_string()
    if target is int:
        return random.randint(1, 1000)
    if target is float:
        return round(random.uniform(0.0, 1000.0), 2)
    if target is bool:
        return random.choice([True, False])
    if target is datetime:
        return datetime.now(timezone.utc)

    # Unknown — return None (caller can override)
    return None


_SENTINEL = object()  # marks "no default at all"


def _field_default(model_class: Any, field_name: str) -> Any:
    """
    Return the default value for a Pydantic/SQLModel field, or _SENTINEL if
    there is none (meaning the field is required).

    Handles PydanticUndefined, Ellipsis, and None defaults correctly.
    """
    try:
        from pydantic_core import PydanticUndefinedType

        fields = model_class.model_fields
        if field_name not in fields:
            return _SENTINEL
        field_info = fields[field_name]

        # Required field — Pydantic marks these with PydanticUndefined or ...
        if field_info.is_required():
            return _SENTINEL

        # Has a default_factory (e.g. lambda: str(uuid.uuid4()))
        if field_info.default_factory is not None:
            return field_info.default_factory()

        # Has an explicit default (may be None, False, 0, "" — all valid)
        default = field_info.default
        if isinstance(default, PydanticUndefinedType) or default is ...:
            return _SENTINEL

        return default
    except Exception:
        return _SENTINEL


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class EntityFactory:
    """
    Generic factory for building test instances of any Pydantic / SQLModel entity.

    Usage::

        from nitro.testing import EntityFactory

        factory = EntityFactory(MyEntity)

        entity = factory.build(name="Alice")        # unsaved instance
        entity = factory.create(name="Alice")       # saved to repository
        entities = factory.create_batch(5)          # 5 saved entities
        entities = factory.build_batch(3)           # 3 unsaved entities

    Auto-generation rules (applied only when a field has no default):

    - ``str``      → random 8-char lowercase string
    - ``int``      → random int in [1, 1000]
    - ``float``    → random float in [0.0, 1000.0]
    - ``bool``     → random True/False
    - ``datetime`` → current UTC datetime
    - ``Optional[X]`` → generates value for the inner type
    - ``id``       → always a new UUID (overrides everything)
    """

    def __init__(self, model_class: Type[T]) -> None:
        self.model_class = model_class

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _make_kwargs(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Build a full kwargs dict suitable for constructing the model."""
        kwargs: Dict[str, Any] = {}
        fields = getattr(self.model_class, "model_fields", {})

        for field_name, field_info in fields.items():
            if field_name in overrides:
                kwargs[field_name] = overrides[field_name]
                continue

            # Always give id a fresh UUID unless caller overrides it
            if field_name == "id":
                kwargs[field_name] = str(uuid.uuid4())
                continue

            default = _field_default(self.model_class, field_name)
            if default is _SENTINEL:
                # Required field — generate a value
                annotation = field_info.annotation
                kwargs[field_name] = _generate_for_type(annotation)
            # else: has a default, let Pydantic handle it

        return kwargs

    def build(self, **overrides: Any) -> T:
        """
        Return an unsaved entity instance with auto-generated field values.

        Any keyword argument overrides the auto-generated value for that field.
        """
        kwargs = self._make_kwargs(overrides)
        return self.model_class(**kwargs)

    def create(self, **overrides: Any) -> T:
        """
        Build and save an entity to the repository.

        Calls ``entity.save()`` — the entity must have a ``save()`` method
        (i.e. be a ``nitro.domain.entities.base_entity.Entity`` subclass).
        """
        entity = self.build(**overrides)
        entity.save()
        return entity

    def build_batch(self, n: int, **overrides: Any) -> List[T]:
        """Build ``n`` unsaved entity instances."""
        return [self.build(**overrides) for _ in range(n)]

    def create_batch(self, n: int, **overrides: Any) -> List[T]:
        """Build and save ``n`` entity instances."""
        return [self.create(**overrides) for _ in range(n)]
