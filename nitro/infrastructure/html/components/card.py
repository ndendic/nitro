from typing import Any, Literal
from rusty_tags import Div, H2, P, HtmlString, Header, Section, Footer
from .utils import cn

CardVariant = Literal["default", "elevated", "outline", "ghost"]


def Card(
    *children: Any,
    variant: CardVariant = "default",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Card container component for grouping related content.

    A flexible container that groups related content and actions.
    Works well with CardHeader, CardTitle, CardDescription, CardContent,
    and CardFooter for structured layouts.

    Args:
        *children: Card content (typically Card* subcomponents)
        variant: Visual style variant
            - "default": Standard card with background
            - "elevated": Card with shadow/elevation
            - "outline": Border-only card
            - "ghost": Minimal/transparent card
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card container

    Example:
        Card(
            CardHeader(
                CardTitle("Card Title"),
                CardDescription("Card description here"),
            ),
            CardContent(
                P("Main card content goes here."),
            ),
            CardFooter(
                Button("Cancel", variant="ghost"),
                Button("Save", variant="primary"),
            ),
        )
    """
    return Div(
        *children,
        cls=cn("card", cls),
        data_variant=variant,
        **attrs,
    )


def CardHeader(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Header section of a card.

    Typically contains CardTitle and optionally CardDescription.

    Args:
        *children: Header content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card header

    Example:
        CardHeader(
            CardTitle("Settings"),
            CardDescription("Manage your account settings"),
        )
    """
    return Header(
        *children,
        cls=cn("card-header", cls),
        **attrs,
    )


def CardTitle(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Title element for a card.

    Args:
        *children: Title content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card title

    Example:
        CardTitle("User Profile")
    """
    return H2(
        *children,
        cls=cn("card-title", cls),
        **attrs,
    )


def CardDescription(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Description/subtitle for a card.

    Args:
        *children: Description content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card description

    Example:
        CardDescription("Configure your notification preferences")
    """
    return P(
        *children,
        cls=cn("card-description", cls),
        **attrs,
    )


def CardContent(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Main content area of a card.

    Args:
        *children: Card content
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card content

    Example:
        CardContent(
            Form(
                Input(label="Email", type="email"),
                Input(label="Password", type="password"),
            )
        )
    """
    return Div(
        *children,
        cls=cn("card-content", cls),
        **attrs,
    )


def CardFooter(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Footer section of a card, typically for actions.

    Args:
        *children: Footer content (usually buttons)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered card footer

    Example:
        CardFooter(
            Button("Cancel", variant="outline"),
            Button("Continue", variant="primary"),
        )
    """
    return Footer(
        *children,
        cls=cn("card-footer", cls),
        **attrs,
    )
