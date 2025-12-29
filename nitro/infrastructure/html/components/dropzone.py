"""Dropzone file upload component.

A styled file drop area that allows users to drag-and-drop files or click
to select files via the native file picker. Uses pure HTML5 file input
without JavaScript dependencies.
"""

from typing import Optional
import rusty_tags as rt
from rusty_tags import HtmlString
from .utils import cn
from .icons import LucideIcon


def Dropzone(
    *children,
    id: str,
    accept: Optional[str] = None,
    multiple: bool = False,
    disabled: bool = False,
    name: Optional[str] = None,
    cls: str = "",
    **attrs
) -> HtmlString:
    """File upload dropzone component.

    Creates a styled drop area with a hidden file input. Clicking the area
    or dropping files triggers the native file picker.

    Args:
        *children: Custom content (icon, text). If empty, default content is shown.
        id: Unique identifier for the input element (required).
        accept: File type restrictions (e.g., "image/*", ".pdf,.docx").
        multiple: Allow selecting multiple files.
        disabled: Disable the dropzone.
        name: Form field name. Defaults to id if not specified.
        cls: Additional CSS classes for the container.
        **attrs: Additional HTML attributes for the container.

    Returns:
        HtmlString: The rendered dropzone HTML.

    Example:
        # Basic dropzone
        Dropzone(id="avatar")

        # Image only, multiple files
        Dropzone(
            id="photos",
            accept="image/*",
            multiple=True
        )

        # Custom content
        Dropzone(
            LucideIcon("cloud-upload", cls="dropzone-icon"),
            P("Drop your resume here", cls="dropzone-text"),
            P("PDF or DOCX, max 5MB", cls="dropzone-hint"),
            id="resume",
            accept=".pdf,.docx"
        )
    """
    # Build input attributes
    input_attrs = {
        "type": "file",
        "id": id,
        "name": name or id,
    }

    if accept:
        input_attrs["accept"] = accept
    if multiple:
        input_attrs["multiple"] = True
    if disabled:
        input_attrs["disabled"] = True

    # Build container attributes
    container_attrs = dict(attrs)
    if disabled:
        container_attrs["data_disabled"] = "true"

    # Default content if no children provided
    if not children:
        children = (
            LucideIcon("upload", cls="dropzone-icon"),
            rt.P("Click to upload or drag and drop", cls="dropzone-text"),
            rt.P("Any file up to 10MB", cls="dropzone-hint"),
        )

    return rt.Label(
        rt.Input(**input_attrs),
        rt.Div(*children, cls="dropzone-content"),
        for_=id,
        cls=cn("dropzone", cls),
        **container_attrs
    )


def DropzoneItem(
    filename: str,
    size: Optional[str] = None,
    icon: str = "file",
    on_remove: Optional[str] = None,
    cls: str = "",
    **attrs
) -> HtmlString:
    """File list item for displaying uploaded files.

    Shows file information with optional remove button. Can be used
    to display files after selection.

    Args:
        filename: The name of the file to display.
        size: Formatted file size (e.g., "2.5 MB").
        icon: Lucide icon name for file type (default: "file").
        on_remove: Action for remove button (onclick handler or href).
        cls: Additional CSS classes.
        **attrs: Additional HTML attributes.

    Returns:
        HtmlString: The rendered file item HTML.

    Example:
        DropzoneItem(
            filename="document.pdf",
            size="1.2 MB",
            icon="file-text",
            on_remove="removeFile('document.pdf')"
        )
    """
    # File info section
    info_content = [LucideIcon(icon)]

    text_content = [rt.Span(filename, cls="dropzone-item-name")]
    if size:
        text_content.append(rt.Span(size, cls="dropzone-item-size"))

    info_content.append(rt.Div(*text_content))

    file_info = rt.Div(*info_content, cls="dropzone-item-info")

    # Build item content
    item_content = [file_info]

    # Add remove button if on_remove provided
    if on_remove:
        if on_remove.startswith("http") or on_remove.startswith("/"):
            # It's a link
            remove_btn = rt.A(
                LucideIcon("x"),
                href=on_remove,
                cls="dropzone-item-remove",
                aria_label=f"Remove {filename}"
            )
        else:
            # It's an onclick handler
            remove_btn = rt.Button(
                LucideIcon("x"),
                type="button",
                onclick=on_remove,
                cls="dropzone-item-remove",
                aria_label=f"Remove {filename}"
            )
        item_content.append(remove_btn)

    return rt.Div(
        *item_content,
        cls=cn("dropzone-item", cls),
        **attrs
    )


def DropzoneList(*children, cls: str = "", **attrs) -> HtmlString:
    """Container for file list items.

    Args:
        *children: DropzoneItem components.
        cls: Additional CSS classes.
        **attrs: Additional HTML attributes.

    Returns:
        HtmlString: The rendered file list container.

    Example:
        DropzoneList(
            DropzoneItem(filename="doc1.pdf", size="1.2 MB"),
            DropzoneItem(filename="doc2.pdf", size="2.5 MB"),
        )
    """
    return rt.Div(
        *children,
        cls=cn("dropzone-list", cls),
        role="list",
        **attrs
    )
