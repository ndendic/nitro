"""Decorator registry for custom field and model validators.

field_validator("field") — adds per-field custom validation logic
model_validator            — adds cross-field validation logic

These decorators attach metadata to entity class methods so that
validate_entity_data() can discover and invoke them.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Type

# Sentinel attribute names stored on the function/method
_FIELD_VALIDATOR_ATTR = "__nitro_field_validator__"
_MODEL_VALIDATOR_ATTR = "__nitro_model_validator__"


def field_validator(*field_names: str) -> Callable:
    """Decorator: mark a classmethod as a custom validator for one or more fields.

    The decorated method receives (cls, value, field_name) and should raise
    ValueError (with a human-readable message) when validation fails.

    Example::

        @field_validator("price")
        def price_positive(cls, value, field_name):
            if value <= 0:
                raise ValueError("Must be greater than zero")

    Multiple fields can share one validator::

        @field_validator("start_date", "end_date")
        def validate_date_format(cls, value, field_name):
            try:
                datetime.fromisoformat(value)
            except (TypeError, ValueError):
                raise ValueError(f"{field_name} must be ISO date (YYYY-MM-DD)")
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        setattr(wrapper, _FIELD_VALIDATOR_ATTR, list(field_names))
        return wrapper

    return decorator


def model_validator(fn: Callable) -> Callable:
    """Decorator: mark a classmethod as a cross-field (model-level) validator.

    The decorated method receives (cls, data: dict) where data contains all
    validated field values so far. Raise ValueError to signal a cross-field error.

    The error is stored under the key "__all__" in the error dict (mirrors Django
    and many other frameworks).

    Example::

        @model_validator
        def end_after_start(cls, data):
            if data.get("end") <= data.get("start"):
                raise ValueError("end must be after start")
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    setattr(wrapper, _MODEL_VALIDATOR_ATTR, True)
    return wrapper


# ------------------------------------------------------------------ #
# Introspection helpers (used by core.py)
# ------------------------------------------------------------------ #


def get_field_validators(
    entity_class: Type,
) -> dict[str, list[Callable]]:
    """Return {field_name: [validator_fn, ...]} for the given entity class.

    Walks the MRO so validators inherited from base classes are included.
    """
    validators: dict[str, list[Callable]] = {}

    for klass in reversed(entity_class.__mro__):
        for attr_name in vars(klass):
            attr = vars(klass)[attr_name]
            # Unwrap staticmethod / classmethod if needed
            raw = attr
            if isinstance(attr, (staticmethod, classmethod)):
                raw = attr.__func__

            fields = getattr(raw, _FIELD_VALIDATOR_ATTR, None)
            if fields is None:
                continue

            for field_name in fields:
                validators.setdefault(field_name, [])
                # Avoid duplicates from diamond inheritance
                if raw not in validators[field_name]:
                    validators[field_name].append(raw)

    return validators


def get_model_validators(entity_class: Type) -> list[Callable]:
    """Return a list of model-level validator functions for *entity_class*.

    Walks the MRO so inherited model validators are included.
    """
    validators: list[Callable] = []

    for klass in reversed(entity_class.__mro__):
        for attr_name in vars(klass):
            attr = vars(klass)[attr_name]
            raw = attr
            if isinstance(attr, (staticmethod, classmethod)):
                raw = attr.__func__

            if getattr(raw, _MODEL_VALIDATOR_ATTR, False):
                if raw not in validators:
                    validators.append(raw)

    return validators
