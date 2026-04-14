"""Core validation logic for nitro.validation.

ValidationResult  — result container
validate_entity_data — main entry point
validate_request     — framework-agnostic request helper
"""

from __future__ import annotations

import json
from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError

from .decorators import get_field_validators, get_model_validators


# ------------------------------------------------------------------ #
# ValidationResult
# ------------------------------------------------------------------ #


class ValidationResult:
    """Outcome of a validation pass.

    Attributes:
        is_valid (bool)     : True when no errors were collected.
        errors (dict)       : {field_name: [error_msg, ...]}. The key "__all__"
                              holds model-level (cross-field) errors. Empty when
                              validation passed.
        data (dict | None)  : The cleaned, coerced field values when is_valid is
                              True; None otherwise.
    """

    __slots__ = ("is_valid", "errors", "data")

    def __init__(
        self,
        *,
        errors: dict[str, list[str]],
        data: Optional[dict[str, Any]],
    ) -> None:
        self.errors = errors
        self.data = data if not errors else None
        self.is_valid = not bool(errors)

    # ---------------------------------------------------------------- #
    # Error formatting
    # ---------------------------------------------------------------- #

    def to_json_errors(self) -> dict[str, Any]:
        """Return a JSON-serialisable error structure for API responses.

        Shape::

            {
                "valid": false,
                "errors": {
                    "price": ["Must be greater than zero"],
                    "__all__": ["end must be after start"]
                }
            }
        """
        return {
            "valid": self.is_valid,
            "errors": dict(self.errors),
        }

    def to_form_errors(self) -> dict[str, str]:
        """Return a flat {field: first_error_message} dict for form rendering.

        Only the first error per field is returned, which is sufficient for
        highlighting individual form inputs.
        """
        return {
            field: messages[0]
            for field, messages in self.errors.items()
            if messages
        }

    def first_error(self, field: str) -> Optional[str]:
        """Return the first error message for *field*, or None."""
        msgs = self.errors.get(field)
        return msgs[0] if msgs else None

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:  # pragma: no cover
        if self.is_valid:
            return f"<ValidationResult valid data={list((self.data or {}).keys())}>"
        return f"<ValidationResult invalid errors={list(self.errors.keys())}>"


# ------------------------------------------------------------------ #
# validate_entity_data
# ------------------------------------------------------------------ #


def validate_entity_data(
    entity_class: Type[BaseModel],
    data: dict[str, Any],
    *,
    partial: bool = False,
) -> ValidationResult:
    """Validate *data* against *entity_class* and return a :class:`ValidationResult`.

    Args:
        entity_class: A Pydantic BaseModel subclass (typically an Entity).
        data:         Raw input dict (e.g., parsed request body).
        partial:      When True, treat all fields as optional — useful for PATCH
                      requests where only a subset of fields is supplied.

    Returns:
        A :class:`ValidationResult` with full per-field error collection.

    All validation stages run in order:
    1. Pydantic schema validation (type coercion, required fields, constraints).
    2. Custom field validators registered with ``@field_validator``.
    3. Cross-field model validators registered with ``@model_validator``.

    Validation continues even after failures so callers receive a complete list
    of errors in a single pass.
    """
    errors: dict[str, list[str]] = {}
    coerced: dict[str, Any] = {}

    # ---------------------------------------------------------------- #
    # Stage 1 — Pydantic schema validation
    # ---------------------------------------------------------------- #
    if partial:
        # For partial validation we only validate the fields that are present.
        # Build a model with only those fields by temporarily making everything
        # optional via model_validate on a filtered input.
        clean_data = _partial_validate(entity_class, data, errors)
    else:
        clean_data = _full_validate(entity_class, data, errors)

    # Start with whatever pydantic accepted (may be partial on error)
    coerced.update(clean_data)

    # ---------------------------------------------------------------- #
    # Stage 2 — Custom field validators
    # ---------------------------------------------------------------- #
    field_validators = get_field_validators(entity_class)

    for field_name, validators in field_validators.items():
        if field_name not in coerced:
            # Field absent (partial mode) or already failed schema validation
            continue

        value = coerced[field_name]
        for validator_fn in validators:
            try:
                validator_fn(entity_class, value, field_name)
            except ValueError as exc:
                errors.setdefault(field_name, []).append(str(exc))

    # ---------------------------------------------------------------- #
    # Stage 3 — Cross-field (model) validators
    # ---------------------------------------------------------------- #
    model_validators = get_model_validators(entity_class)

    for validator_fn in model_validators:
        try:
            validator_fn(entity_class, coerced)
        except ValueError as exc:
            errors.setdefault("__all__", []).append(str(exc))

    return ValidationResult(
        errors=errors,
        data=coerced if not errors else None,
    )


# ------------------------------------------------------------------ #
# validate_request
# ------------------------------------------------------------------ #


def validate_request(
    entity_class: Type[BaseModel],
    request: Any,
    *,
    partial: bool = False,
) -> ValidationResult:
    """Extract data from *request* and validate against *entity_class*.

    Supports requests from Sanic, Flask, FastAPI/Starlette, or any object that
    exposes one of:
    - ``.json``        — Sanic / dict attribute
    - ``.json()``      — Sanic async (call result), or synchronous callable
    - ``.get_json()``  — Flask
    - ``.body``        — raw bytes (decoded as UTF-8 JSON)

    Falls back to an empty dict if no data can be extracted, which will
    trigger required-field errors via the normal validation path.

    Args:
        entity_class: The Entity/BaseModel class to validate against.
        request:      A framework request object or anything with the above attrs.
        partial:      Pass True for PATCH-style partial updates.

    Returns:
        A :class:`ValidationResult`.
    """
    data = _extract_data(request)
    return validate_entity_data(entity_class, data, partial=partial)


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _full_validate(
    entity_class: Type[BaseModel],
    data: dict[str, Any],
    errors: dict[str, list[str]],
) -> dict[str, Any]:
    """Run Pydantic validation on all fields. Collect per-field errors."""
    try:
        instance = entity_class.model_validate(data)
        return instance.model_dump()
    except ValidationError as exc:
        coerced = dict(data)  # best-effort: keep raw values for stage 2/3
        for err in exc.errors():
            # loc is a tuple like ("field_name",) or ("field_name", "sub")
            loc = err.get("loc", ())
            field = str(loc[0]) if loc else "__all__"
            msg = _friendly_pydantic_message(err)
            errors.setdefault(field, []).append(msg)
        return coerced


def _partial_validate(
    entity_class: Type[BaseModel],
    data: dict[str, Any],
    errors: dict[str, list[str]],
) -> dict[str, Any]:
    """Run Pydantic validation only on provided fields (partial/PATCH mode).

    Strategy: build a temporary model with all fields optional, then validate
    only the keys present in *data*.
    """
    # Filter to only provided keys
    provided = {k: v for k, v in data.items() if k in entity_class.model_fields}

    if not provided:
        return {}

    try:
        # Use model_validate with strict=False, only the provided fields
        partial_model = entity_class.model_validate(provided)
        return {k: getattr(partial_model, k) for k in provided}
    except ValidationError as exc:
        coerced = dict(provided)
        for err in exc.errors():
            loc = err.get("loc", ())
            field = str(loc[0]) if loc else "__all__"
            # Only report errors for fields that were actually provided
            if field in provided or field == "__all__":
                msg = _friendly_pydantic_message(err)
                errors.setdefault(field, []).append(msg)
        return coerced


def _friendly_pydantic_message(err: dict[str, Any]) -> str:
    """Convert a Pydantic v2 error dict to a human-readable string."""
    err_type = err.get("type", "")
    msg = err.get("msg", "Invalid value")

    # Strip the verbose pydantic prefix "Value error, " if present
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]

    return msg


def _extract_data(request: Any) -> dict[str, Any]:
    """Extract a dict from a framework request object."""
    # Dict or dict-like passed directly
    if isinstance(request, dict):
        return request

    # Attribute: .json (Sanic — may be dict or None)
    json_attr = getattr(request, "json", None)
    if json_attr is not None:
        if callable(json_attr):
            try:
                result = json_attr()
                if isinstance(result, dict):
                    return result
            except Exception:
                pass
        elif isinstance(json_attr, dict):
            return json_attr

    # Flask: .get_json()
    get_json = getattr(request, "get_json", None)
    if callable(get_json):
        try:
            result = get_json()
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    # Raw bytes body
    body = getattr(request, "body", None)
    if body:
        try:
            if isinstance(body, (bytes, bytearray)):
                body = body.decode("utf-8")
            return json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    return {}
