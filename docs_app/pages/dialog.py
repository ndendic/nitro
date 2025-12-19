"""Dialog component documentation page"""

from .templates.base import *
from nitro.infrastructure.events import on, emit_elements
from nitro.infrastructure.html.components import (
    Dialog,
    DialogTrigger,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogBody,
    DialogFooter,
    DialogClose,
)
from nitro.infrastructure.html.components import LucideIcon
from fastapi import APIRouter
from fastapi.requests import Request

router: APIRouter = APIRouter()


def example_basic_dialog() -> HtmlString:
    return Div(
        DialogTrigger(
            "Open basic dialog",
            dialog_id="basic_dialog",
            cls="dialog-trigger",
            style="padding:0.5rem 1rem; border:1px solid currentColor; border-radius:0.5rem; background:transparent; cursor:pointer;",
        ),
        Dialog(
            DialogContent(
                DialogHeader(
                    DialogTitle("Basic dialog"),
                    DialogClose(
                        LucideIcon("x"),
                        dialog_id="basic_dialog",
                        style="border:none; background:none; cursor:pointer; text-decoration:underline;",
                    ),
                    cls="dialog-header",
                    style="display:flex; align-items:center; justify-content:space-between;",
                ),
                DialogBody(
                    P("Dialogs use standard HTML dialog elements with Datastar signals."),
                    P("When you pass `id='basic_dialog'`, the signal becomes `$basic_dialog_open` automatically."),
                    cls="dialog-body",
                    style="display:grid; gap:0.75rem;",
                ),
                DialogFooter(
                    DialogClose(
                        "Cancel",
                        dialog_id="basic_dialog",
                        style="border:1px solid currentColor; background:transparent; padding:0.4rem 0.9rem; border-radius:0.5rem; cursor:pointer;",
                    ),
                    DialogClose(
                        "Confirm",
                        dialog_id="basic_dialog",
                        on_click="console.log('Confirmed')",
                        style="border:1px solid currentColor; padding:0.4rem 0.9rem; border-radius:0.5rem; cursor:pointer;",
                    ),
                    cls="dialog-footer",
                    style="display:flex; justify-content:flex-end; gap:0.75rem;",
                ),
                cls="dialog-content",
            ),
            id="basic_dialog",
            cls="dialog",
            style="gap:1.5rem; padding:1.5rem; border:1px solid currentColor; border-radius:0.75rem; background:Canvas; color:CanvasText; min-width:18rem;",
            data_style="{backdropFilter: $basic_dialog_open ? 'blur(6px)' : 'none'}",
        ),
    )


def example_custom_dialog() -> HtmlString:
    return Div(
        DialogTrigger(
            "Compose message",
            dialog_id="composer",
            cls="dialog-trigger",
            style="padding:0.5rem 1rem; border:1px solid currentColor; border-radius:999px; background:transparent; cursor:pointer;",
        ),
        Dialog(
            DialogContent(
                DialogHeader(
                    DialogTitle("Compose message"),
                    DialogClose(
                        "×",
                        dialog_id="composer",
                        style="border:none; background:none; font-size:1.25rem; cursor:pointer; line-height:1;",
                    ),
                    cls="dialog-header",
                    style="display:flex; align-items:center; justify-content:space-between;",
                ),
                DialogBody(
                    P("Use standard HTML dialog elements with Datastar for reactive behavior."),
                    Div(
                        Label("Subject", _for="subject"),
                        Input(id="subject", placeholder="Quarterly report", style="padding:0.4rem 0.6rem; border:1px solid currentColor; border-radius:0.4rem;"),
                        Label("Message", _for="message"),
                        Textarea(id="message", rows=4, style="padding:0.4rem 0.6rem; border:1px solid currentColor; border-radius:0.4rem;"),
                        style="display:grid; gap:0.75rem;",
                    ),
                    cls="dialog-body",
                    style="display:grid; gap:1rem;",
                ),
                DialogFooter(
                    DialogClose(
                        "Discard",
                        dialog_id="composer",
                        style="border:1px solid currentColor; background:transparent; padding:0.45rem 1rem; border-radius:0.5rem; cursor:pointer;",
                    ),
                    DialogClose(
                        "Send",
                        dialog_id="composer",
                        on_click="console.log('Message sent')",
                        style="border:1px solid currentColor; padding:0.45rem 1rem; border-radius:0.5rem; cursor:pointer;",
                    ),
                    cls="dialog-footer",
                    style="display:flex; justify-content:flex-end; gap:0.75rem;",
                ),
                cls="dialog-content",
                data_style="{boxShadow: $composer_open ? '0 24px 48px -24px oklch(0 0 0 / 0.45)' : 'none'}",
            ),
            id="composer",
            style="gap:1.5rem; padding:1.75rem; border:1px solid currentColor; border-radius:1rem; background:Canvas; color:CanvasText; min-width:22rem;",
            data_style="{opacity: $composer_open ? 1 : 0.92}",
        ),
    )


def example_confirm_dialog() -> HtmlString:
    """Example of how to build a confirmation dialog with the simplified API"""
    return Div(
        DialogTrigger(
            "Delete file",
            dialog_id="delete-file",
            cls="dialog-trigger",
            style="padding:0.45rem 1rem; border:1px solid currentColor; border-radius:0.5rem; background:var(--red-3, #fee); cursor:pointer;",
        ),
        Dialog(
            DialogContent(
                DialogHeader(
                    DialogTitle("Delete file"),
                    DialogClose(
                        "×",
                        dialog_id="delete-file",
                        style="border:none; background:none; cursor:pointer; font-size:1rem;",
                    ),
                    cls="dialog-header",
                    style="display:flex; align-items:center; justify-content:space-between;",
                ),
                DialogBody(
                    P("Are you sure you want to delete this file? This action cannot be undone."),
                    cls="dialog-body",
                ),
                DialogFooter(
                    DialogClose(
                        "Cancel",
                        dialog_id="delete-file",
                        style="padding:0.45rem 1rem; border:1px solid currentColor; border-radius:0.5rem; background:transparent; cursor:pointer;",
                    ),
                    DialogClose(
                        "Delete",
                        dialog_id="delete-file",
                        on_click="console.log('File deleted')",
                        style="padding:0.45rem 1rem; border:1px solid currentColor; border-radius:0.5rem; background:var(--red-6, #c00); color:Canvas; cursor:pointer;",
                    ),
                    cls="dialog-footer",
                ),
                cls="dialog-content",
                data_style="{maxWidth: '26rem', borderColor: $delete_file_open ? 'currentColor' : 'transparent'}",
            ),
            id="delete-file",
        ),
    )


page = Div(
        H1("Dialog Component"),
        P("The Dialog component provides a simplified interface to the native HTML `dialog` element with Datastar integration."),

        Section(
            "Component Purpose",
            P("Dialog solves modal orchestration using standard web APIs:"),
            Ul(
                Li("🏗️ Datastar-driven open state with automatic signal generation"),
                Li("♿️ Accessibility handled by the browser via `<dialog>` APIs"),
                Li("⌨️ Keyboard support including ESC, focus trap, and restoration"),
                Li("🪟 Backdrop interaction control through inline expressions"),
                Li("🎛️ Simple composition without complex context passing"),
            ),
        ),

        Section(
            "Basic Dialog Demo",
            P("A straightforward dialog using the simplified API."),
            ComponentShowcase(example_basic_dialog),
        ),

        Section(
            "Custom Dialog Demo",
            P("Demonstrates styling hooks and inline side effects."),
            ComponentShowcase(example_custom_dialog),
        ),

        Section(
            "Confirmation Dialog Example",
            P("How to build a confirmation dialog with the simplified API."),
            ComponentShowcase(example_confirm_dialog),
        ),

        Section(
            "API Reference",
            CodeBlock(
                """
from typing import Any, Optional

# Root dialog wrapper
Dialog(
    *children: Any,
    id: str,  # Required - HTML id of dialog element
    default_open: bool = False,
    modal: bool = True,
    close_on_escape: bool = True,
    close_on_backdrop: bool = True,
    cls: str = "",
    **attrs: Any,
) -> HtmlString

# Trigger button (uses basic JS: document.getElementById('id').showModal())
DialogTrigger(
    *children: Any,
    dialog_id: str,  # Required - ID of dialog to open
    cls: str = "",
    **attrs: Any,
) -> HtmlString

# Dialog content wrapper
DialogContent(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString

# Dialog sections
DialogHeader(*children: Any, cls: str = "", **attrs: Any) -> HtmlString
DialogTitle(*children: Any, cls: str = "", **attrs: Any) -> HtmlString
DialogBody(*children: Any, cls: str = "", **attrs: Any) -> HtmlString
DialogFooter(*children: Any, cls: str = "", **attrs: Any) -> HtmlString

# Close button (uses basic JS: document.getElementById('id').close())
DialogClose(
    *children: Any,
    dialog_id: str,  # Required - ID of dialog to close
    cls: str = "",
    **attrs: Any,
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),

        Section(
            "Implementation Notes",
            Ul(
                Li("🆔 Pass `id` to Dialog and `dialog_id` to triggers/closers"),
                Li("🦀 Native-first: uses standard HTML `<dialog>` element with basic JavaScript API"),
                Li("📊 Simple: `document.getElementById('dialog-id').showModal()` and `.close()`"),
                Li("🎛️ No complex state management - just basic DOM manipulation"),
                Li("🚫 No Datastar complexity - pure JavaScript for dialog control"),
            ),
        ),

        Section(
            "Migration from Old API",
            P("The new API is simpler but requires some changes:"),
            Ul(
                Li("✅ `Dialog(id='my-dialog')` - same as before"),
                Li("✅ `DialogTrigger('Open', dialog_id='my-dialog')` - now requires explicit dialog_id"),
                Li("✅ `DialogClose('Close', dialog_id='my-dialog')` - now requires explicit dialog_id"),
                Li("❌ No more `ConfirmDialog` - build your own with the components above"),
                Li("❌ No more `content_attrs` - use `DialogContent` with direct attributes"),
            ),
        ),

        Section(
            "Accessibility",
            Ul(
                Li("🎯 Focus returns to the trigger once the dialog closes"),
                Li("⌨️ ESC and backdrop clicks can be toggled via parameters"),
                Li("🔖 `aria-*` attributes are automatically set for proper association"),
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