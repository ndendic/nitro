"""GraphQL type and schema generation from Nitro Entity models.

This module converts Entity field metadata (via Pydantic's model_json_schema)
into GraphQL type definitions — SDL strings and runtime type descriptors.

Type mapping (Python/JSON-schema → GraphQL):
    string         → String
    integer        → Int
    number         → Float
    boolean        → Boolean
    array          → [T]
    object         → JSON (scalar)
    format=uuid    → ID
    Optional[T]    → T   (nullable in GraphQL by omitting !)

Public API
----------
map_field_type(field_info) -> str
    Return the GraphQL type string for a single field.

entity_to_type_def(entity_class, extra_scalars) -> str
    Return the SDL ``type`` block for one entity.

generate_schema(entity_classes, extra_scalars) -> str
    Return a complete SDL document for one or more entity classes,
    including Query and Mutation root types.

EntityTypeInfo
    Dataclass holding the parsed type information for an entity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type

from nitro.html.components.model_views.fields import get_model_fields


# ---------------------------------------------------------------------------
# Python / JSON-schema → GraphQL type mapping
# ---------------------------------------------------------------------------

_TYPE_MAP: dict[str, str] = {
    "string": "String",
    "integer": "Int",
    "number": "Float",
    "boolean": "Boolean",
    "array": "[String]",   # items resolved separately when possible
    "object": "JSON",
}

_FORMAT_MAP: dict[str, str] = {
    "uuid": "ID",
    "email": "String",
    "uri": "String",
    "date": "String",
    "date-time": "String",
    "time": "String",
}

# Scalar that must appear in the SDL when used
JSON_SCALAR = "scalar JSON"


def map_field_type(field_info: dict[str, Any], *, required: bool = True) -> str:
    """Return the GraphQL type string for a single field metadata dict.

    Args:
        field_info: Field metadata from ``get_model_fields()``.
        required: If True and the field is non-null, appends ``!``.

    Returns:
        GraphQL type string, e.g. ``"String!"``, ``"Int"``, ``"[String!]!"``.
    """
    ftype = field_info.get("type", "string")
    fmt = field_info.get("format")
    is_required = field_info.get("required", False) and required

    # Format overrides type for scalars
    if fmt and fmt in _FORMAT_MAP:
        gql_type = _FORMAT_MAP[fmt]
    elif ftype in _TYPE_MAP:
        gql_type = _TYPE_MAP[ftype]
    else:
        gql_type = "String"  # safe fallback

    # id field always maps to ID scalar
    if field_info.get("name") == "id":
        gql_type = "ID"
        is_required = True

    bang = "!" if is_required else ""
    return f"{gql_type}{bang}"


# ---------------------------------------------------------------------------
# Entity → SDL type block
# ---------------------------------------------------------------------------

@dataclass
class FieldDef:
    """Parsed GraphQL field definition."""
    name: str
    gql_type: str
    description: str = ""

    def to_sdl(self) -> str:
        lines: list[str] = []
        if self.description:
            lines.append(f'  """{self.description}"""')
        lines.append(f"  {self.name}: {self.gql_type}")
        return "\n".join(lines)


@dataclass
class EntityTypeInfo:
    """Holds all type information for a single Entity class."""
    entity_class: Any
    type_name: str
    fields: list[FieldDef] = field(default_factory=list)
    uses_json_scalar: bool = False

    @property
    def query_one_name(self) -> str:
        return self.type_name[0].lower() + self.type_name[1:]

    @property
    def query_list_name(self) -> str:
        return self.query_one_name + "s"

    @property
    def mutation_create_name(self) -> str:
        return f"create{self.type_name}"

    @property
    def mutation_update_name(self) -> str:
        return f"update{self.type_name}"

    @property
    def mutation_delete_name(self) -> str:
        return f"delete{self.type_name}"


def _build_entity_type_info(entity_class: type) -> EntityTypeInfo:
    """Build ``EntityTypeInfo`` from an Entity subclass."""
    type_name = entity_class.__name__
    info = EntityTypeInfo(entity_class=entity_class, type_name=type_name)

    raw_fields = get_model_fields(entity_class)

    # Ensure id is first
    ordered: list[tuple[str, dict]] = []
    if "id" in raw_fields:
        ordered.append(("id", raw_fields["id"]))
    for name, fdata in raw_fields.items():
        if name != "id":
            ordered.append((name, fdata))

    for name, fdata in ordered:
        gql_type = map_field_type(fdata)
        if "JSON" in gql_type:
            info.uses_json_scalar = True
        desc = fdata.get("description", "")
        info.fields.append(FieldDef(name=name, gql_type=gql_type, description=desc))

    return info


def entity_to_type_def(entity_class: type, *, include_description: bool = True) -> str:
    """Return the SDL ``type`` block string for a single entity.

    Example output::

        type Product {
          id: ID!
          name: String!
          price: Float
        }
    """
    info = _build_entity_type_info(entity_class)
    lines: list[str] = []

    if include_description:
        doc = getattr(entity_class, "__doc__", None)
        if doc:
            lines.append(f'"""{doc.strip()}"""')

    lines.append(f"type {info.type_name} {{")
    for fd in info.fields:
        lines.append(fd.to_sdl())
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Input types (for create / update mutations)
# ---------------------------------------------------------------------------

def _input_type_sdl(info: EntityTypeInfo, *, for_update: bool = False) -> str:
    """Generate Create or Update input type SDL."""
    suffix = "UpdateInput" if for_update else "CreateInput"
    lines = [f"input {info.type_name}{suffix} {{"]
    for fd in info.fields:
        if fd.name == "id":
            continue  # never in input
        # For updates all fields are optional
        gql_type = fd.gql_type.rstrip("!") if for_update else fd.gql_type
        if fd.description:
            lines.append(f'  """{fd.description}"""')
        lines.append(f"  {fd.name}: {gql_type}")
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full schema SDL generation
# ---------------------------------------------------------------------------

def generate_schema(
    entity_classes: Sequence[type],
    *,
    include_mutations: bool = True,
) -> str:
    """Build a complete SDL document from a collection of Entity classes.

    Generates:
    - One ``type`` block per entity
    - One ``input`` block per entity (Create + Update)
    - Root ``type Query`` with get-by-id and list operations
    - Root ``type Mutation`` with create, update, delete (when include_mutations=True)
    - ``scalar JSON`` if any field uses it

    Args:
        entity_classes: Sequence of Entity subclasses to include.
        include_mutations: Whether to include Mutation type (default True).

    Returns:
        SDL string ready for use with any GraphQL executor.
    """
    type_infos = [_build_entity_type_info(cls) for cls in entity_classes]
    uses_json = any(ti.uses_json_scalar for ti in type_infos)

    parts: list[str] = []

    if uses_json:
        parts.append(JSON_SCALAR)
        parts.append("")

    # Type definitions
    for info in type_infos:
        parts.append(entity_to_type_def(info.entity_class))
        parts.append("")

    # Input types
    for info in type_infos:
        parts.append(_input_type_sdl(info, for_update=False))
        parts.append("")
        parts.append(_input_type_sdl(info, for_update=True))
        parts.append("")

    # Query type
    query_fields: list[str] = []
    for info in type_infos:
        query_fields.append(f"  {info.query_one_name}(id: ID!): {info.type_name}")
        query_fields.append(f"  {info.query_list_name}: [{info.type_name}!]!")

    parts.append("type Query {")
    parts.extend(query_fields)
    parts.append("}")
    parts.append("")

    if include_mutations:
        mutation_fields: list[str] = []
        for info in type_infos:
            mutation_fields.append(
                f"  {info.mutation_create_name}(input: {info.type_name}CreateInput!): {info.type_name}!"
            )
            mutation_fields.append(
                f"  {info.mutation_update_name}(id: ID!, input: {info.type_name}UpdateInput!): {info.type_name}"
            )
            mutation_fields.append(
                f"  {info.mutation_delete_name}(id: ID!): Boolean!"
            )

        parts.append("type Mutation {")
        parts.extend(mutation_fields)
        parts.append("}")

    return "\n".join(parts)
