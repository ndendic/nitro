from typing import Any, Optional
import rusty_tags as rt
from .utils import cn
from .icons import LucideIcon


def Accordion(
    *children,
    name: Optional[str] = None,
    cls: str = "",
    **attrs: Any,
) -> rt.HtmlString:
    """
    Simple accordion container. When `name` is provided, only one child
    AccordionItem with that name can be open at a time (native HTML behavior).
    """
    # If accordion has a name, apply it to children that don't have one
    if name:
        processed_children = []
        for child in children:
            # If child is AccordionItem without name, add the accordion name
            if (
                hasattr(child, "tag")
                and child.tag == "details"
                and "name" not in child.attrs
            ):
                child_copy = rt.Details(*child.children, **child.attrs, name=name)
                processed_children.append(child_copy)
            else:
                processed_children.append(child)
        children = processed_children

    return rt.Section(*children, cls=cn("accordion", cls), **attrs)


def AccordionItemTrigger(
    title,
    icon="chevron-down",
    cls="",
    icon_cls="",
    **attrs: Any,
) -> rt.HtmlString:
    return rt.H2(
        title,
        LucideIcon(
            icon,
            cls=icon_cls,
        ),
        cls=cls,
        **attrs,
    )


def AccordionItem(
    trigger_content,
    *children,
    open: bool = False,
    name: Optional[str] = None,
    cls: str = "group border-b last:border-b-0",
    summary_cls="w-full focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] transition-all outline-none rounded-md",
    hide_marker: bool = True,
    **attrs: Any,
) -> rt.HtmlString:
    """Individual accordion item using HTML details/summary."""
    details_attrs = {"cls": cn("accordion-item", cls), "open": open, **attrs}

    # Add name attribute for grouping behavior
    if name:
        details_attrs["name"] = name

    return rt.Details(
        rt.Summary(
            AccordionItemTrigger(trigger_content)
            if isinstance(trigger_content, str)
            else trigger_content,
            cls=cn("accordion-trigger", summary_cls),
            style=f"list-style: none;" if hide_marker else "",
        ),
        rt.Div(*children, cls="accordion-content"),
        **details_attrs,
    )
