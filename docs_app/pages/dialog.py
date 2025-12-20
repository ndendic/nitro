"""Dialog component documentation page"""

from .templates.base import *
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    Dialog,
    DialogTrigger,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogBody,
    DialogFooter,
    DialogClose,
    Button,
)
from nitro.infrastructure.html.components import LucideIcon
from fastapi import APIRouter
from fastapi.requests import Request

router: APIRouter = APIRouter()


def example_basic_dialog() -> HtmlString:
    """Basic dialog following Basecoat UI patterns."""
    return Div(
        DialogTrigger(
            "Open Dialog",
            dialog_id="basic-dialog",
        ),
        Dialog(
            DialogHeader(
                DialogTitle("Dialog Title", id="basic-dialog-title"),                
                DialogDescription(
                    "This is a basic dialog using native HTML dialog element with proper accessibility.",
                    id="basic-dialog-description",
                ),
                
            ),
            DialogBody(
                P("The dialog component follows Basecoat UI patterns:"),
                Ul(
                    Li("Uses native HTML <dialog> element"),
                    Li("Proper ARIA attributes for accessibility"),
                    Li("Keyboard support (ESC to close)"),
                    Li("Backdrop click to close"),
                    Li("Focus management handled by browser"),
                ),
            ),
            DialogFooter(
                Button(
                    "Cancel",
                    onclick="this.closest('dialog').close()",
                ),
                Button(
                    "Confirm",
                    onclick="console.log('Confirmed'); this.closest('dialog').close()",
                ),
            ),
            DialogClose(
                LucideIcon("x"),
                dialog_id="basic-dialog",
                aria_label="Close dialog",
            ),
            id="basic-dialog",
        ),
        cls="flex gap-4",
    )


def example_custom_dialog() -> HtmlString:
    """Dialog with form content."""
    return Div(
        DialogTrigger(
            LucideIcon("mail"),
            " Compose Message",
            dialog_id="compose-dialog",
        ),
        Dialog(
            DialogHeader(
                DialogTitle("Compose Message", id="compose-dialog-title"),
                DialogDescription(
                    "Send a message to your team.",
                    id="compose-dialog-description",
                ),                
            ),
            DialogBody(
                Div(
                    Input(
                        id="subject-input",
                        placeholder="Enter subject",
                        label="Subject",
                        autofocus=True,
                        cls="field mb-4",
                    ),
                ),
                Div(
                    Label("Message", _for="message-input"),
                    Textarea(
                        id="message-input",
                        rows=4,
                        placeholder="Type your message here",
                    ),
                    cls="field mb-4"
                ),
                cls="overflow-y-auto scrollbar",
            ),
            DialogFooter(
                Button(
                    "Cancel",
                    onclick="this.closest('dialog').close()",
                ),
                Button(
                    LucideIcon("send", size=16),
                    " Send",
                    onclick="console.log('Message sent'); this.closest('dialog').close()",
                ),
            ),
            DialogClose(
                LucideIcon("x"),
                dialog_id="compose-dialog",
                aria_label="Close dialog",
            ),
            id="compose-dialog",
        ),
        cls="flex gap-4",
    )


def example_confirm_dialog() -> HtmlString:
    """Confirmation dialog with destructive action."""
    return Div(
        DialogTrigger(
            LucideIcon("trash-2"),
            " Delete File",
            dialog_id="delete-dialog",
        ),
        Dialog(
            DialogHeader(
                DialogTitle("Delete File?", id="delete-dialog-title"),
                DialogDescription(
                    "This action cannot be undone. The file will be permanently deleted.",
                    id="delete-dialog-description",
                ),
            ),
            DialogBody(
                P("Are you sure you want to delete this file? All data will be lost permanently."),
            ),
            DialogFooter(
                Button(
                    "Cancel",
                    onclick="this.closest('dialog').close()",
                ),
                Button(
                    LucideIcon("trash-2", size=16),
                    " Delete",
                    onclick="console.log('File deleted'); this.closest('dialog').close()",
                    variant="destructive",
                ),
            ),
            DialogClose(
                LucideIcon("x"),
                dialog_id="delete-dialog",
                aria_label="Close dialog",
            ),
            id="delete-dialog",
        ),
        cls="flex gap-4",
    )


page = Div(
        H1("Dialog Component"),
        P(
            "A modal dialog component using native HTML &lt;dialog&gt; element following ",
            "Basecoat UI patterns with proper accessibility and keyboard support."
        ),

        TitledSection(
            "Design Philosophy",
            P("Dialog provides modal overlays following Basecoat UI patterns:"),
            Ul(
                Li("Native HTML &lt;dialog&gt; element - proper semantics and browser support"),
                Li("Accessibility first - ARIA attributes and keyboard navigation"),
                Li("Focus management - handled by the browser automatically"),
                Li("Backdrop interaction - click outside to close"),
                Li("ESC key support - native keyboard closing"),
                Li("Simple API - minimal complexity, maximum functionality"),
            ),
        ),

        TitledSection(
            "Basic Dialog",
            P("A simple dialog with title, description, and action buttons."),
            ComponentShowcase(example_basic_dialog),
        ),

        TitledSection(
            "Dialog with Form",
            P("Dialog containing form inputs for data collection."),
            ComponentShowcase(example_custom_dialog),
        ),

        TitledSection(
            "Confirmation Dialog",
            P("Destructive action confirmation with clear messaging."),
            ComponentShowcase(example_confirm_dialog),
        ),

        TitledSection(
            "API Reference",
            CodeBlock(
                """
# Dialog - Modal container using native dialog element
def Dialog(
    *children,              # DialogHeader, DialogBody, DialogFooter
    id: str,                # Required - unique dialog identifier
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogTrigger - Button that opens the dialog
def DialogTrigger(
    *children,              # Button content
    dialog_id: str,         # ID of the dialog to open
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional button attributes
) -> HtmlString

# DialogHeader - Contains title and description
def DialogHeader(
    *children,              # DialogTitle, DialogDescription, DialogClose
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogTitle - Dialog heading
def DialogTitle(
    *children,              # Title text
    id: str = None,         # For aria-labelledby (pattern: {dialog_id}-title)
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogDescription - Dialog description text
def DialogDescription(
    *children,              # Description text
    id: str = None,         # For aria-describedby (pattern: {dialog_id}-description)
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogBody - Main content area
def DialogBody(
    *children,              # Body content
    cls: str = "",          # Additional CSS classes (use 'overflow-y-auto' for scrolling)
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogFooter - Contains action buttons
def DialogFooter(
    *children,              # Action buttons
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional HTML attributes
) -> HtmlString

# DialogClose - Button that closes the dialog
def DialogClose(
    *children,              # Button content
    dialog_id: str,         # ID of the dialog (for backward compatibility)
    cls: str = "",          # Additional CSS classes
    **attrs                 # Additional button attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),

        TitledSection(
            "Key Behaviors",
            P("The dialog component follows Basecoat UI patterns:"),
            Ul(
                Li("Opens with showModal() - proper modal behavior with focus trapping"),
                Li("Closes with this.closest('dialog').close() - flexible and simple"),
                Li("ESC key automatically closes the dialog (native browser behavior)"),
                Li("Clicking backdrop closes the dialog (onclick handler)"),
                Li("Focus returns to trigger when closed (native browser behavior)"),
                Li("Proper ARIA attributes for screen readers"),
            ),
        ),

        TitledSection(
            "Accessibility",
            P("Built-in accessibility following Basecoat UI standards:"),
            Ul(
                Li("Native &lt;dialog&gt; element - proper semantics"),
                Li("aria-modal='true' - indicates modal behavior"),
                Li("aria-labelledby - links to dialog title"),
                Li("aria-describedby - links to dialog description"),
                Li("aria-haspopup='dialog' on trigger button"),
                Li("aria-label on close button for screen readers"),
                Li("Focus management handled automatically by browser"),
                Li("Keyboard navigation (ESC, Tab) works out of the box"),
            ),
        ),

        TitledSection(
            "CSS Classes",
            P("The dialog includes Basecoat UI recommended classes:"),
            Ul(
                Li("dialog - base styling class"),
                Li("w-full - full width on mobile"),
                Li("sm:max-w-[425px] - max width on small screens and above"),
                Li("max-h-[612px] - maximum height with scrolling"),
                Li("overflow-y-auto scrollbar - for scrollable body content"),
            ),
        ),

        BackLink(),
        id="content"
    )

@router.get("/xtras/dialog")
@template(title="Dialog Component Documentation")
def dialog_page():
    return page

@on("page.dialog")
async def get_dialog(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.dialog")