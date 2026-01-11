"""ModelField component - Renders individual form fields from Pydantic field metadata.

This module provides the ModelField component that maps Pydantic field metadata
to appropriate Nitro UI components with Datastar signal bindings.
"""

from typing import Any, Dict, Optional
from rusty_tags import Input, HtmlString
from rusty_tags.datastar import Signals
from nitro.html.components import (
    Field,
    Checkbox,
    Select,
    SelectOption,
    Textarea,
    InputGroup,
)
from nitro.html.components.icons import LucideIcon
from nitro.html.components.datepicker import DatePicker
from .fields import get_input_type
from .combobox import render_fk_field


def ModelField(
    field_info: Dict[str, Any],
    error: str = "",
    disabled: bool = False,
    bind: str = "",
) -> HtmlString:
    """Render a form field from Pydantic field metadata.

    Maps field type to appropriate input component and wraps in Field component
    with label, description, and error handling. Binds input to Datastar signal.

    Args:
        field_info: Field metadata dict from get_model_fields()
        signals: Datastar Signals object for binding
        error: Validation error message to display
        disabled: Whether field should be disabled

    Returns:
        HtmlString: Field-wrapped input component with Datastar binding

    Example:
        >>> from nitro.html.components.model_views.fields import get_model_fields
        >>> from rusty_tags.datastar import Signals
        >>> fields = get_model_fields(MyEntity)
        >>> name_field = fields.get('name')
        >>> ModelField(name_field, bind='name')
        <Field with Input type="text" ...> 
    """
    name = field_info['name']
    input_type = get_input_type(field_info)
    extra = field_info.get('extra', {})

    if bind == '':
        bind = f'{field_info["model_name"]}.{name}'

    # Check if this is a foreign key field
    if extra.get('foreign_key'):
        # Render as Combobox for FK fields
        input_elem = render_fk_field(field_info, bind, disabled)
        # FK field already wrapped in Field, return directly
        return Field(
            input_elem,
            label=field_info.get('title', ''),
            label_for=name,
            required=field_info.get('required', False),
            orientation="horizontal" if input_type == 'checkbox' else "vertical",
            error=error,
        )

    # Check for component override
    component_override = extra.get('component')

    # Build the input element based on type
    if component_override == 'textarea' or input_type == 'textarea':
        input_elem = Textarea(
            id=name,
            bind=bind,
            placeholder=field_info.get('description', ''),
            disabled=disabled,
        )
    elif input_type == 'checkbox':
        input_elem = Checkbox(
            field_info.get('title', ''),
            id=name,
            bind=bind,
            disabled=disabled,
        )
    elif input_type == 'select' and field_info.get('enum'):
        input_elem = Select(
            *[SelectOption(opt, value=opt) for opt in field_info['enum']],
            id=name,
            bind=bind,
            placeholder=f"Select {field_info['title']}",
            disabled=disabled,
        )
    elif input_type == 'date':
        input_elem = DatePicker(
            id=name,
            bind=bind,
            disabled=disabled,
        )
    else:
        # Standard input (text, number, email, url, etc.)
        input_attrs = {
            'type': input_type,
            'id': name,
            'bind': bind,
            'placeholder': field_info.get('description', ''),
            'disabled': disabled,
        }

        # Add validation attributes for number fields
        if input_type == 'number':
            # Pydantic converts ge/le to minimum/maximum in JSON schema
            # Check both in extra and at root level
            if 'minimum' in extra:
                input_attrs['min'] = extra['minimum']
            if 'maximum' in extra:
                input_attrs['max'] = extra['maximum']

        # Add string length constraints
        if 'minLength' in extra:
            input_attrs['minlength'] = extra['minLength']
        if 'maxLength' in extra:
            input_attrs['maxlength'] = extra['maxLength']

        # Check for icon
        icon = extra.get('icon')
        if icon:
            # When icon is present, use InputGroup
            # Need to add padding to input for icon space
            input_attrs['cls'] = 'input pl-9'
            input_elem = InputGroup(
                Input(**input_attrs),
                left=LucideIcon(icon, cls="size-4"),
            )
        else:
            input_elem = Input(**input_attrs)

    # Wrap in Field component
    return Field(
        input_elem,
        label=field_info.get('title', '') if input_type != 'checkbox' else '',
        label_for=name if input_type != 'checkbox' else None,
        description=field_info.get('description', '') if not extra.get('icon') else '',
        required=field_info.get('required', False),
        error=error,
    )


def sort_fields(fields: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Sort fields by order attribute, maintaining declaration order for unordered.

    Fields with 'order' in json_schema_extra are sorted first by their order value.
    Fields without 'order' maintain their declaration order and come after ordered fields.

    Args:
        fields: List of field metadata dicts from get_model_fields()

    Returns:
        Sorted list of field metadata dicts

    Example:
        >>> fields = [
        ...     {'name': 'field1', 'extra': {}},
        ...     {'name': 'field2', 'extra': {'order': 1}},
        ...     {'name': 'field3', 'extra': {'order': 0}},
        ... ]
        >>> sorted_fields = sort_fields(fields)
        >>> [f['name'] for f in sorted_fields]
        ['field3', 'field2', 'field1']
    """
    def get_order(field: Dict[str, Any]) -> tuple[int, int]:
        """Get sort key for field.

        Returns tuple (group, order) where:
        - group 0 = has explicit order (sorted first)
        - group 1 = no explicit order (maintains declaration order)
        """
        order = field.get('extra', {}).get('order')
        if order is not None:
            return (0, order)  # Ordered fields come first
        return (1, 0)  # Unordered maintain position

    # Stable sort preserves original order for same keys
    return sorted(fields, key=get_order)
