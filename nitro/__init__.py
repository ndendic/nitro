# Re-export everything from rusty-tags core
from rusty_tags import *

# Import framework-specific components
from .templates import Page, create_template, page_template
from .utils import show, AttrDict, uniq
from .client import Client
from .events import *
from .datastar import *

__author__ = "Nikola Dendic"
__description__ = "Booster add-on for your favourite web-framework. Built on rusty-tags core."

__all__ = [
    # Core HTML/SVG tags and utilities (re-exported from rusty-tags)
    "HtmlString", "TagBuilder", "CustomTag",
    "A", "Aside", "B", "Body", "Br", "Button", "Code", "Div", "Em", "Form",
    "H1", "H2", "H3", "H4", "H5", "H6", "Head", "Header", "Html", "I", "Img",
    "Input", "Label", "Li", "Link", "Main", "Nav", "P", "Script", "Section",
    "Span", "Strong", "Table", "Td", "Th", "Title", "Tr", "Ul", "Ol",
    "Svg", "Circle", "Rect", "Line", "Path", "Polygon", "Polyline", "Ellipse",
    "Text", "G", "Defs", "Use", "Symbol", "Marker", "LinearGradient", "RadialGradient",
    "Stop", "Pattern", "ClipPath", "Mask", "Image", "ForeignObject",
    "Meta", "Hr", "Iframe", "Textarea", "Select", "Figure", "Figcaption",
    "Article", "Footer", "Details", "Summary", "Address",
    "Tbody", "Thead", "Tfoot", "Caption", "Col", "Colgroup",
    "Abbr", "Area", "Audio", "Base", "Bdi", "Bdo", "Blockquote", "Canvas", "Cite",
    "Data", "Datalist", "Dd", "Del", "Dfn", "Dialog", "Dl", "Dt", "Embed", "Fieldset",
    "Hgroup", "Ins", "Kbd", "Legend", "Map", "Mark", "Menu", "Meter", "Noscript",
    "Object", "Optgroup", "OptionEl", "Option", "Picture", "Pre", "Progress", "Q", "Rp", "Rt",
    "Ruby", "S", "Samp", "Small", "Source", "Style", "Sub", "Sup", "Template", "Time",
    "Track", "U", "Var", "Video", "Wbr",

    # Framework-specific utilities
    "Page", "create_template", "page_template", "show", "AttrDict", "uniq",
    "Client",

    # Event system
    "Namespace", "ANY", "default_namespace", "event", "on", "emit", "emit_async", "Event",

    # Datastar integration
    "DS", "signals", "Signals", "reactive_class", "attribute_generator",
    "SSE", "ElementPatchMode", "EventType",
]