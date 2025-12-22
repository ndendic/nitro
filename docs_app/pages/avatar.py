"""Avatar component documentation page"""

from .templates.base import *  # noqa: F403
from .templates.components import DiceBearAvatar
from fastapi.requests import Request
from fastapi import APIRouter

from nitro.infrastructure.html.components import Avatar, AvatarGroup
from nitro.infrastructure.events import on, emit_elements

router: APIRouter = APIRouter()


def example_basic():
    """Basic avatar with image."""
    return Div(
        Avatar(
            src="https://github.com/ndendic.png",
            alt="John Doe",
            size="md",
        ),
        cls="flex items-center gap-4",
    )


def example_fallback():
    """Avatar with fallback initials when no image is provided."""
    return Div(
        Avatar(alt="John Doe", size="md"),
        Avatar(alt="Alice Smith", size="md"),
        Avatar(alt="Bob", size="md"),
        Avatar(fallback="AB", size="md"),
        cls="flex items-center gap-4",
    )


def example_sizes():
    """Avatar in all available sizes."""
    return Div(
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=xs", alt="Extra Small", size="xs"),
            Span("xs (24px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=sm", alt="Small", size="sm"),
            Span("sm (32px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=md", alt="Medium", size="md"),
            Span("md (40px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=lg", alt="Large", size="lg"),
            Span("lg (48px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=xl", alt="Extra Large", size="xl"),
            Span("xl (64px)", cls="text-sm text-muted-foreground"),
            cls="flex flex-col items-center gap-2",
        ),
        cls="flex items-end gap-6",
    )


def example_fallback_sizes():
    """Fallback avatars in all sizes."""
    return Div(
        Avatar(alt="John Doe", size="xs"),
        Avatar(alt="John Doe", size="sm"),
        Avatar(alt="John Doe", size="md"),
        Avatar(alt="John Doe", size="lg"),
        Avatar(alt="John Doe", size="xl"),
        cls="flex items-center gap-4",
    )


def example_avatar_group():
    """Group of avatars with overlap effect."""
    return AvatarGroup(
        Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=User1", alt="User 1"),
        Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=User2", alt="User 2"),
        Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=User3", alt="User 3"),
        Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=User4", alt="User 4"),
        Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=User5", alt="User 5"),
        max_avatars=3,
    )


def example_with_badge():
    """Avatar with status badge overlay."""
    return Div(
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=Online", alt="Online User", size="lg"),
            Span(cls="absolute right-0 bottom-0 -translate-y-1/2 size-3 bg-green-500 rounded-full ring-2 ring-background"),
            cls="relative inline-block",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=Busy", alt="Busy User", size="lg"),
            Span(cls="absolute right-0 bottom-0 -translate-y-1/2 size-3 bg-yellow-500 rounded-full ring-2 ring-background"),
            cls="relative inline-block",
        ),
        Div(
            Avatar(src="https://api.dicebear.com/7.x/avataaars/svg?seed=Offline", alt="Offline User", size="lg"),
            Span(cls="absolute right-0 bottom-0 -translate-y-1/2 size-3 bg-gray-400 rounded-full ring-2 ring-background"),
            cls="relative inline-block",
        ),
        cls="flex items-center gap-6",
    )


page = Div(
        H1("Avatar Component"),
        P(
            "Display user profile images with automatic fallback to initials "
            "when no image is available."
        ),
        TitledSection(
            "Design Philosophy",
            P("Avatar follows common UI patterns:"),
            Ul(
                Li("Circular shape for profile imagery"),
                Li("Automatic initials extraction from alt text"),
                Li("Multiple size variants for different contexts"),
                Li("Composable with badges for status indicators"),
                Li("AvatarGroup for team/participant displays"),
            ),
        ),
        TitledSection(
            "Basic Usage",
            P("Avatar with an image source:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "Fallback Initials",
            P("When no image is provided, shows initials extracted from alt text or explicit fallback:"),
            ComponentShowcase(example_fallback),
        ),
        TitledSection(
            "Sizes",
            P("Available size variants from extra-small to extra-large:"),
            ComponentShowcase(example_sizes),
        ),
        TitledSection(
            "Fallback Sizes",
            P("Fallback initials scale with avatar size:"),
            ComponentShowcase(example_fallback_sizes),
        ),
        TitledSection(
            "Avatar Group",
            P("Display multiple avatars with overlap effect, with +N indicator for overflow:"),
            ComponentShowcase(example_avatar_group),
        ),
        TitledSection(
            "With Status Badge",
            P("Combine with status indicators for presence/activity:"),
            ComponentShowcase(example_with_badge),
        ),
        TitledSection(
            "API Reference",
            CodeBlock(
                """
def Avatar(
    src: str = "",              # Image URL
    alt: str = "",              # Alt text (also used for initials)
    fallback: str = "",         # Explicit fallback text
    size: str = "md",           # xs, sm, md, lg, xl
    cls: str = "",              # Additional CSS classes
    **attrs                     # Additional HTML attributes
) -> HtmlString

def AvatarGroup(
    *children,                  # Avatar components
    max_avatars: int = 4,       # Max to show before +N
    cls: str = "",              # Additional CSS classes
    **attrs                     # Additional HTML attributes
) -> HtmlString

# Size reference
# xs: 24px (size-6)
# sm: 32px (size-8)
# md: 40px (size-10)
# lg: 48px (size-12)
# xl: 64px (size-16)
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Accessibility",
            Ul(
                Li("role='img' on fallback-only avatars"),
                Li("aria-label for screen reader context"),
                Li("Alt text on image elements"),
                Li("role='group' and aria-label on AvatarGroup"),
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/avatar")
@template(title="Avatar Component Documentation")
def avatar_page():
    return page

@on("page.avatar")
async def get_avatar(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.avatar")