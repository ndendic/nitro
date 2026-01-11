"""ModelForm component - Generate complete forms from BaseModel classes.

This module provides the ModelForm component that generates a full form
from an BaseModel class, combining multiple ModelField components with
Datastar signal management for reactivity.
"""

from typing import Type, List, Dict, Any, Optional
from rusty_tags import Div, HtmlString
from rusty_tags.datastar import Signals
from pydantic import BaseModel
from .fields import get_model_fields
from .model_field import ModelField, sort_fields


def ModelForm(
    entity_class: Type[BaseModel],
    instance: Optional[BaseModel] = None,
    exclude_fields: List[str] = None,
    errors: Dict[str, str] = None,
    signals: Optional[Signals] = None,
    read_only: bool = False,
    cls: str = "",
) -> HtmlString:
    """Generate a complete form from BaseModel class.

    Generates all form fields from entity metadata, creates Datastar signals,
    and handles pre-population, validation errors, and layout options.

    Args:
        entity_class: BaseModel class to generate form for
        instance: BaseModel instance for edit mode (optional)
        exclude_fields: Field names to exclude (default: ['id'])
        errors: Dict of field_name -> error message
        signals: External Signals object (optional)
        orientation: 'vertical' or 'horizontal' layout
        read_only: Disable all inputs
        cls: Additional CSS classes

    Returns:
        Div containing form fields with Datastar signals

    Example:
        >>> # Create mode
        >>> form = ModelForm(User)
        >>>
        >>> # Edit mode
        >>> user = User.get("user-123")
        >>> form = ModelForm(User, instance=user)
        >>>
        >>> # With validation errors
        >>> errors = {'email': 'Invalid email format'}
        >>> form = ModelForm(User, instance=user, errors=errors)
        >>>
        >>> # With external signals
        >>> signals = Signals(name='', email='')
        >>> form = ModelForm(User, signals=signals)
    """
    # Set defaults
    if exclude_fields is None:
        exclude_fields = ['id']
    if errors is None:
        errors = {}

    # Get field metadata
    fields = get_model_fields(entity_class, exclude=exclude_fields)

    # Filter hidden fields
    visible_fields = [
        f for f in fields.values()
        if not f.get('extra', {}).get('hidden_in_form', False)
    ]

    # Sort fields by order attribute
    visible_fields = sort_fields(visible_fields)

    # Create or use signals
    if signals is None:
        if instance:
            # Edit mode: use instance values
            signal_values = {}
            for f in visible_fields:
                field_name = f['name']
                value = getattr(instance, field_name, None)
                # Handle None values appropriately
                if value is None:
                    if f['type'] == 'boolean':
                        signal_values[field_name] = False
                    elif f['type'] in ('integer', 'number'):
                        signal_values[field_name] = 0
                    else:
                        signal_values[field_name] = ''
                else:
                    # Convert dates and enums to strings for Datastar compatibility
                    if hasattr(value, 'isoformat'):
                        # date, datetime, time objects
                        signal_values[field_name] = value.isoformat()
                    elif hasattr(value, 'value'):
                        # Enum objects
                        signal_values[field_name] = value.value
                    else:
                        signal_values[field_name] = value
        else:
            # Create mode: use defaults
            signal_values = {}
            for f in visible_fields:
                field_name = f['name']
                default = f.get('default')

                # Check if default is available
                if default is not None and default != 'PydanticUndefined':
                    signal_values[field_name] = default
                elif f['type'] == 'boolean':
                    signal_values[field_name] = False
                elif f['type'] in ('integer', 'number'):
                    signal_values[field_name] = 0
                else:
                    signal_values[field_name] = ''

        signals = Signals(**signal_values)

    # Build form fields
    form_fields = []
    has_width_fields = any(
        f.get('extra', {}).get('width') for f in visible_fields
    )

    for field in visible_fields:
        field_error = errors.get(field['name'], '')

        # Get width class for grid layout
        width = field.get('extra', {}).get('width', 'full')
        width_class = {
            'full': 'col-span-full',
            'half': 'col-span-1',
            'third': 'col-span-1',
        }.get(width, 'col-span-full')

        field_elem = ModelField(
            field,
            bind=field['name'],
            error=field_error,
            disabled=read_only,
        )

        # Wrap with width class if using grid and field has specific width
        if has_width_fields and width != 'full':
            field_elem = Div(field_elem, cls=width_class)
        elif has_width_fields:
            # Full width fields in grid need col-span-full
            field_elem = Div(field_elem, cls='col-span-full')

        form_fields.append(field_elem)

    # Determine container classes
    if has_width_fields:
        # Use grid if any field has width specified
        container_cls = "grid grid-cols-2 gap-4"
    else:
        # Default vertical layout
        container_cls = "space-y-4"

    # Add custom classes
    if cls:
        container_cls = f"{container_cls} {cls}"

    return Div(
        *form_fields,
        cls=container_cls.strip(),
        signals=signals,
    )


def get_form_values(signals: Signals, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract current form values from signals.

    Utility function for form submission handling.

    Args:
        signals: Datastar Signals object
        fields: List of field metadata dicts

    Returns:
        Dict mapping field names to current signal values

    Example:
        >>> signals = Signals(name='John', email='john@example.com')
        >>> fields = get_model_fields(User)
        >>> values = get_form_values(signals, fields)
        >>> values
        {'name': 'John', 'email': 'john@example.com'}
    """
    return {f['name']: getattr(signals, f['name']) for f in fields}
