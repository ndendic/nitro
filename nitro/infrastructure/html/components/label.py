from typing import Any, Optional
from rusty_tags import Label as HTMLLabel, HtmlString
from .utils import cn


def Label(
    *children: Any,
    html_for: Optional[str] = None,
    required: bool = False,
    disabled: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Label component for form inputs.

    A text label associated with a form control, providing
    accessible naming for inputs.

    Args:
        *children: Label content (text, required indicators, etc.)
        html_for: ID of the associated form element (maps to HTML 'for' attribute)
        required: Whether to indicate the field is required
        disabled: Whether to apply disabled styling
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered label element

    Example:
        # Basic label
        Label("Email", html_for="email-input")

        # Required field label
        Label("Password", html_for="password-input", required=True)

        # Label with icon
        Label(LucideIcon("mail"), "Email Address", html_for="email")
    """
    label_attrs = dict(attrs)

    if html_for:
        label_attrs["for_"] = html_for

    if required:
        label_attrs["data_required"] = "true"

    if disabled:
        label_attrs["data_disabled"] = "true"

    return HTMLLabel(
        *children,
        cls=cn("label", cls),
        **label_attrs,
    )
