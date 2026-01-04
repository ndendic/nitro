import rusty_tags as rt
from rusty_tags import HtmlString, Div
from enum import auto
from .utils import cn
from .base import VEnum


class ContainerT(VEnum):
    "Max width container sizes from https://franken-ui.dev/docs/container"

    def _generate_next_value_(name, start, count, last_values):
        return f"text-{name}"

    xs = auto()
    sm = auto()
    lg = auto()
    xl = auto()
    expand = auto()

def Container(
    *c,  # Contents of Container tag (often other HtmlString Components)
    cls=cn("mt-5", ContainerT.xl),  # Classes in addition to Container styling
    **kwargs,  # Additional args for Container (`Div` tag)
) -> HtmlString:  # Container(..., cls='container')
    "Div to be used as a container that often wraps large sections or a page of content"
    return Div(*c, cls=cn("container", cn(cls)), **kwargs)

def Center(
    *c,  # Components to center
    vertical: bool = True,  # Whether to center vertically
    horizontal: bool = True,  # Whether to center horizontally
    cls="",  # Additional classes
    **kwargs,  # Additional args for container div
) -> HtmlString:  # Div with centered contents
    "Centers contents both vertically and horizontally by default"
    classes = ["flex"]
    if vertical:
        classes.append("items-center min-h-full")
    if horizontal:
        classes.append("justify-center min-w-full")
    return Div(*c, cls=cn(cn(classes), cn(cls)), **kwargs)



class FlexT(VEnum):
    "Flexbox modifiers using Tailwind CSS"

    def _generate_next_value_(name, start, count, last_values):
        return name

    # Display
    block = "flex"
    inline = "inline-flex"

    # Horizontal Alignment
    left = "justify-start"
    center = "justify-center"
    right = "justify-end"
    between = "justify-between"
    around = "justify-around"

    # Vertical Alignment
    stretch = "items-stretch"
    top = "items-start"
    middle = "items-center"
    bottom = "items-end"

    # Direction
    row = "flex-row"
    row_reverse = "flex-row-reverse"
    column = "flex-col"
    column_reverse = "flex-col-reverse"

    # Wrap
    nowrap = "flex-nowrap"
    wrap = "flex-wrap"
    wrap_reverse = "flex-wrap-reverse"



def Grid(
    *div,  # `Div` components to put in the grid
    cols_min: int = 1,  # Minimum number of columns at any screen size
    cols_max: int = 4,  # Maximum number of columns allowed at any screen size
    cols_sm: int = None,  # Number of columns on small screens
    cols_md: int = None,  # Number of columns on medium screens
    cols_lg: int = None,  # Number of columns on large screens
    cols_xl: int = None,  # Number of columns on extra large screens
    cols: int = None,  # Number of columns on all screens
    cls="gap-4",  # Additional classes on the grid (tip: `gap` provides spacing for grids)
    **kwargs,  # Additional args for `Div` tag
) -> HtmlString:  # Responsive grid component
    "Creates a responsive grid layout with smart defaults based on content"
    if cols:
        cols_min = cols_sm = cols_md = cols_lg = cols_xl = cols
    else:
        n = len(div)
        cols_max = min(n, cols_max)
        cols_sm = cols_sm or min(n, cols_min, cols_max)
        cols_md = cols_md or min(n, cols_min + 1, cols_max)
        cols_lg = cols_lg or min(n, cols_min + 2, cols_max)
        cols_xl = cols_xl or cols_max
    return Div(
        *div,
        cls=cn(
            f"grid grid-cols-{cols_min} sm:grid-cols-{cols_sm} md:grid-cols-{cols_md} lg:grid-cols-{cols_lg} xl:grid-cols-{cols_xl}",
            cls,
        ),
        **kwargs,
    )



def DivFullySpaced(
    *c,  # Components
    cls="w-full",  # Classes for outer div (`w-full` makes it use all available width)
    **kwargs,  # Additional args for outer div
):  # Div with spaced components via flex classes
    "Creates a flex div with it's components having as much space between them as possible"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(FlexT.block, FlexT.between, FlexT.middle, cls),
        **kwargs,
    )



def DivCentered(
    *c,  # Components
    cls="space-y-4",  # Classes for outer div (`space-y-4` provides spacing between components)
    vstack=True,  # Whether to stack the components vertically
    **kwargs,  # Additional args for outer div
) -> HtmlString:  # Div with components centered in it
    "Creates a flex div with it's components centered in it"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(
            FlexT.block,
            (FlexT.column if vstack else FlexT.row),
            FlexT.middle,
            FlexT.center,
            cls,
        ),
        **kwargs,
    )



def DivLAligned(
    *c,  # Components
    cls="space-x-4",  # Classes for outer div
    **kwargs,  # Additional args for outer div
) -> HtmlString:  # Div with components aligned to the left
    "Creates a flex div with it's components aligned to the left"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(FlexT.block, FlexT.left, FlexT.middle, cls),
        **kwargs,
    )



def DivRAligned(
    *c,  # Components
    cls="space-x-4",  # Classes for outer div
    **kwargs,  # Additional args for outer div
) -> HtmlString:  # Div with components aligned to the right
    "Creates a flex div with it's components aligned to the right"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(FlexT.block, FlexT.right, FlexT.middle, cls),
        **kwargs,
    )



def DivVStacked(
    *c,  # Components
    cls="space-y-4",  # Additional classes on the div  (tip: `space-y-4` provides spacing between components)
    **kwargs,  # Additional args for the div
) -> HtmlString:  # Div with components stacked vertically
    "Creates a flex div with it's components stacked vertically"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(FlexT.block, FlexT.column, FlexT.middle, cls),
        **kwargs,
    )


def DivHStacked(
    *c,  # Components
    cls="space-x-4",  # Additional classes on the div (`space-x-4` provides spacing between components)
    **kwargs,  # Additional args for the div
) -> HtmlString:  # Div with components stacked horizontally
    "Creates a flex div with it's components stacked horizontally"
    cls = cn(cls)
    return Div(
        *c,
        cls=cn(FlexT.block, FlexT.row, FlexT.middle, cls),
        **kwargs,
    )
