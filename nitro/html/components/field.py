"""Field component - Form field wrapper with label, description, and error states."""

from typing import Any, Optional
from rusty_tags import Div, HtmlString, H3, P, Span
from rusty_tags import Label as HTMLLabel
from .utils import cn


def Field(
    *children: Any,
    label: str = "",
    label_for: str = "",
    error: str = "",
    description: str = "",
    orientation: str = "vertical",
    required: bool = False,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Form field wrapper providing Basecoat context styling.

    All inputs inside Field are automatically styled via Basecoat CSS.
    Uses semantic children for proper structure:
    - h2/h3 for title/label
    - p for description
    - [role="alert"] for errors

    Args:
        *children: Form input elements (Input, Select, Checkbox, etc.)
        label: Field label text
        label_for: ID of the associated form element (for label association)
        error: Error message to display (triggers invalid state)
        description: Helper text displayed below the label
        orientation: Layout direction - "vertical" (default) or "horizontal"
        required: Whether to show required indicator
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered field container

    Example:
        # Basic field with input
        Field(
            Input(type="email", id="email"),
            label="Email",
            label_for="email",
        )

        # Field with description
        Field(
            Input(type="password", id="password"),
            label="Password",
            label_for="password",
            description="Must be at least 8 characters",
        )

        # Field with error state
        Field(
            Input(type="text", id="name"),
            label="Name",
            label_for="name",
            error="Name is required",
        )

        # Horizontal orientation
        Field(
            Checkbox("Accept terms", id="terms"),
            label="Terms",
            orientation="horizontal",
        )
    """
    field_classes = cn("field", cls)

    field_attrs: dict[str, Any] = dict(attrs)

    # Set orientation attribute for horizontal layout
    if orientation == "horizontal":
        field_attrs["data_orientation"] = "horizontal"

    # Set invalid state if there's an error
    if error:
        field_attrs["data_invalid"] = "true"

    # Build field content
    field_content: list[Any] = []

    # Add label if provided
    if label:
        if label_for:
            # Use a label element if we have a for attribute
            field_content.append(
                HTMLLabel(
                    label,
                    Span("*",cls="text-destructive") if required else None,
                    for_=label_for,
                    cls="text-sm font-medium leading-snug",
                )
            )
        else:
            # Use h3 for semantic structure (Basecoat styles h2/h3 in .field)
            field_content.append(
                H3(label)
            )

    # Add the form input children
    field_content.extend(children)
    # Add description if provided (before input for better UX)
    if description:
        field_content.append(
            P(description)
        )

    # Add error message if provided
    if error:
        field_content.append(
            P(error, role="alert")
        )

    return Div(
        *field_content,
        cls=field_classes,
        **field_attrs,
    )


def Fieldset(
    *children: Any,
    legend: str = "",
    description: str = "",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Fieldset component for grouping related form fields.

    Args:
        *children: Field components to group
        legend: Fieldset title
        description: Helper text below the legend
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered fieldset container

    Example:
        Fieldset(
            Field(Input(id="first"), label="First Name", label_for="first"),
            Field(Input(id="last"), label="Last Name", label_for="last"),
            legend="Personal Information",
            description="Enter your full legal name.",
        )
    """
    from rusty_tags import Fieldset as HTMLFieldset, Legend

    fieldset_content: list[Any] = []

    if legend:
        fieldset_content.append(Legend(legend))

    if description:
        fieldset_content.append(P(description))

    fieldset_content.extend(children)

    return HTMLFieldset(
        *fieldset_content,
        cls=cn("fieldset", cls),
        **attrs,
    )
