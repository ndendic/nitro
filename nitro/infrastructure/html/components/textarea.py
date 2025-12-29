"""Textarea component with Datastar binding support."""

from typing import Any, Optional
from rusty_tags import Textarea as HTMLTextarea, HtmlString
from .utils import cn


def Textarea(
    *children: Any,
    id: Optional[str] = None,
    bind: Any = None,
    placeholder: str = "",
    rows: int = 3,
    cols: Optional[int] = None,
    disabled: bool = False,
    required: bool = False,
    readonly: bool = False,
    maxlength: Optional[int] = None,
    minlength: Optional[int] = None,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Textarea input with Datastar two-way binding.

    Uses Basecoat's context-based styling inside Field.
    When placed inside a .field container, the textarea is
    automatically styled via Basecoat CSS. Can also use .textarea class
    for standalone usage.

    Args:
        *children: Default text content for the textarea
        id: Unique identifier for the textarea (optional, used for label association)
        bind: Datastar Signal for two-way binding (optional)
        placeholder: Placeholder text when empty
        rows: Number of visible text lines (default: 3)
        cols: Visible width in average character widths (optional)
        disabled: Whether the textarea is disabled
        required: Whether the textarea is required
        readonly: Whether the textarea is read-only
        maxlength: Maximum character limit
        minlength: Minimum character limit
        cls: Additional CSS classes
        **attrs: Additional HTML attributes passed through

    Returns:
        HtmlString: Rendered textarea element

    Example:
        # Basic textarea
        Textarea(id="message", placeholder="Enter your message...")

        # With Datastar binding
        from nitro.infrastructure.html.datastar import Signal, Signals
        form = Signals(bio="")
        Textarea(
            id="bio",
            bind=form.bio,
            placeholder="Tell us about yourself...",
            rows=5,
        )

        # Inside a Field (recommended for forms)
        Field(
            Textarea(
                id="comments",
                bind=form.comments,
                placeholder="Leave a comment...",
                rows=4,
            ),
            label="Comments",
            label_for="comments",
        )

        # With character limit
        Textarea(
            id="tweet",
            bind=form.tweet,
            maxlength=280,
            placeholder="What's happening?",
        )
    """
    textarea_attrs: dict[str, Any] = {
        "id": id if id else None,
        "name": attrs.pop("name", id) if id else attrs.pop("name", None),
        "placeholder": placeholder if placeholder else None,
        "rows": rows,
        "cols": cols if cols else None,
        "disabled": disabled if disabled else None,
        "required": required if required else None,
        "readonly": readonly if readonly else None,
        "maxlength": maxlength if maxlength else None,
        "minlength": minlength if minlength else None,
    }

    # Handle Datastar binding
    if bind is not None:
        # Signal from Datastar
        if hasattr(bind, 'to_js'):
            # Get the signal name without the $ prefix
            signal_name = bind.to_js().lstrip('$')
            textarea_attrs["data_bind"] = signal_name
        elif isinstance(bind, str):
            textarea_attrs["data_bind"] = bind.lstrip('$')

    # Merge additional attributes
    textarea_attrs.update(attrs)

    # Create the textarea - add .textarea class for Basecoat styling
    # Basecoat CSS targets: .form/.field textarea OR .textarea
    input_kwargs = {k: v for k, v in textarea_attrs.items() if v is not None}
    input_kwargs["cls"] = cn("textarea", cls) if cls else "textarea"

    return HTMLTextarea(*children, **input_kwargs)
