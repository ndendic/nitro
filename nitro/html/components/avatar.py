"""Avatar component for displaying user profile images with fallback support."""

from typing import Any, Literal
from rusty_tags import Div, Img, Span, HtmlString
from .utils import cn, cva

# Avatar size configuration using cva
avatar_variants = cva(
    base="avatar",
    config={
        "variants": {
            "size": {
                "xs": "avatar-xs",
                "sm": "avatar-sm",
                "md": "avatar-md",
                "lg": "avatar-lg",
                "xl": "avatar-xl",
            },
        },
        "defaultVariants": {"size": "md"},
    }
)


SIZE_PIXELS = {
    "xs": 24,
    "sm": 32,
    "md": 40,
    "lg": 48,
    "xl": 64,
}

AvatarSize = Literal["xs", "sm", "md", "lg", "xl"]

def DiceBearAvatar(
    seed_name: str,  # Seed name (ie 'Isaac Flath')
    h: int = 30,  # Height
    w: int = 30,  # Width
):  # Span with Avatar
    "Creates an Avatar using https://dicebear.com/"
    url = "https://api.dicebear.com/8.x/lorelei/svg?seed="
    return Span(    
        Img(
            cls="aspect-square",
            alt="Avatar",
            loading="lazy",
            src=f"{url}{seed_name}",
            style=f"width: {w}px; height: {h}px;",
        ),
        cls="relative flex shrink-0 overflow-hidden rounded-full bg-secondary"
    )
    
def _get_initials(text: str, max_chars: int = 2) -> str:
    """Extract initials from text.

    - For single word: first 2 chars
    - For multiple words: first char of each word (up to max_chars)
    """
    if not text:
        return ""

    words = text.strip().split()
    if len(words) == 1:
        return words[0][:max_chars].upper()
    else:
        initials = "".join(word[0] for word in words if word)
        return initials[:max_chars].upper()


def Avatar(
    src: str = "",
    alt: str = "",
    fallback: str = "",
    size: AvatarSize = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Avatar component displaying profile images with fallback initials.

    Shows an image when available, falls back to initials when no image
    is provided or the image fails to load.

    Args:
        src: Image URL for the avatar
        alt: Alt text for the image (also used for generating initials)
        fallback: Explicit fallback text (overrides auto-generated initials)
        size: Avatar size
            - "xs": Extra small (24px)
            - "sm": Small (32px)
            - "md": Medium (40px, default)
            - "lg": Large (48px)
            - "xl": Extra large (64px)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered avatar element

    Example:
        # With image
        Avatar(src="/user.jpg", alt="John Doe", size="md")

        # With fallback initials (auto-generated)
        Avatar(alt="John Doe", size="lg")  # Shows "JD"

        # With explicit fallback
        Avatar(fallback="AB", size="sm")

        # Just initials
        Avatar(alt="Alice", size="xl")  # Shows "AL"
    """
    size_px = SIZE_PIXELS.get(size, SIZE_PIXELS["md"])

    # Determine fallback text
    initials = fallback if fallback else _get_initials(alt)

    # Base classes for the container
    base_cls = cn(
        "relative inline-flex items-center justify-center",
        "rounded-full overflow-hidden",
        "bg-muted text-muted-foreground font-medium",
        "select-none shrink-0",
        cls,
    )

    if src:
        # With image - show image with fallback hidden
        return Div(
            Img(
                src=src,
                alt=alt,
                cls="aspect-square size-full object-cover",
                style=f"width: {size_px}px; height: {size_px}px;",
            ),    
            cls=base_cls,
            data_size=size,
            **attrs,
        )
    else:
        # No image - show fallback initials
        return Div(
            initials, 
            style=f"width: {size_px}px; height: {size_px}px;" if initials else "display: none;",
            cls=base_cls,
            data_size=size,
            role="img",
            aria_label=alt or fallback or "Avatar",
            **attrs,
        )


def AvatarGroup(
    *children: Any,
    max_avatars: int = 4,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Container for grouping multiple avatars with overlap effect.

    Displays avatars overlapping each other, commonly used for showing
    team members or participants.

    Args:
        *children: Avatar components to group
        max_avatars: Maximum number of avatars to show (rest shown as +N)
        cls: Additional CSS classes
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered avatar group container

    Example:
        AvatarGroup(
            Avatar(src="/user1.jpg", alt="User 1"),
            Avatar(src="/user2.jpg", alt="User 2"),
            Avatar(src="/user3.jpg", alt="User 3"),
            max_avatars=3,
        )
    """
    visible = children[:max_avatars]
    remaining = len(children) - max_avatars

    # Apply negative margin to create overlap effect
    styled_avatars = []
    for i, avatar in enumerate(visible):
        wrapper_cls = "-ml-3 ring-2 ring-background rounded-full" if i > 0 else "ring-2 ring-background rounded-full"
        styled_avatars.append(
            Div(avatar, cls=wrapper_cls)
        )

    # Add overflow indicator if needed
    if remaining > 0:
        styled_avatars.append(
            Div(
                Avatar(fallback=f"+{remaining}", size="md"),
                cls="-ml-3 ring-2 ring-background rounded-full",
            )
        )

    return Div(
        *styled_avatars,
        cls=cn("flex items-center", cls),
        role="group",
        aria_label="Avatar group",
        **attrs,
    )