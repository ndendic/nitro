"""JSON Schema generation from Entity classes for OpenAPI components."""
from __future__ import annotations

from typing import Any, Optional, Type

from pydantic import BaseModel

from nitro.html.components.model_views.fields import get_model_fields


_FIELD_TYPE_MAP = {
    "string": {"type": "string"},
    "integer": {"type": "integer"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
    "array": {"type": "array", "items": {}},
    "object": {"type": "object"},
}

_FORMAT_MAP = {
    "email": "email",
    "uri": "uri",
    "date": "date",
    "date-time": "date-time",
    "time": "time",
    "uuid": "uuid",
}


def _field_to_schema(field_info: dict[str, Any]) -> dict[str, Any]:
    """Convert a single field metadata dict to an OpenAPI property schema."""
    ftype = field_info.get("type", "string")
    fmt = field_info.get("format")

    schema = dict(_FIELD_TYPE_MAP.get(ftype, {"type": "string"}))

    if fmt and fmt in _FORMAT_MAP:
        schema["format"] = _FORMAT_MAP[fmt]

    if field_info.get("description"):
        schema["description"] = field_info["description"]

    if field_info.get("enum"):
        schema["enum"] = field_info["enum"]

    if field_info.get("default") is not None:
        schema["default"] = field_info["default"]

    extra = field_info.get("extra", {})
    for constraint in ("minimum", "maximum", "minLength", "maxLength"):
        if constraint in extra:
            schema[constraint] = extra[constraint]

    if extra.get("read_only"):
        schema["readOnly"] = True

    return schema


def generate_schema(
    entity_class: Type[BaseModel],
    exclude: Optional[list[str]] = None,
    readonly_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Generate an OpenAPI-compatible JSON Schema for an entity class.

    Returns a schema dict with 'type', 'properties', and 'required' keys.
    """
    fields = get_model_fields(entity_class, exclude=exclude)

    properties: dict[str, Any] = {}
    required: list[str] = ["id"]

    if "id" not in fields:
        properties["id"] = {"type": "string"}

    for name, info in fields.items():
        prop = _field_to_schema(info)
        if readonly_fields and name in readonly_fields:
            prop["readOnly"] = True
        properties[name] = prop
        if info.get("required") and info.get("default") is None and name != "id":
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }


def generate_create_schema(
    entity_class: Type[BaseModel],
    exclude: Optional[list[str]] = None,
    readonly_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Generate a schema for create requests (no id, no readonly fields)."""
    fields = get_model_fields(entity_class, exclude=exclude)
    skip = set(readonly_fields or [])
    skip.add("id")

    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, info in fields.items():
        if name in skip:
            continue
        prop = _field_to_schema(info)
        prop.pop("readOnly", None)
        properties[name] = prop
        if info.get("required") and info.get("default") is None:
            required.append(name)

    result: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        result["required"] = required
    return result


def generate_update_schema(
    entity_class: Type[BaseModel],
    exclude: Optional[list[str]] = None,
    readonly_fields: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Generate a schema for update requests (all fields optional, no readonly)."""
    fields = get_model_fields(entity_class, exclude=exclude)
    skip = set(readonly_fields or [])
    skip.add("id")

    properties: dict[str, Any] = {}

    for name, info in fields.items():
        if name in skip:
            continue
        prop = _field_to_schema(info)
        prop.pop("readOnly", None)
        properties[name] = prop

    return {"type": "object", "properties": properties}
