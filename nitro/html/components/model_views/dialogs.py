"""CRUD Dialog components for model views.

This module provides CRUDDialog and DeleteConfirmDialog components that combine
forms with dialogs for complete CRUD operations.
"""

from typing import Type, List, Dict, Any, Optional, Union, Tuple
from pydantic import BaseModel
from nitro.html.components import (
    Dialog, DialogHeader, DialogTitle, DialogDescription,
    DialogBody, DialogFooter, DialogClose, DialogTrigger,
    AlertDialog, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel,
    Button
)
from rusty_tags import HtmlString, Fragment
from .form import ModelForm


def CRUDDialog(
    entity_class: Type[BaseModel],
    instance: Optional[BaseModel] = None,
    dialog_id: str = "crud-dialog",
    exclude_fields: List[str] = None,
    errors: Dict[str, str] = None,
    on_save: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    include_trigger: bool = False,
    trigger_text: Optional[str] = None,
    trigger_variant: str = "default",
) -> Union[HtmlString, Tuple[HtmlString, HtmlString]]:
    """Generate CRUD dialog with form.

    Args:
        entity_class: BaseModel class for form generation
        instance: BaseModel instance for edit mode (optional)
        dialog_id: Unique dialog ID
        exclude_fields: Fields to exclude from form
        errors: Validation errors dict
        on_save: Datastar expression for save action
        title: Custom dialog title
        description: Dialog description text
        include_trigger: Include DialogTrigger button
        trigger_text: Custom trigger button text
        trigger_variant: Trigger button variant

    Returns:
        Dialog (and optionally DialogTrigger) components

    Example:
        >>> # Create dialog
        >>> dialog = CRUDDialog(User, dialog_id="create-user", on_save="$createUser()")
        >>>
        >>> # Edit dialog
        >>> user = User.get("user-123")
        >>> dialog = CRUDDialog(User, instance=user, on_save="$updateUser('user-123')")
        >>>
        >>> # With trigger button
        >>> trigger, dialog = CRUDDialog(
        ...     User,
        ...     include_trigger=True,
        ...     trigger_text="Add User"
        ... )
    """
    exclude_fields = exclude_fields or ['id']

    # Determine mode and title
    is_edit = instance is not None
    entity_name = entity_class.__name__

    if title is None:
        title = f"{'Edit' if is_edit else 'Create'} {entity_name}"

    if description is None:
        if is_edit:
            description = f"Update the {entity_name.lower()} details below."
        else:
            description = f"Fill in the details to create a new {entity_name.lower()}."

    # Build save action
    save_action = on_save or ""
    if save_action:
        # Chain with dialog close
        save_action = f"{save_action}; document.getElementById('{dialog_id}').close()"

    # Build dialog
    dialog = Dialog(
        DialogHeader(
            DialogTitle(title, id=f"{dialog_id}-title"),
            DialogDescription(description, id=f"{dialog_id}-description"),
        ),
        DialogBody(
            ModelForm(
                entity_class,
                instance=instance,
                exclude_fields=exclude_fields,
                errors=errors,
            ),
            cls="overflow-y-auto scrollbar",
        ),
        DialogFooter(
            DialogClose("Cancel"),
            Button(
                "Save",
                variant="primary",
                on_click=save_action if save_action else None,
            ),
        ),
        id=dialog_id,
    )

    # Optionally include trigger
    if include_trigger:
        if trigger_text is None:
            trigger_text = f"{'Edit' if is_edit else 'Create'} {entity_name}"

        trigger = DialogTrigger(
            trigger_text,
            dialog_id=dialog_id,
            variant=trigger_variant,
        )

        return Fragment(trigger, dialog)

    return dialog


def DeleteConfirmDialog(
    entity_name: str,
    entity_id: str,
    dialog_id: str = "delete-dialog",
    on_confirm: Optional[str] = None,
    title: Optional[str] = None,
    message: Optional[str] = None,
    include_trigger: bool = False,
    trigger_text: Optional[str] = None,
    trigger_variant: str = "default",
) -> HtmlString:
    """Generate delete confirmation dialog.

    Args:
        entity_name: Name of entity type being deleted
        entity_id: ID of entity to delete
        dialog_id: Unique dialog ID
        on_confirm: Datastar expression for delete action
        title: Custom dialog title
        message: Custom confirmation message

    Returns:
        AlertDialog component

    Example:
        >>> # Delete confirmation
        >>> dialog = DeleteConfirmDialog(
        ...     entity_name="User",
        ...     entity_id="user-123",
        ...     on_confirm="$deleteUser('{id}')"
        ... )
        >>>
        >>> # Custom message
        >>> dialog = DeleteConfirmDialog(
        ...     entity_name="Product",
        ...     entity_id="prod-1",
        ...     title="Remove Product?",
        ...     message="This will permanently delete the product from inventory."
        ... )
    """
    if title is None:
        title = f"Delete {entity_name}?"

    if message is None:
        message = (
            f"Are you sure you want to delete this item? "
            # f"Are you sure you want to delete this {entity_name.lower()}? "
            "This action cannot be undone."
        )

    # Build confirm action with ID substitution
    confirm_action = on_confirm or ""
    if confirm_action and '{id}' in confirm_action:
        confirm_action = confirm_action.replace('{id}', entity_id)

    return AlertDialog(
        AlertDialogHeader(
            AlertDialogTitle(title, id=f"{dialog_id}-title"),
            AlertDialogDescription(message, id=f"{dialog_id}-description"),
        ),
        AlertDialogFooter(
            AlertDialogCancel("Cancel"),
            AlertDialogAction(
                "Delete",
                variant="destructive",
                on_click=confirm_action,
            ),
        ),
        id=dialog_id,
    )
