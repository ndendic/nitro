"""Field introspection utilities for Pydantic models.

This module provides utilities for extracting field metadata from Pydantic Entity
classes and mapping them to appropriate UI components and input types.
"""

from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel
from nitro.utils import AttrDict

def get_model_fields(
    model: Type[BaseModel],
    exclude: Optional[List[str]] = None,
    include_computed: bool = False,
) -> AttrDict[str, Dict[str, Any]]:
    """Extract field metadata from a Pydantic model.
    Uses model_json_schema() to extract complete field metadata including
    json_schema_extra properties. Preserves field declaration order."""
    
    exclude = exclude or []

    # Use mode='serialization' to include computed fields when requested
    # mode='validation' (default) excludes computed fields
    mode = 'serialization' if include_computed else 'validation'
    schema = model.model_json_schema(mode=mode)
    props = schema.get('properties', {})
    required = set(schema.get('required', []))
    defs = schema.get('$defs', {})

    # Standard JSON schema keys that are part of the field definition
    standard_keys = {
        'type', 'format', 'title', 'description', 'enum',
        'default', 'anyOf', 'allOf', 'oneOf', 'items',
        'properties', 'additionalProperties', 'required',
        'minLength', 'maxLength', 'pattern', 'minimum',
        'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
        'multipleOf', 'minItems', 'maxItems', 'uniqueItems',
        'const', 'examples', '$ref', 'definitions', 'readOnly'
    }

    def resolve_ref(ref_path: str) -> Dict[str, Any]:
        """Resolve a $ref reference to its definition."""
        if ref_path.startswith('#/$defs/'):
            def_name = ref_path.split('/')[-1]
            return defs.get(def_name, {})
        return {}

    fields = AttrDict()
    for name, info in props.items():
        if name in exclude:
            continue

        # Resolve $ref if present (for enums)
        if '$ref' in info:
            ref_def = resolve_ref(info['$ref'])
            # Merge the reference definition with the field info
            # Field info (like default) takes precedence
            resolved_info = {**ref_def, **{k: v for k, v in info.items() if k != '$ref'}}
            info = resolved_info

        # Handle anyOf for Optional types
        field_type = info.get('type')
        field_format = info.get('format')
        constraints = {}  # Store validation constraints
        if info.get('anyOf'):
            # Extract non-null type from anyOf
            for t in info['anyOf']:
                if t.get('type') != 'null':
                    field_type = t.get('type', 'string')
                    # Also extract format if present in the anyOf item
                    if 'format' in t:
                        field_format = t['format']
                    # Extract validation constraints (minimum, maximum, etc.)
                    for constraint_key in ['minimum', 'maximum', 'minLength', 'maxLength']:
                        if constraint_key in t:
                            constraints[constraint_key] = t[constraint_key]
                    break

        # Extract extra metadata (anything not in standard JSON schema keys)
        extra = {k: v for k, v in info.items() if k not in standard_keys}
        # Add constraints to extra for easy access
        extra.update(constraints)

        # Handle readOnly flag from JSON schema (for computed fields)
        # Convert readOnly (camelCase) to read_only (snake_case)
        if info.get('readOnly'):
            extra['read_only'] = True

        fields[name] = {
            'model_name': model.__name__,
            'model_class': model,
            'name': name,
            'type': field_type,
            'format': field_format,
            'required': name in required,
            'title': info.get('title', name.replace('_', ' ').title()),
            'description': info.get('description', ''),
            'enum': info.get('enum'),
            'default': info.get('default'),
            'extra': extra,
        }

    return fields


def get_input_type(field_info: Dict[str, Any]) -> str:
    """Map Pydantic field schema to HTML input type.

    Determines the appropriate HTML input type based on the field's JSON schema
    type and format. Format hints take precedence over type.

    Args:
        field_info: Field metadata dict from get_model_fields()

    Returns:
        HTML input type string: 'text', 'email', 'number', 'date',
        'datetime-local', 'time', 'url', 'checkbox', 'select'

    Example:
        >>> field = {'type': 'string', 'format': 'email'}
        >>> get_input_type(field)
        'email'
        >>> field = {'type': 'integer'}
        >>> get_input_type(field)
        'number'
        >>> field = {'type': 'boolean'}
        >>> get_input_type(field)
        'checkbox'
    """
    ftype = field_info.get('type')
    fmt = field_info.get('format')

    # Format takes precedence over type
    if fmt == 'email':
        return 'email'
    if fmt == 'date':
        return 'date'
    if fmt == 'date-time':
        return 'datetime-local'
    if fmt == 'time':
        return 'time'
    if fmt == 'uri':
        return 'url'

    # Enum fields should use select
    if field_info.get('enum'):
        return 'select'

    # Type-based mapping
    if ftype == 'string':
        return 'text'
    if ftype == 'integer':
        return 'number'
    if ftype == 'number':
        return 'number'
    if ftype == 'boolean':
        return 'checkbox'

    # Default to text for unknown types
    return 'text'


def get_component_for_field(field_info: Dict[str, Any]) -> str:
    """Map field metadata to appropriate component name.

    Determines which Nitro component to use for rendering the field.
    Respects custom component overrides via json_schema_extra['component'].

    Args:
        field_info: Field metadata dict from get_model_fields()

    Returns:
        Component name string: 'Input', 'Textarea', 'Checkbox', 'Select', etc.

    Example:
        >>> field = {'type': 'string', 'extra': {}}
        >>> get_component_for_field(field)
        'Input'
        >>> field = {'type': 'string', 'extra': {'component': 'textarea'}}
        >>> get_component_for_field(field)
        'Textarea'
    """
    # Check for custom component override in extra metadata
    extra = field_info.get('extra', {})
    if extra and 'component' in extra:
        # Capitalize first letter for component name
        component = extra['component']
        return component[0].upper() + component[1:] if component else 'Input'

    # Map based on field type and format
    ftype = field_info.get('type')

    # Enum fields use Select
    if field_info.get('enum'):
        return 'Select'

    # Boolean fields use Checkbox
    if ftype == 'boolean':
        return 'Checkbox'

    # All other types default to Input (text, number, email, date, etc.)
    return 'Input'
