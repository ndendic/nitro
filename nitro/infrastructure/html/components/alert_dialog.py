"""Alert Dialog component for confirmation dialogs.

A modal dialog component for important confirmations that requires user
acknowledgment. Uses native HTML <dialog> element with showModal() for
proper focus management and backdrop interaction.
"""

from typing import Any, Optional
from rusty_tags import Div, Header, Footer, H2, P, HtmlString
from rusty_tags import Dialog as NativeDialog
from rusty_tags.datastar import Signals
from .button import Button
from .utils import cn
from .button import ButtonVariant


def AlertDialog(
    *children: Any,
    id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Alert dialog container using native HTML <dialog> element.

    Creates a modal dialog that blocks background interaction and requires
    user acknowledgment. Uses showModal() for proper focus trapping.

    Args:
        *children: AlertDialogHeader and AlertDialogFooter components
        id: Unique identifier for the dialog (required)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        Complete alert dialog structure

    Example:
        AlertDialog(
            AlertDialogHeader(
                AlertDialogTitle("Are you sure?"),
                AlertDialogDescription("This action cannot be undone."),
            ),
            AlertDialogFooter(
                AlertDialogCancel("Cancel", dialog_id="confirm-delete"),
                AlertDialogAction("Delete", dialog_id="confirm-delete"),
            ),
            id="confirm-delete",
        )
    """
    signal_name = f"{id.replace('-', '_')}_open"

    return NativeDialog(
        Div(
            *children,
            role="alertdialog",
            aria_modal="true",
            aria_labelledby=f"{id}-title",
            aria_describedby=f"{id}-description",
        ),
        id=id,
        cls=cn("dialog", cls),
        signals=Signals(**{signal_name: False}),
        # Close on backdrop click (clicking the dialog element itself, not content)
        data_on_click="if (event.target === this) this.close()",
        **attrs,
    )


def AlertDialogTrigger(
    *children: Any,
    dialog_id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that opens an alert dialog.

    Uses showModal() to open the dialog in modal mode with backdrop
    and focus trapping.

    Args:
        *children: Button content
        dialog_id: ID of the alert dialog to open
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button element that triggers the dialog

    Example:
        AlertDialogTrigger("Delete Account", dialog_id="confirm-delete")
    """
    return Button(
        *children,
        cls=cls,
        aria_haspopup="dialog",
        aria_controls=dialog_id,
        on_click=f"document.getElementById('{dialog_id}').showModal()",
        **attrs,
    )


def AlertDialogHeader(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Header section for alert dialog.

    Contains the title and description. Styled according to Basecoat
    dialog patterns.

    Args:
        *children: AlertDialogTitle and AlertDialogDescription
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


def AlertDialogTitle(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Title element for alert dialog.

    Should be placed inside AlertDialogHeader. The id is used for
    aria-labelledby reference.

    Args:
        *children: Title content
        id: Element ID (auto-generated from parent dialog if not provided)
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


def AlertDialogDescription(
    *children: Any,
    id: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Description text for alert dialog.

    Should be placed inside AlertDialogHeader. Provides additional
    context for the user's decision.

    Args:
        *children: Description content
        id: Element ID (auto-generated from parent dialog if not provided)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        P element for the dialog description
    """
    return P(
        *children,
        id=id,
        cls=cn(cls),
        **attrs,
    )


def AlertDialogFooter(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Footer section for alert dialog actions.

    Contains AlertDialogCancel and AlertDialogAction buttons.
    Styled according to Basecoat dialog patterns.

    Args:
        *children: Action and cancel buttons
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


def AlertDialogAction(
    *children: Any,
    variant: ButtonVariant = "default",
    on_click: str = "",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Action button for alert dialog (confirm/proceed).

    Typically used for the primary action the user is confirming.
    Closes the dialog after executing the action.

    Args:
        *children: Button content
        variant: Button variant
        on_click: Additional action to perform on click
        variant: Button variant (default, destructive, etc.)
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button element for the action

    Example:
        AlertDialogAction("Delete", variant="destructive")
    """
    # Combine user action with dialog close
    close_action = "el.closest('dialog').close()"
    combined_action = f"{on_click}; {close_action}" if on_click else close_action

    return Button(
        *children,
        variant=variant,
        cls=cls,
        on_click=combined_action,
        **attrs,
    )


def AlertDialogCancel(
    *children: Any,
    cls: str = "",
    variant: ButtonVariant = "outline",
    **attrs: Any,
) -> HtmlString:
    """Cancel button for alert dialog.

    Closes the dialog without performing any action.
    Styled with outline variant by default.

    Args:
        *children: Button content (defaults to "Cancel" if empty)
        variant: Button variant
        cls: Additional CSS classes
        **attrs: Additional button attributes

    Returns:
        Button element for cancel action

    Example:
        AlertDialogCancel("Never mind", variant="outline")
    """
    content = children if children else ("Cancel",)

    return Button(
        *content,
        variant=variant,
        cls=cls,
        onclick="this.closest('dialog').close()",
        **attrs,
    )
