"""ModelCard component for displaying entity data in card format.

Provides read-only display of entity fields with formatting, grouping,
and optional action buttons.
"""

from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel
from nitro.html.components import (
    Card, CardHeader, CardTitle, CardDescription,
    CardContent, CardFooter, Button, Badge
)
from rusty_tags import Div, Span, Dl, Dt, Dd, HtmlString
from .fields import get_model_fields


def ModelCard(
    entity_class: Type[BaseModel],
    instance: BaseModel,
    exclude_fields: Optional[List[str]] = None,
    title_field: Optional[str] = None,
    description_field: Optional[str] = None,
    actions: Optional[List[str]] = None,
    on_edit: Optional[str] = None,
    on_delete: Optional[str] = None,
    variant: str = "default",
    cls: str = "",
) -> HtmlString:
    """Display entity data in a Card component.

    Renders entity fields as a read-only card with optional title,
    description, and action buttons. Supports field grouping and
    type-based formatting.

    Args:
        entity_class: BaseModel class for field metadata
        instance: BaseModel instance to display
        exclude_fields: Fields to exclude (default: ['id'])
        title_field: Field to use as card title
        description_field: Field to use as description
        actions: List of actions ['edit', 'delete']
        on_edit: Datastar expression for edit action
        on_delete: Datastar expression for delete action
        variant: Card variant ('default', 'elevated', 'outline')
        cls: Additional CSS classes

    Returns:
        Card component with entity data

    Example:
        user = User.get("user-123")
        card = ModelCard(
            User,
            instance=user,
            title_field='name',
            actions=['edit', 'delete'],
            on_edit="$openEdit('{id}')",
        )
    """
    exclude_fields = exclude_fields or ['id']
    actions = actions or []

    # Get field metadata
    fields = get_model_fields(entity_class, exclude=exclude_fields)

    # Filter hidden fields
    visible_fields = [
        f for f in fields.values()
        if not f.get('extra', {}).get('hidden_in_card', False)
    ]

    # Extract title and description
    card_title = None
    card_description = None

    if title_field:
        card_title = str(getattr(instance, title_field, ''))
        # Remove from visible fields
        visible_fields = [f for f in visible_fields if f['name'] != title_field]

    if description_field:
        card_description = str(getattr(instance, description_field, ''))
        visible_fields = [f for f in visible_fields if f['name'] != description_field]

    # Group fields if grouping metadata exists
    grouped_fields = group_fields(visible_fields)

    # Build field display elements
    content_elements = []

    for group_name, group_fields_list in grouped_fields.items():
        # Add group header if named
        if group_name:
            content_elements.append(
                Div(group_name, cls="text-sm font-medium text-muted-foreground mt-4 mb-2 first:mt-0")
            )

        # Add fields as definition list
        dl_items = []
        for field in group_fields_list:
            value = getattr(instance, field['name'], None)
            formatted = format_display_value(value, field)

            dl_items.extend([
                Dt(field['title'], cls="text-sm font-medium text-muted-foreground"),
                Dd(formatted, cls="text-sm mb-3"),
            ])

        content_elements.append(Dl(*dl_items))

    # Build action buttons
    footer_buttons = []
    if 'edit' in actions and on_edit:
        edit_action = on_edit.replace('{id}', str(instance.id))
        footer_buttons.append(
            Button("Edit", variant="outline", size="sm", on_click=edit_action)
        )
    if 'delete' in actions and on_delete:
        delete_action = on_delete.replace('{id}', str(instance.id))
        footer_buttons.append(
            Button("Delete", variant="destructive", size="sm", on_click=delete_action)
        )

    # Build card components
    header_component = None
    if card_title or card_description:
        header_children = []
        if card_title:
            header_children.append(CardTitle(card_title))
        if card_description:
            header_children.append(CardDescription(card_description))
        header_component = CardHeader(*header_children)

    footer_component = None
    if footer_buttons:
        footer_component = CardFooter(
            Div(*footer_buttons, cls="flex gap-2")
        )

    # Build final card
    card_children = []
    if header_component:
        card_children.append(header_component)
    card_children.append(CardContent(*content_elements))
    if footer_component:
        card_children.append(footer_component)

    return Card(
        *card_children,
        variant=variant,
        cls=cls,
    )


def group_fields(fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group fields by their 'group' metadata.

    Organizes fields into groups based on json_schema_extra['group'].
    Fields without a group are placed under the empty string key.

    Args:
        fields: List of field metadata dicts

    Returns:
        Dict with group names as keys, field lists as values.
        Empty string key contains ungrouped fields.

    Example:
        fields = [
            {'name': 'f1', 'extra': {'group': 'Basic'}},
            {'name': 'f2', 'extra': {}},
        ]
        result = group_fields(fields)
        # {'Basic': [f1], '': [f2]}
    """
    groups = {'': []}

    for field in fields:
        group = field.get('extra', {}).get('group', '')
        if group not in groups:
            groups[group] = []
        groups[group].append(field)

    return groups


def format_display_value(value: Any, field: Dict[str, Any]) -> Any:
    """Format value for read-only display.

    Applies type-specific formatting for better display:
    - None -> dash placeholder
    - Boolean -> Yes/No badge
    - Enum -> outline badge
    - Date -> formatted string
    - Email/URL -> styled text

    Args:
        value: Field value from entity instance
        field: Field metadata dict

    Returns:
        Formatted value (string or HTML component)

    Example:
        field = {'type': 'boolean'}
        format_display_value(True, field)  # Badge("Yes")
    """
    if value is None:
        return Span("-", cls="text-muted-foreground")

    field_type = field.get('type')
    extra = field.get('extra', {})

    # Boolean formatting
    if field_type == 'boolean':
        if value:
            return Badge("Yes", variant="default")
        else:
            return Badge("No", variant="secondary")

    # Enum formatting
    if field.get('enum'):
        # Use outline badge for enum values
        return Badge(str(value), variant="outline")

    # Date formatting
    if field.get('format') == 'date':
        if hasattr(value, 'strftime'):
            return value.strftime('%B %d, %Y')
        return str(value)

    if field.get('format') == 'date-time':
        if hasattr(value, 'strftime'):
            return value.strftime('%B %d, %Y at %H:%M')
        return str(value)

    # Currency formatting
    if extra.get('format') == 'currency':
        return f"${value:,.2f}"

    # Email formatting
    if field.get('format') == 'email':
        return Span(str(value), cls="text-primary underline")

    # URL formatting
    if field.get('format') == 'uri':
        return Span(str(value), cls="text-primary underline truncate")

    # Default: string
    return str(value)
