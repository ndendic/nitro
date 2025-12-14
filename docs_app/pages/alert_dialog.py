"""Alert Dialog component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi import APIRouter

from nitro.infrastructure.html.components import (
    AlertDialog,
    AlertDialogTrigger,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogAction,
    AlertDialogCancel,
    Button,
    LucideIcon,
)

router: APIRouter = APIRouter()


def example_basic():
    """Basic confirmation dialog."""
    return Div(
        AlertDialogTrigger(
            "Show Dialog",
            dialog_id="basic-alert",
            variant="outline",
        ),
        AlertDialog(
            AlertDialogHeader(
                AlertDialogTitle("Are you absolutely sure?", id="basic-alert-title"),
                AlertDialogDescription(
                    "This action cannot be undone. This will permanently delete your account and remove your data from our servers.",
                    id="basic-alert-description",
                ),
            ),
            AlertDialogFooter(
                AlertDialogCancel("Cancel", dialog_id="basic-alert"),
                AlertDialogAction("Continue", dialog_id="basic-alert"),
            ),
            id="basic-alert",
        ),
        cls="flex gap-4",
    )


def example_destructive():
    """Destructive action confirmation."""
    return Div(
        AlertDialogTrigger(
            LucideIcon("trash-2"),
            " Delete Account",
            dialog_id="delete-alert",
            variant="destructive",
        ),
        AlertDialog(
            AlertDialogHeader(
                AlertDialogTitle("Delete Account", id="delete-alert-title"),
                AlertDialogDescription(
                    "Are you sure you want to delete your account? All of your data will be permanently removed. This action cannot be undone.",
                    id="delete-alert-description",
                ),
            ),
            AlertDialogFooter(
                AlertDialogCancel("Cancel", dialog_id="delete-alert"),
                AlertDialogAction(
                    "Yes, delete my account",
                    dialog_id="delete-alert",
                    variant="destructive",
                    on_click="console.log('Account deleted!')",
                ),
            ),
            id="delete-alert",
        ),
        cls="flex gap-4",
    )


def example_with_form():
    """Alert dialog with additional confirmation input."""
    return Div(
        AlertDialogTrigger(
            "Delete Project",
            dialog_id="form-alert",
            variant="outline",
        ),
        AlertDialog(
            AlertDialogHeader(
                AlertDialogTitle("Delete Project?", id="form-alert-title"),
                AlertDialogDescription(
                    "This will permanently delete the project and all associated data. Type 'DELETE' to confirm.",
                    id="form-alert-description",
                ),
            ),
            Div(
                Input(
                    type="text",
                    placeholder="Type DELETE to confirm",
                    cls="input w-full",
                ),
                cls="py-4",
            ),
            AlertDialogFooter(
                AlertDialogCancel("Cancel", dialog_id="form-alert"),
                AlertDialogAction(
                    "Delete Project",
                    dialog_id="form-alert",
                    variant="destructive",
                    on_click="console.log('Project deleted!')",
                ),
            ),
            id="form-alert",
        ),
        cls="flex gap-4",
    )


def example_custom_buttons():
    """Custom button variants and text."""
    return Div(
        AlertDialogTrigger(
            "Save Changes?",
            dialog_id="save-alert",
            variant="primary",
        ),
        AlertDialog(
            AlertDialogHeader(
                AlertDialogTitle("Unsaved Changes", id="save-alert-title"),
                AlertDialogDescription(
                    "You have unsaved changes. Would you like to save them before leaving?",
                    id="save-alert-description",
                ),
            ),
            AlertDialogFooter(
                AlertDialogCancel("Discard", dialog_id="save-alert"),
                AlertDialogAction(
                    "Save Changes",
                    dialog_id="save-alert",
                    variant="primary",
                    on_click="console.log('Changes saved!')",
                ),
            ),
            id="save-alert",
        ),
        cls="flex gap-4",
    )


@router.get("/xtras/alert-dialog")
@template(title="Alert Dialog Component Documentation")
def alert_dialog_docs():
    return Div(
        H1("Alert Dialog Component"),
        P(
            "A modal dialog component for important confirmations that requires user "
            "acknowledgment. Uses native HTML &lt;dialog&gt; element with showModal() for "
            "proper focus management and backdrop interaction."
        ),
        Section(
            "Design Philosophy",
            P("Alert Dialog provides interrupt-style confirmations:"),
            Ul(
                Li("Modal behavior - blocks interaction with background content"),
                Li("Native HTML &lt;dialog&gt; - proper accessibility and focus management"),
                Li("Focus trap - keyboard navigation stays within the dialog"),
                Li("Escape key closes - standard keyboard behavior"),
                Li("Backdrop click closes - optional click-outside behavior"),
            ),
        ),
        Section(
            "Basic Usage",
            P("A simple confirmation dialog with cancel and continue actions:"),
            ComponentShowcase(example_basic),
        ),
        Section(
            "Destructive Actions",
            P("Use destructive variant for dangerous actions like deletion:"),
            ComponentShowcase(example_destructive),
        ),
        Section(
            "With Form Content",
            P("Add custom content like confirmation inputs:"),
            ComponentShowcase(example_with_form),
        ),
        Section(
            "Custom Buttons",
            P("Customize button variants and text for different contexts:"),
            ComponentShowcase(example_custom_buttons),
        ),
        Section(
            "API Reference",
            CodeBlock(
                """
# AlertDialog - Modal container using native dialog element
def AlertDialog(
    *children,              # AlertDialogHeader, custom content, AlertDialogFooter
    id: str,                # Required - unique dialog identifier
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogTrigger - Button that opens the dialog
def AlertDialogTrigger(
    *children,              # Button content
    dialog_id: str,         # ID of the dialog to open
    cls: str = "",          # Additional CSS classes
    **attrs                 # Passed to Button component
) -> HtmlString

# AlertDialogHeader - Contains title and description
def AlertDialogHeader(
    *children,              # AlertDialogTitle, AlertDialogDescription
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogTitle - Dialog heading
def AlertDialogTitle(
    *children,              # Title text
    id: str = None,         # For aria-labelledby
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogDescription - Dialog description text
def AlertDialogDescription(
    *children,              # Description text
    id: str = None,         # For aria-describedby
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogFooter - Contains action buttons
def AlertDialogFooter(
    *children,              # AlertDialogCancel, AlertDialogAction
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogAction - Confirm/proceed button
def AlertDialogAction(
    *children,              # Button content
    dialog_id: str,         # ID of the dialog
    on_click: str = "",     # Additional action to perform
    variant: str = "default",  # Button variant
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# AlertDialogCancel - Cancel button (closes dialog)
def AlertDialogCancel(
    *children,              # Button content (defaults to "Cancel")
    dialog_id: str,         # ID of the dialog
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        Section(
            "Key Behaviors",
            Ul(
                Li("Opens with showModal() - proper modal behavior"),
                Li("Focus trapped inside dialog"),
                Li("Escape key closes dialog"),
                Li("Clicking backdrop closes dialog"),
                Li("Action buttons close after executing their handler"),
            ),
        ),
        Section(
            "Accessibility",
            Ul(
                Li("Uses native &lt;dialog&gt; element for proper semantics"),
                Li("role='alertdialog' for screen readers"),
                Li("aria-modal='true' indicates modal behavior"),
                Li("aria-labelledby references the title"),
                Li("aria-describedby references the description"),
                Li("Focus management handled by browser"),
            ),
        ),
        BackLink(),
    )
