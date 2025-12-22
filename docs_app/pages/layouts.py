"""Layout component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import *
from nitro.infrastructure.html.components.base_layouts import (
    Container, Center, Grid, DivFullySpaced, DivCentered,
    DivLAligned, DivRAligned, DivVStacked, DivHStacked,
    ContainerT, FlexT
)

router: APIRouter = APIRouter()


def example_container():
    return Div(
        Container(
            P("This is content inside a Container component."),
            P("Containers provide max-width constraints and centering."),
            cls="border-2 border-dashed border-primary rounded-md p-4",
        ),
        cls="w-full"
    )


def example_container_sizes():
    return Div(
        Container(
            P("Extra Small Container (xs)"),
            cls="border-2 border-dashed border-primary rounded-md p-2 mb-4 " + str(ContainerT.xs),
        ),
        Container(
            P("Small Container (sm)"),
            cls="border-2 border-dashed border-primary rounded-md p-2 mb-4 " + str(ContainerT.sm),
        ),
        Container(
            P("Large Container (lg)"),
            cls="border-2 border-dashed border-primary rounded-md p-2 mb-4 " + str(ContainerT.lg),
        ),
        Container(
            P("Extra Large Container (xl)"),
            cls="border-2 border-dashed border-primary rounded-md p-2 " + str(ContainerT.xl),
        ),
    )


def example_center():
    return Div(
        Center(
            Div(
                P("Centered Content"),
                cls="bg-primary text-primary-foreground p-4 rounded-md",
            ),
            cls="h-32 border-2 border-dashed border-primary rounded-md",
        ),
    )


def example_center_options():
    return Div(
        Div(
            P("Horizontal only:", cls="text-sm text-muted-foreground mb-2"),
            Center(
                Div("H", cls="bg-primary text-primary-foreground p-2 rounded"),
                vertical=False,
                cls="h-16 border-2 border-dashed border-primary rounded-md",
            ),
        ),
        Div(
            P("Vertical only:", cls="text-sm text-muted-foreground mb-2"),
            Center(
                Div("V", cls="bg-primary text-primary-foreground p-2 rounded"),
                horizontal=False,
                cls="h-16 border-2 border-dashed border-primary rounded-md",
            ),
        ),
        Div(
            P("Both (default):", cls="text-sm text-muted-foreground mb-2"),
            Center(
                Div("B", cls="bg-primary text-primary-foreground p-2 rounded"),
                cls="h-16 border-2 border-dashed border-primary rounded-md",
            ),
        ),
        cls="grid grid-cols-3 gap-4"
    )


def example_grid():
    return Grid(
        Div("Item 1", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
        Div("Item 2", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
        Div("Item 3", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
        Div("Item 4", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
        Div("Item 5", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
        Div("Item 6", cls="bg-primary text-primary-foreground p-4 rounded-md text-center"),
    )


def example_grid_cols():
    return Div(
        P("Fixed 2 columns:", cls="text-sm text-muted-foreground mb-2"),
        Grid(
            Div("1", cls="bg-secondary p-4 rounded-md text-center"),
            Div("2", cls="bg-secondary p-4 rounded-md text-center"),
            Div("3", cls="bg-secondary p-4 rounded-md text-center"),
            Div("4", cls="bg-secondary p-4 rounded-md text-center"),
            cols=2,
        ),
        P("Fixed 4 columns:", cls="text-sm text-muted-foreground mb-2 mt-4"),
        Grid(
            Div("1", cls="bg-secondary p-4 rounded-md text-center"),
            Div("2", cls="bg-secondary p-4 rounded-md text-center"),
            Div("3", cls="bg-secondary p-4 rounded-md text-center"),
            Div("4", cls="bg-secondary p-4 rounded-md text-center"),
            cols=4,
        ),
    )


def example_div_fully_spaced():
    return DivFullySpaced(
        Div("Left", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
        Div("Center", cls="bg-secondary px-4 py-2 rounded-md"),
        Div("Right", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
        cls="w-full border-2 border-dashed border-primary rounded-md p-4",
    )


def example_div_centered():
    return DivCentered(
        Div("First", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
        Div("Second", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
        Div("Third", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
        cls="h-48 border-2 border-dashed border-primary rounded-md gap-2",
    )


def example_div_centered_horizontal():
    return DivCentered(
        Div("A", cls="bg-secondary px-4 py-2 rounded-md"),
        Div("B", cls="bg-secondary px-4 py-2 rounded-md"),
        Div("C", cls="bg-secondary px-4 py-2 rounded-md"),
        vstack=False,
        cls="h-24 border-2 border-dashed border-primary rounded-md gap-2",
    )


def example_div_aligned():
    return Div(
        Div(
            P("Left Aligned:", cls="text-sm text-muted-foreground mb-2"),
            DivLAligned(
                Div("A", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                Div("B", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                Div("C", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                cls="border-2 border-dashed border-primary rounded-md p-2 gap-2",
            ),
        ),
        Div(
            P("Right Aligned:", cls="text-sm text-muted-foreground mb-2"),
            DivRAligned(
                Div("A", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                Div("B", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                Div("C", cls="bg-primary text-primary-foreground px-3 py-1 rounded"),
                cls="border-2 border-dashed border-primary rounded-md p-2 gap-2",
            ),
        ),
        cls="space-y-4"
    )


def example_div_stacked():
    return Div(
        Div(
            P("Vertical Stack:", cls="text-sm text-muted-foreground mb-2"),
            DivVStacked(
                Div("Top", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                Div("Middle", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                Div("Bottom", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                cls="border-2 border-dashed border-primary rounded-md p-4 gap-2",
            ),
        ),
        Div(
            P("Horizontal Stack:", cls="text-sm text-muted-foreground mb-2"),
            DivHStacked(
                Div("Left", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                Div("Center", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                Div("Right", cls="bg-primary text-primary-foreground px-4 py-2 rounded-md"),
                cls="border-2 border-dashed border-primary rounded-md p-4 gap-2",
            ),
        ),
        cls="grid grid-cols-2 gap-4"
    )


def example_flex_types():
    return Div(
        P("FlexT provides flexbox utility classes:"),
        Div(
            Div(
                P("FlexT.between + FlexT.middle", cls="text-xs text-muted-foreground"),
                Div(
                    Div("A", cls="bg-secondary px-2 py-1 rounded"),
                    Div("B", cls="bg-secondary px-2 py-1 rounded"),
                    Div("C", cls="bg-secondary px-2 py-1 rounded"),
                    cls=cn(FlexT.block, FlexT.between, FlexT.middle, "h-12 border rounded p-2"),
                ),
            ),
            Div(
                P("FlexT.column + FlexT.center", cls="text-xs text-muted-foreground"),
                Div(
                    Div("1", cls="bg-secondary px-2 py-1 rounded"),
                    Div("2", cls="bg-secondary px-2 py-1 rounded"),
                    cls=cn(FlexT.block, FlexT.column, FlexT.center, "border rounded p-2 gap-2"),
                ),
            ),
            cls="grid grid-cols-2 gap-4"
        ),
        cls="space-y-2"
    )


page = Div(
    H1("Layout Components"),
    P(
        "Layout components for building responsive, well-structured page layouts. "
        "These components provide common layout patterns using flexbox and grid."
    ),
    TitledSection(
        "Design Philosophy",
        P("The layout components follow these principles:"),
        Ul(
            Li("Smart defaults with full customization via cls parameter"),
            Li("Responsive grid that adapts to content and screen size"),
            Li("Semantic naming that describes layout intent"),
            Li("Composable patterns that work together"),
        ),
    ),
    TitledSection(
        "Container",
        P("A max-width container with automatic horizontal centering:"),
        ComponentShowcase(example_container),
    ),
    TitledSection(
        "Container Sizes",
        P("ContainerT enum provides different max-width constraints:"),
        ComponentShowcase(example_container_sizes),
    ),
    TitledSection(
        "Center",
        P("Centers content both vertically and horizontally:"),
        ComponentShowcase(example_center),
    ),
    TitledSection(
        "Center Options",
        P("Control vertical and horizontal centering independently:"),
        ComponentShowcase(example_center_options),
    ),
    TitledSection(
        "Grid",
        P("Responsive grid with smart column defaults based on content:"),
        ComponentShowcase(example_grid),
    ),
    TitledSection(
        "Grid Column Control",
        P("Override automatic column calculation with fixed values:"),
        ComponentShowcase(example_grid_cols),
    ),
    TitledSection(
        "DivFullySpaced",
        P("Distributes items with maximum space between them:"),
        ComponentShowcase(example_div_fully_spaced),
    ),
    TitledSection(
        "DivCentered",
        P("Centers items with vertical stacking by default:"),
        ComponentShowcase(example_div_centered),
    ),
    TitledSection(
        "DivCentered Horizontal",
        P("Use vstack=False for horizontal centering:"),
        ComponentShowcase(example_div_centered_horizontal),
    ),
    TitledSection(
        "DivLAligned & DivRAligned",
        P("Align items to left or right edges:"),
        ComponentShowcase(example_div_aligned),
    ),
    TitledSection(
        "DivVStacked & DivHStacked",
        P("Stack items vertically or horizontally:"),
        ComponentShowcase(example_div_stacked),
    ),
    TitledSection(
        "FlexT Enum",
        P("Low-level flexbox utilities for custom layouts:"),
        ComponentShowcase(example_flex_types),
    ),
    TitledSection(
        "API Reference",
        CodeBlock(
            """
# Container
def Container(
    *c,                                     # Contents
    cls="mt-5 container-xl",                # Additional classes
    **kwargs                                # Additional HTML attributes
) -> HtmlString

class ContainerT(VEnum):
    xs, sm, lg, xl, expand                  # Container size variants

# Centering
def Center(
    *c,                                     # Components to center
    vertical: bool = True,                  # Center vertically
    horizontal: bool = True,                # Center horizontally
    cls="",                                 # Additional classes
    **kwargs
) -> HtmlString

# Grid
def Grid(
    *div,                                   # Grid items
    cols_min: int = 1,                      # Min columns at any screen
    cols_max: int = 4,                      # Max columns allowed
    cols_sm: int = None,                    # Columns on small screens
    cols_md: int = None,                    # Columns on medium screens
    cols_lg: int = None,                    # Columns on large screens
    cols_xl: int = None,                    # Columns on extra large screens
    cols: int = None,                       # Fixed columns (overrides responsive)
    cls="gap-4",                            # Gap and other classes
    **kwargs
) -> HtmlString

# Flex Layouts
def DivFullySpaced(*c, cls="w-full", **kwargs) -> HtmlString
    # Items spaced with justify-between

def DivCentered(*c, cls="space-y-4", vstack=True, **kwargs) -> HtmlString
    # Items centered, optionally stacked

def DivLAligned(*c, cls="space-x-4", **kwargs) -> HtmlString
    # Items aligned left

def DivRAligned(*c, cls="space-x-4", **kwargs) -> HtmlString
    # Items aligned right

def DivVStacked(*c, cls="space-y-4", **kwargs) -> HtmlString
    # Items stacked vertically

def DivHStacked(*c, cls="space-x-4", **kwargs) -> HtmlString
    # Items stacked horizontally

# FlexT Enum - Flexbox utilities
class FlexT(VEnum):
    # Display
    block = "flex"
    inline = "inline-flex"

    # Horizontal alignment
    left, center, right, between, around

    # Vertical alignment
    stretch, top, middle, bottom

    # Direction
    row, row_reverse, column, column_reverse

    # Wrap
    nowrap, wrap, wrap_reverse
""",
            code_cls="language-python",
        ),
    ),
    BackLink(),
    id="content"
)


@router.get("/xtras/layouts")
@template(title="Layout Components Documentation")
def layouts_docs():
    return page


@on("page.layouts")
async def get_layouts(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.layouts")
