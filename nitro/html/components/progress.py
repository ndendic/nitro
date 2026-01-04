"""Progress bar component.

A simple progress bar with determinate and indeterminate modes.
Uses Tailwind utility classes for styling (no custom CSS required).
"""

from typing import Any, Literal, Optional, Union
from rusty_tags import Div, HtmlString
from rusty_tags.datastar import Signal
from .utils import cn

ProgressSize = Literal["sm", "md", "lg"]

# Size mapping for progress bar height
SIZE_CLASSES = {
    "sm": "h-1",
    "md": "h-2",
    "lg": "h-4",
}


def Progress(
    value: Union[int, float, Signal, None] = None,
    max_value: int = 100,
    indeterminate: bool = False,
    size: ProgressSize = "md",
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Progress bar component.

    A progress indicator that shows completion status. Supports both
    determinate (specific percentage) and indeterminate (unknown duration) modes.

    Args:
        value: Current progress value (0 to max_value). Can be:
            - int/float: Static progress value
            - Signal: Datastar signal for reactive updates
            - None: Required for indeterminate mode
        max_value: Maximum value for progress calculation (default 100)
        indeterminate: If True, shows animated loading state
        size: Bar height - "sm" (h-1), "md" (h-2), "lg" (h-4)
        cls: Additional CSS classes for the container
        **attrs: Additional HTML attributes

    Returns:
        HtmlString: Rendered progress bar element

    Example:
        # Static progress
        Progress(value=65)

        # Different sizes
        Progress(value=50, size="sm")
        Progress(value=50, size="lg")

        # Indeterminate loading
        Progress(indeterminate=True)

        # With Datastar signal for reactive updates
        progress_signal = Signal("progress", 0)
        Progress(value=progress_signal)
    """
    height_cls = SIZE_CLASSES.get(size, SIZE_CLASSES["md"])

    # Container classes (track)
    container_cls = cn(
        "progress",
        height_cls,
        cls,
    )

    # Calculate width for determinate mode
    if indeterminate:
        # Indeterminate mode: animated bar using inline keyframe animation
        indicator_cls = "progress-indicator"
        # Use inline style for animation since custom Tailwind classes may not be available
        indicator_style = "width: 40%; animation: progress-indeterminate 1.5s ease-in-out infinite; left: -40%;"
        aria_valuenow = None
    elif isinstance(value, Signal):
        # Reactive mode with Datastar signal
        indicator_cls = "progress-indicator"
        # Use text binding for dynamic width
        indicator_style = None
        width_expr = f"width: ${{{value._name}}}%"
        attrs["data_style"] = width_expr
        aria_valuenow = None
    else:
        # Static determinate mode
        percentage = min(100, max(0, (value or 0) / max_value * 100))
        indicator_cls = "progress-indicator"
        indicator_style = f"width: {percentage}%;"
        aria_valuenow = value


    # Build indicator element
    indicator_attrs = {"cls": indicator_cls}
    if indicator_style:
        indicator_attrs["style"] = indicator_style

    # Build container with ARIA attributes
    container_attrs = dict(attrs)
    container_attrs["role"] = "progressbar"
    container_attrs["aria_valuemin"] = "0"
    container_attrs["aria_valuemax"] = str(max_value)
    if aria_valuenow is not None:
        container_attrs["aria_valuenow"] = str(aria_valuenow)
    if indeterminate:
        container_attrs["aria_busy"] = "true"

    # Handle reactive value with Datastar
    if isinstance(value, Signal):
        return Div(
            Div(
                cls=indicator_cls,
                data_style=f"'width: ' + ${value._name} + '%'",
            ),
            cls=container_cls,
            data_size=size,
            **container_attrs,
        )
    else:
        return Div(
            Div(**indicator_attrs),
            cls=container_cls,
            data_size=size,
            **container_attrs,
        )
