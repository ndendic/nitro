"""Dropzone component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import (
    Dropzone,
    DropzoneItem,
    DropzoneList,
    LucideIcon,
    Badge,
)

router: APIRouter = APIRouter()


def example_basic():
    return Dropzone(id="basic-upload")


def example_multiple():
    return Dropzone(
        id="multi-upload",
        multiple=True
    )


def example_accept():
    return Div(
        Div(
            P("Images only:", cls="text-sm font-medium mb-2"),
            Dropzone(
                LucideIcon("image", cls="dropzone-icon"),
                P("Drop images here", cls="dropzone-text"),
                P("PNG, JPG, GIF up to 10MB", cls="dropzone-hint"),
                id="image-upload",
                accept="image/*"
            ),
            cls="flex-1"
        ),
        Div(
            P("Documents only:", cls="text-sm font-medium mb-2"),
            Dropzone(
                LucideIcon("file-text", cls="dropzone-icon"),
                P("Drop documents here", cls="dropzone-text"),
                P("PDF, DOC, DOCX", cls="dropzone-hint"),
                id="doc-upload",
                accept=".pdf,.doc,.docx"
            ),
            cls="flex-1"
        ),
        cls="grid grid-cols-1 md:grid-cols-2 gap-4"
    )


def example_with_list():
    return Div(
        Dropzone(id="files-upload", multiple=True),
        DropzoneList(
            DropzoneItem(
                filename="report-2024.pdf",
                size="2.4 MB",
                icon="file-text",
                on_remove="alert('Remove report-2024.pdf')"
            ),
            DropzoneItem(
                filename="photo.jpg",
                size="1.8 MB",
                icon="image",
                on_remove="alert('Remove photo.jpg')"
            ),
            DropzoneItem(
                filename="data.xlsx",
                size="856 KB",
                icon="file-spreadsheet",
                on_remove="alert('Remove data.xlsx')"
            ),
        ),
    )


def example_disabled():
    return Dropzone(
        id="disabled-upload",
        disabled=True
    )


def example_custom_content():
    return Dropzone(
        LucideIcon("cloud-upload", cls="dropzone-icon"),
        P("Drag and drop your files", cls="dropzone-text"),
        P("or click to browse", cls="dropzone-hint"),
        Div(
            Badge("Max 5 files"),
            Badge("10MB each"),
            cls="flex gap-2 mt-2"
        ),
        id="custom-upload",
        multiple=True
    )


page = Div(
    H1("Dropzone Component"),
    P(
        "A styled file upload area that supports drag-and-drop and click-to-upload. "
        "Uses native HTML5 file input with no JavaScript dependencies for a simple, "
        "accessible file upload experience."
    ),
    TitledSection(
        "Basic Usage",
        P("A simple dropzone with default styling and content:"),
        ComponentShowcase(example_basic),
    ),
    TitledSection(
        "Multiple Files",
        P("Allow selecting multiple files at once:"),
        ComponentShowcase(example_multiple),
    ),
    TitledSection(
        "File Type Restrictions",
        P("Restrict which file types can be selected using the accept prop:"),
        ComponentShowcase(example_accept),
    ),
    TitledSection(
        "With File List",
        P(
            "Display selected files using DropzoneItem components. "
            "The file list is typically populated via JavaScript after file selection:"
        ),
        ComponentShowcase(example_with_list),
    ),
    TitledSection(
        "Disabled State",
        P("Disable the dropzone to prevent file selection:"),
        ComponentShowcase(example_disabled),
    ),
    TitledSection(
        "Custom Content",
        P("Customize the dropzone content with your own icons, text, and elements:"),
        ComponentShowcase(example_custom_content),
    ),
    TitledSection(
        "API Reference",
        H3("Dropzone", cls="text-lg font-semibold mt-4 mb-2"),
        CodeBlock(
            """
def Dropzone(
    *children,                    # Custom content (icon, text, etc.)
    id: str,                      # Unique identifier (required)
    accept: str = None,           # File type restrictions (e.g., "image/*", ".pdf")
    multiple: bool = False,       # Allow multiple file selection
    disabled: bool = False,       # Disable the dropzone
    name: str = None,             # Form field name (defaults to id)
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
        H3("DropzoneItem", cls="text-lg font-semibold mt-6 mb-2"),
        CodeBlock(
            """
def DropzoneItem(
    filename: str,                # File name to display
    size: str = None,             # Formatted file size (e.g., "2.5 MB")
    icon: str = "file",           # Lucide icon name
    on_remove: str = None,        # Remove action (onclick or href)
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
        H3("DropzoneList", cls="text-lg font-semibold mt-6 mb-2"),
        CodeBlock(
            """
def DropzoneList(
    *children,                    # DropzoneItem components
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
            code_cls="language-python",
        ),
    ),
    TitledSection(
        "Styling",
        P(
            "The dropzone uses BaseCoat CSS classes. You can customize appearance "
            "using the cls prop or by overriding CSS custom properties:"
        ),
        CodeBlock(
            """
/* Available CSS classes */
.dropzone              /* Main container */
.dropzone-content      /* Inner content wrapper */
.dropzone-icon         /* Upload icon */
.dropzone-text         /* Primary text */
.dropzone-hint         /* Secondary hint text */
.dropzone-list         /* File list container */
.dropzone-item         /* Individual file item */
.dropzone-item-info    /* File name and size */
.dropzone-item-remove  /* Remove button */

/* State attributes */
[data-disabled]        /* Disabled state */
[data-invalid]         /* Error state */
""",
            code_cls="language-css",
        ),
    ),
    BackLink(),
    id="content"
)


@router.get("/xtras/dropzone")
@template(title="Dropzone Component Documentation")
def dropzone_page():
    return page


@on("page.dropzone")
async def get_dropzone(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.dropzone")
