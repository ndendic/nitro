"""Dialog component following Basecoat UI patterns.

A modal dialog component using native HTML <dialog> element with proper
accessibility attributes and keyboard support.
"""

from typing import Any, Optional
from rusty_tags import Div, Header, Footer, H2, HtmlString, P
from rusty_tags import Dialog as NativeDialog
from .utils import cn
from .button import Button, ButtonVariant

def Dialog(
    *children: Any,
    id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Dialog container using native HTML <dialog> element.

    Creates a modal dialog following Basecoat UI patterns with proper
    accessibility attributes and backdrop interaction.

    Args:
        *children: DialogHeader, DialogBody, DialogFooter components
        id: Unique identifier for the dialog (required)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete dialog structure

    Example:
        Dialog(
            DialogHeader(
                DialogTitle("Edit Profile", id="profile-title"),
                DialogDescription("Make changes to your profile.", id="profile-desc"),
                DialogClose(dialog_id="profile-dialog"),
            ),
            DialogBody(
                # Form fields here
            ),
            DialogFooter(
                Button("Cancel", on_click="this.closest('dialog').close()"),
                Button("Save", variant="primary"),
            ),
            id="profile-dialog",
        )
    """
    return NativeDialog(
        Div(
            *children,
            role="document",
        ),
        id=id,
        cls=cn("dialog w-full sm:max-w-[425px] max-h-[612px]", cls),
        aria_modal="true",
        aria_labelledby=f"{id}-title",
        aria_describedby=f"{id}-description",
        # Close on backdrop click (clicking the dialog element itself, not content)
        onclick="if (event.target === this) this.close()",
        **attrs,
    )


def DialogTrigger(
    *children: Any,
    dialog_id: str,
    cls: str = "",
    variant: ButtonVariant = "outline",
    **attrs: Any,
) -> HtmlString:
    """Button that opens a dialog.

    Uses showModal() to open the dialog in modal mode with backdrop
    and focus trapping following Basecoat UI patterns.

    Args:
        *children: Button content
        dialog_id: ID of the dialog to open
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button element that triggers the dialog

    Example:
        DialogTrigger("Open Dialog", dialog_id="my-dialog")
    """
    button_attrs = dict(attrs)
    button_attrs["type"] = button_attrs.get("type", "button")
    button_attrs["aria_haspopup"] = "dialog"
    button_attrs["aria_controls"] = dialog_id
    button_attrs["onclick"] = f"document.getElementById('{dialog_id}').showModal()"
    button_attrs["cls"] = cls

    return Button(*children, variant=variant, **button_attrs)


def DialogHeader(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Header section for dialog.

    Contains the title and optional description following Basecoat UI patterns.

    Args:
        *children: DialogTitle and optional DialogDescription
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Header element for the dialog
    """
    return Header(
        *children,
        cls=cn(cls),
        **attrs,
    )


def DialogTitle(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Title element for dialog.

    Should be placed inside DialogHeader. The id is used for
    aria-labelledby reference following Basecoat UI patterns.

    Args:
        *children: Title content
        id: Element ID (should match pattern: {dialog_id}-title)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        H2 element for the dialog title
    """
    return H2(
        *children,
        id=id,
        cls=cn(cls),
        **attrs,
    )


def DialogDescription(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Description text for dialog.

    Should be placed inside DialogHeader. Provides additional
    context for the dialog following Basecoat UI patterns.

    Args:
        *children: Description content
        id: Element ID (should match pattern: {dialog_id}-description)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Div element for the dialog description
    """
    return P(
        *children,
        id=id,
        cls=cn(cls),
        **attrs,
    )


def DialogBody(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Body section for dialog content.

    Main content area with automatic scrolling for overflow following
    Basecoat UI patterns. Use overflow-y-auto for scrollable content.

    Args:
        *children: Body content
        cls: Additional CSS classes (consider 'overflow-y-auto scrollbar')
        **attrs: Additional HTML attributes

    Returns:
        Div element for the dialog body
    """
    return Div(
        *children,
        cls=cn(cls),
        **attrs,
    )


def DialogFooter(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Footer section for dialog actions.

    Contains action buttons following Basecoat UI patterns.

    Args:
        *children: Action buttons
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Footer element for the dialog
    """
    return Footer(
        *children,
        cls=cn(cls),
        **attrs,
    )


def DialogClose(
    *children: Any,
    variant: ButtonVariant = "outline",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that closes a dialog.

    Uses this.closest('dialog').close() following Basecoat UI patterns
    for more flexible dialog closing without needing to know the dialog ID.

    Args:
        *children: Button content
        dialog_id: ID of the dialog (kept for backward compatibility)
        variant: Button variant
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button element for closing the dialog

    Example:
        DialogClose("×", dialog_id="my-dialog", aria_label="Close dialog")
    """
    button_attrs = dict(attrs)
    button_attrs["type"] = button_attrs.get("type", "button")
    button_attrs["onclick"] = "this.closest('dialog').close()"
    button_attrs["cls"] = cls

    return Button(*children, variant=variant, **button_attrs)