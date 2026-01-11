"""Combobox component for model_views with foreign key field integration.

This module provides a wrapper around the base Combobox component to integrate
with Pydantic BaseModel foreign key fields, automatically loading related entity
options and rendering searchable dropdowns.
"""

from typing import Any, List, Dict, Optional, Type, Callable
from rusty_tags import HtmlString
from rusty_tags.datastar import Signals
from nitro.html.components.combobox import (
    Combobox as BaseCombobox,
    ComboboxItem,
)
from pydantic import BaseModel


def get_related_entity_class(foreign_key: str) -> Type[BaseModel]:
    """Get BaseModel class from foreign_key string.

    Resolves the BaseModel class referenced in a foreign_key field metadata.
    Supports both __tablename__ matching and class name matching.

    Args:
        foreign_key: String like 'users.id', 'category.id', or 'User.id'

    Returns:
        BaseModel class for the related model

    Raises:
        ValueError: If no BaseModel class matches the foreign_key string

    Example:
        >>> # For FK 'users.id', finds BaseModel with __tablename__ = 'users'
        >>> UserClass = get_related_entity_class('users.id')
        >>> # For FK 'Category.id', finds BaseModel class named Category
        >>> CategoryClass = get_related_entity_class('Category.id')
    """
    # Parse the foreign key string - format is 'table_name.field'
    table_name = foreign_key.split('.')[0]

    # Try finding by __tablename__ first (most reliable)
    for subclass in BaseModel.__subclasses__():
        if hasattr(subclass, '__tablename__') and subclass.__tablename__ == table_name:
            return subclass

    # Fallback: Try matching class name (case-insensitive)
    for subclass in BaseModel.__subclasses__():
        if subclass.__name__.lower() == table_name.lower():
            return subclass

    # No match found
    raise ValueError(f"Could not find BaseModel class for foreign_key: {foreign_key}")


def render_fk_field(
    field_info: Dict[str, Any],
    bind: str,
    disabled: bool = False,
) -> HtmlString:
    """Render a foreign key field as Combobox.

    Automatically loads options from the related BaseModel class and creates
    a searchable Combobox component with proper label/value mapping.

    Args:
        field_info: Field metadata dict from get_model_fields()
        bind: Datastar signal name for binding
        disabled: Whether to disable the combobox

    Returns:
        Combobox component with related entity options

    Raises:
        ValueError: If field does not have foreign_key metadata

    Example:
        >>> field_info = {
        ...     'name': 'author_id',
        ...     'title': 'Author',
        ...     'extra': {
        ...         'foreign_key': 'users.id',
        ...         'display_field': 'name',
        ...     }
        ... }
        >>> signals = Signals(author_id='')
        >>> render_fk_field(field_info, signals)
        <Combobox with user options...>
    """
    name = field_info['name']
    extra = field_info.get('extra', {})
    foreign_key = extra.get('foreign_key')

    if not foreign_key:
        raise ValueError(f"Field {name} does not have foreign_key metadata")

    # Get related BaseModel class
    related_entity = get_related_entity_class(foreign_key)

    # Determine display field (default to 'id')
    display_field = extra.get('display_field', 'id')

    # Load options from related entity
    entities = related_entity.all()

    # Build ComboboxItem elements
    items = [
        ComboboxItem(
            getattr(entity, display_field, entity.id),
            value=entity.id,
        )
        for entity in entities
    ]

    return BaseCombobox(
        *items,
        id=name,
        bind=bind,
        placeholder=f"Select {field_info.get('title', name)}...",
        empty_text="No options available",
        cls="w-full",
    )


def Combobox(
    *children: Any,
    options: Optional[List[Dict[str, Any]]] = None,
    id: Optional[str] = None,
    bind: Any = None,
    placeholder: str = "Select...",
    empty_text: str = "No results found",
    display_key: str = "label",
    value_key: str = "value",
    searchable: bool = True,
    clearable: bool = True,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Combobox wrapper that accepts options list for convenience.

    Provides a simpler interface for creating comboboxes from option dicts,
    automatically converting them to ComboboxItem elements.

    Args:
        *children: ComboboxItem elements (if options not provided)
        options: List of option dicts with label/value keys
        id: Unique identifier
        bind: Datastar signal for selected value
        placeholder: Placeholder text
        empty_text: Text to show when no items match
        display_key: Key for display text in option dict
        value_key: Key for value in option dict
        searchable: Enable search filtering (always True in base component)
        clearable: Show clear button (not used - for interface compatibility)
        disabled: Disable interaction (not used - for interface compatibility)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Combobox component with dropdown

    Example:
        >>> options = [
        ...     {'value': '1', 'label': 'Option 1'},
        ...     {'value': '2', 'label': 'Option 2'},
        ... ]
        >>> Combobox(options=options, bind='selected')
    """
    # If options provided, convert to ComboboxItem elements
    if options:
        items = [
            ComboboxItem(
                opt.get(display_key, str(opt)),
                value=opt.get(value_key, opt),
            )
            for opt in options
        ]
    else:
        items = list(children)

    return BaseCombobox(
        *items,
        id=id,
        bind=bind,
        placeholder=placeholder,
        empty_text=empty_text,
        cls=cls,
        **attrs,
    )
