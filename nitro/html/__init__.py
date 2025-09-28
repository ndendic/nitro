from rusty_tags import *
from .template import Page, create_template, page_template


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
    # Template utilities
    "Page", "create_template", "page_template",
]