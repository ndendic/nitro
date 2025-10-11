from typing import Any, Optional
from rusty_tags import *
from rusty_tags.datastar import Signals

# Import the native dialog element (capital D is the HTML dialog element)
from rusty_tags import Dialog as native_dialog

default_style = Style("""
.dialog {
    top: 0;
    bottom: 0;
    opacity: 0;
    transition: all;
    transition-behavior: allow-discrete;

    &:is([open],:popover-open) {
      opacity: 100;

      &::backdrop {
        opacity: 100;
      }
      > article {
        scale: 100;
      }

      @starting-style {
        opacity: 0;

        &::backdrop {
          opacity: 0;
        }
        > article {
          scale: 95;
        }
      }
    }
    &::backdrop {
      opacity: 0;
      transition: all;
      transition-behavior: allow-discrete;
    }
  }
};
""")

def Dialog(
    *children: Any,
    id: Optional[str] = None,
    default_open: bool = False,
    modal: bool = True,
    close_on_escape: bool = True,
    close_on_backdrop: bool = True,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Simplified dialog component using standard HTML <dialog> element.
    
    Args:
        *children: Dialog content elements
        id: Dialog ID (generates signal `$<id>_open`)
        default_open: Whether dialog starts open
        modal: Whether to use showModal() vs show()
        close_on_escape: Whether ESC key closes dialog
        close_on_backdrop: Whether clicking backdrop closes dialog
        cls: CSS classes for dialog element
        **attrs: Additional attributes for dialog element
    """
    if not id:
        raise ValueError("Dialog requires an 'id' parameter")
    
    # Convert kebab-case to snake_case for signal name
    signal_name = f"{id.replace('-', '_')}_open"
    
    dialog_attrs = dict(attrs)
    dialog_attrs["id"] = id
    dialog_attrs["cls"] = cls
    dialog_attrs["aria-modal"] = "true" if modal else "false"
    
    # Basic dialog attributes
    if default_open:
        dialog_attrs["open"] = ""
    
    # Handle escape key
    if not close_on_escape:
        dialog_attrs["data_on_keydown"] = (
            "if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); }"
        )
    
    # Handle backdrop clicks
    if not close_on_backdrop:
        dialog_attrs["data_on_click"] = (
            "if (event.target === event.currentTarget) event.preventDefault()"
        )
    
    return native_dialog(
        *children,
        signals=Signals(**{signal_name: default_open}),
        **dialog_attrs,
    )


def DialogTrigger(
    *children: Any,
    dialog_id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that opens a dialog using basic JavaScript API.
    
    Args:
        *children: Button content
        dialog_id: ID of the dialog to open
        cls: CSS classes
        **attrs: Additional button attributes
    """
    button_attrs = dict(attrs)
    button_attrs["cls"] = cls
    button_attrs["type"] = button_attrs.get("type", "button")
    button_attrs["aria-haspopup"] = "dialog"
    button_attrs["aria-controls"] = dialog_id
    
    # Use basic JavaScript to open dialog
    button_attrs["on_click"] = f"document.getElementById('{dialog_id}').showModal()"
    
    return Button(*children, **button_attrs)


def DialogContent(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Content wrapper for dialog body.
    
    Args:
        *children: Content elements
        cls: CSS classes
        **attrs: Additional attributes
    """
    content_attrs = dict(attrs)
    content_attrs["cls"] = cls
    content_attrs["role"] = "document"
    
    return Div(*children, **content_attrs)


def DialogHeader(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Header section for dialog.
    
    Args:
        *children: Header content
        cls: CSS classes
        **attrs: Additional attributes
    """
    header_attrs = dict(attrs)
    header_attrs["cls"] = cls
    
    return Header(*children, **header_attrs)


def DialogTitle(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Title element for dialog.
    
    Args:
        *children: Title content
        cls: CSS classes
        **attrs: Additional attributes
    """
    title_attrs = dict(attrs)
    title_attrs["cls"] = cls
    
    return H2(*children, **title_attrs)


def DialogBody(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Body section for dialog content.
    
    Args:
        *children: Body content
        cls: CSS classes
        **attrs: Additional attributes
    """
    body_attrs = dict(attrs)
    body_attrs["cls"] = cls
    
    return Div(*children, **body_attrs)


def DialogFooter(
    *children: Any,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Footer section for dialog actions.
    
    Args:
        *children: Footer content
        cls: CSS classes
        **attrs: Additional attributes
    """
    footer_attrs = dict(attrs)
    footer_attrs["cls"] = cls
    
    return Footer(*children, **footer_attrs)


def DialogClose(
    *children: Any,
    dialog_id: str,
    cls: str = "",
    **attrs: Any,
) -> HtmlString:
    """Button that closes a dialog using basic JavaScript API.
    
    Args:
        *children: Button content
        dialog_id: ID of the dialog to close
        cls: CSS classes
        **attrs: Additional button attributes
    """
    button_attrs = dict(attrs)
    button_attrs["cls"] = cls
    button_attrs["type"] = button_attrs.get("type", "button")
    
    # Use basic JavaScript to close dialog
    button_attrs["on_click"] = f"document.getElementById('{dialog_id}').close()"
    
    return Button(*children, **button_attrs)