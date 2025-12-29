import rusty_tags as rt
from rusty_tags import HtmlString
from enum import Enum, auto
from .utils import cn

class VEnum(Enum):
    def __str__(self):
        return self.value

    def __add__(self, other):
        return cn(self, other)

    def __radd__(self, other):
        return cn(other, self)


class TextT(VEnum):
    "Text Styles"

    def _generate_next_value_(name, start, count, last_values):
        return f"text-{name}"

    paragraph = "paragraph"
    # Text Style
    lead, meta, gray, italic = (
        auto(),
        auto(),
        "text-gray-500 dark:text-gray-200",
        "italic",
    )
    # Text Size
    xs, sm, lg, xl = "text-xs", "text-sm", "text-lg", "text-xl"
    # Text Weight
    light, normal, medium, bold, extrabold = (
        "font-light",
        "font-normal",
        "font-medium",
        "font-bold",
        "font-extrabold",
    )
    # Text Color
    muted, primary, secondary = (
        "text-muted-foreground",
        "text-primary-foreground",
        "text-secondary-foreground",
    )
    success, warning, error, info = (
        "text-success",
        "text-warning",
        "text-error",
        "text-info",
    )
    # Text Alignment
    left, right, center = "text-left", "text-right", "text-center"
    justify, start, end = "text-justify", "text-start", "text-end"
    # Vertical Alignment
    top, middle, bottom = "align-top", "align-middle", "align-bottom"
    # Text Wrapping
    truncate, break_, nowrap = "text-truncate", "text-break", "text-nowrap"
    # other
    underline = "underline"
    highlight = "bg-yellow-200 dark:bg-yellow-800 text-black"


class TextPresets(VEnum):
    "Common Typography Presets"

    muted_sm = TextT.muted + TextT.sm
    muted_lg = TextT.muted + TextT.lg

    bold_sm = TextT.bold + TextT.sm
    bold_lg = TextT.bold + TextT.lg

    md_weight_sm = cn((TextT.sm, TextT.medium))
    md_weight_muted = cn((TextT.medium, TextT.muted))


def H1(
    *c: str | HtmlString,  # Contents of H1 tag (often text)
    cls: Enum | str = "",  # Classes in addition to H1 styling
    **kwargs,  # Additional args for H1 tag
) -> HtmlString:  # H1(..., cls='h1')
    "H1 with styling and appropriate size"
    return rt.H1(*c, cls=cn("h1 mb-4",cls), **kwargs)


def H2(
    *c: str | HtmlString,  # Contents of H2 tag (often text)
    cls: Enum | str = "",  # Classes in addition to H2 styling
    **kwargs,  # Additional args for H2 tag
) -> HtmlString:  # H2(..., cls='h2')
    "H2 with styling and appropriate size"
    return rt.H2(*c, cls=cn("h2",cls), **kwargs)


def H3(
    *c: HtmlString | str,  # Contents of H3 tag (often text)
    cls: Enum | str = "",  # Classes in addition to H3 styling
    **kwargs,  # Additional args for H3 tag
) -> HtmlString:  # H3(..., cls='h3')
    "H3 with styling and appropriate size"
    return rt.H3(*c, cls=cn("h3",cls), **kwargs)


def H4(
    *c: HtmlString | str,  # Contents of H4 tag (often text)
    cls: Enum | str = "",  # Classes in addition to H4 styling
    **kwargs,  # Additional args for H4 tag
) -> HtmlString:  # H4(..., cls='h4')
    "H4 with styling and appropriate size"
    return rt.H4(*c, cls=cn("h4",cls), **kwargs)


def H5(
    *c: HtmlString | str,  # Contents of H5 tag (often text)
    cls: Enum | str = "",  # Classes in addition to H5 styling
    **kwargs,  # Additional args for H5 tag
) -> HtmlString:  # H5(..., cls='text-lg font-semibold')
    "H5 with styling and appropriate size"
    return rt.H5(*c, cls=cn("h5",cls), **kwargs)


def H6(
    *c: HtmlString | str,  # Contents of H6 tag (often text)
    cls: Enum | str = "h6",  # Classes in addition to H6 styling
    **kwargs,  # Additional args for H6 tag
) -> HtmlString:  # H6(..., cls='text-base font-semibold')
    "H6 with styling and appropriate size"
    return rt.H6(*c, cls=cn("text-base font-semibold", cn(cls)), **kwargs)


def Subtitle(
    *c: HtmlString | str,  # Contents of P tag (often text)
    cls: Enum | str = "mt-1.5",  # Additional classes
    **kwargs,  # Additional args for P tag
) -> HtmlString:
    "Styled muted_sm text designed to go under Headings and Titles"
    return rt.P(*c, cls=cn(TextPresets.muted_sm, cn(cls)), **kwargs)


def Q(
    *c: HtmlString | str,  # Contents of Q tag (quote)
    cls: Enum | str = "q",  # Additional classes
    **kwargs,  # Additional args for Q tag
) -> HtmlString:
    "Styled quotation mark"
    return rt.Q(*c, cls=cn(TextT.italic, TextT.lg, cn(cls)), **kwargs)


def Em(
    *c: HtmlString | str,  # Contents of Em tag (emphasis)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Em tag
) -> HtmlString:
    "Styled emphasis text"
    return rt.Em(*c, cls=cn(TextT.medium, cn(cls)), **kwargs)


def Strong(
    *c: HtmlString | str,  # Contents of Strong tag
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Strong tag
) -> HtmlString:
    "Styled strong text"
    return rt.Strong(*c, cls=cn(TextT.bold, cn(cls)), **kwargs)


def I(
    *c: HtmlString | str,  # Contents of I tag (italics)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for I tag
) -> HtmlString:
    "Styled italic text"
    return rt.I(*c, cls=cn(TextT.italic, cn(cls)), **kwargs)


def Small(
    *c: HtmlString | str,  # Contents of Small tag
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Small tag
) -> HtmlString:
    "Styled small text"
    return rt.Small(*c, cls=cn(TextT.sm, cn(cls)), **kwargs)


def Mark(
    *c: HtmlString | str,  # Contents of Mark tag (highlighted text)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Mark tag
) -> HtmlString:
    "Styled highlighted text"
    return rt.Mark(*c, cls=cn(TextT.highlight, cn(cls)), **kwargs)


def Del(
    *c: HtmlString | str,  # Contents of Del tag (deleted text)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Del tag
) -> HtmlString:
    "Styled deleted text"
    return rt.Del(*c, cls=cn("line-through", TextT.gray, cn(cls)), **kwargs)


def Ins(
    *c: str | HtmlString,  # Contents of Ins tag (inserted text)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Ins tag
) -> HtmlString:
    "Styled inserted text"
    return rt.Ins(*c, cls=cn(TextT.underline + " text-green-600", cn(cls)), **kwargs)


def Sub(
    *c: HtmlString | str,  # Contents of Sub tag (subscript)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Sub tag
) -> HtmlString:
    "Styled subscript text"
    return rt.Sub(*c, cls=cn(TextT.sm + " -bottom-1 relative", cn(cls)), **kwargs)


def Sup(
    *c: HtmlString | str,  # Contents of Sup tag (superscript)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Sup tag
) -> HtmlString:
    "Styled superscript text"
    return rt.Sup(*c, cls=cn(TextT.sm + " -top-1 relative", cn(cls)), **kwargs)


def Blockquote(
    *c: str | HtmlString,  # Contents of Blockquote tag (often text)
    cls: Enum | str = "",  # Classes in addition to Blockquote styling
    **kwargs,  # Additional args for Blockquote tag
) -> HtmlString:  # Blockquote(..., cls='blockquote')
    "Blockquote with Styling"
    return rt.Blockquote(*c, cls=cn("blockquote", cn(cls)), **kwargs)


def Caption(*c: str | HtmlString, cls: Enum | str = "", **kwargs) -> HtmlString:
    "Styled caption text"
    return rt.Caption(rt.Span(*c, cls=cn(TextT.gray, TextT.sm, cn(cls))), **kwargs)


def Cite(
    *c: str | HtmlString,  # Contents of Cite tag
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Cite tag
) -> HtmlString:
    "Styled citation text"
    return rt.Cite(*c, cls=cn(TextT.italic, TextT.gray, cn(cls)), **kwargs)


def Time(
    *c: str | HtmlString,  # Contents of Time tag
    cls: Enum | str = "",  # Additional classes
    datetime: str = None,  # datetime attribute
    **kwargs,  # Additional args for Time tag
) -> HtmlString:
    "Styled time element"
    if datetime:
        kwargs["datetime"] = datetime
    return rt.Time(*c, cls=cn(TextT.gray, cn(cls)), **kwargs)


def Address(
    *c: str | HtmlString,  # Contents of Address tag
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Address tag
) -> HtmlString:
    "Styled address element"
    return rt.Address(*c, cls=cn(TextT.italic, cn(cls)), **kwargs)


def Abbr(
    *c: str | HtmlString,  # Contents of Abbr tag
    cls: Enum | str = "",  # Additional classes
    title: str = None,  # Title attribute for abbreviation
    **kwargs,  # Additional args for Abbr tag
) -> HtmlString:
    "Styled abbreviation with dotted underline"
    if title:
        kwargs["title"] = title
    return rt.Abbr(
        *c,
        cls=cn(
            "border-b border-dotted border-secondary hover:cursor-help",
            cn(cls),
        ),
        **kwargs,
    )


def Dfn(
    *c: str | HtmlString,  # Contents of Dfn tag (definition)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Dfn tag
) -> HtmlString:
    "Styled definition term with italic and medium weight"
    return rt.Dfn(
        *c,
        cls=cn(TextT.medium + TextT.italic + TextT.gray, cn(cls)),
        **kwargs,
    )


def Kbd(
    *c: str | HtmlString,  # Contents of Kbd tag (keyboard input)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Kbd tag
) -> HtmlString:
    "Styled keyboard input with subtle background"
    return rt.Kbd(
        *c,
        cls=cn(
            "font-mono px-1.5 py-0.5 text-sm bg-secondary border border-gray-300 dark:border-gray-600 rounded shadow-sm",
            cn(cls),
        ),
        **kwargs,
    )


def Samp(
    *c: str | HtmlString,  # Contents of Samp tag (sample output)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Samp tag
) -> HtmlString:
    "Styled sample output with subtle background"
    return rt.Samp(
        *c,
        cls=cn("font-mono bg-secondary px-1 rounded", TextT.gray, cn(cls)),
        **kwargs,
    )


def Var(
    *c: str | HtmlString,  # Contents of Var tag (variable)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Var tag
) -> HtmlString:
    "Styled variable with italic monospace"
    return rt.Var(
        *c,
        cls=cn("font-mono", TextT.italic + TextT.gray, cn(cls)),
        **kwargs,
    )


def Figure(
    *c: str | HtmlString,  # Contents of Figure tag
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Figure tag
) -> HtmlString:
    "Styled figure container with card-like appearance"
    return rt.Figure(
        *c,
        cls=cn(
            "p-4 my-4 border border-gray-200 dark:border-gray-800 rounded-lg shadow-sm bg-card",
            cn(cls),
        ),
        **kwargs,
    )

def Data(
    *c: HtmlString | str,  # Contents of Data tag
    value: str = None,  # Value attribute
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Data tag
) -> HtmlString:
    "Styled data element"
    if value:
        kwargs["value"] = value
    return rt.Data(
        *c,
        cls=cn("font-mono text-sm bg-secondary px-1 rounded", cn(cls)),
        **kwargs,
    )


def Meter(
    *c: HtmlString | str,  # Contents of Meter tag
    value: float = None,  # Current value
    min: float = None,  # Minimum value
    max: float = None,  # Maximum value
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Meter tag
) -> HtmlString:
    "Styled meter element"
    if value is not None:
        kwargs["value"] = value
    if min is not None:
        kwargs["min"] = min
    if max is not None:
        kwargs["max"] = max
    return rt.Meter(*c, cls=cn("w-full h-2 bg-secondary rounded", cn(cls)), **kwargs)


def S(
    *c: HtmlString | str,  # Contents of S tag (strikethrough)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for S tag
) -> HtmlString:
    "Styled strikethrough text (different semantic meaning from Del)"
    return rt.S(*c, cls=cn("line-through", TextT.gray, cn(cls)), **kwargs)


def U(
    *c: HtmlString | str,  # Contents of U tag (unarticulated annotation)
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for U tag
) -> HtmlString:
    "Styled underline (for proper names in Chinese, proper spelling etc)"
    return rt.U(*c, cls=cn(TextT.underline, cn(cls)), **kwargs)


def Output(
    *c: HtmlString | str,  # Contents of Output tag
    form: str = None,  # ID of form this output belongs to
    for_: str = None,  # IDs of elements this output is for
    cls: Enum | str = "",  # Additional classes
    **kwargs,  # Additional args for Output tag
) -> HtmlString:
    "Styled output element for form results"
    if form:
        kwargs["form"] = form
    if for_:
        kwargs["for"] = for_  # Note: 'for' is reserved in Python
    return rt.Span(
        *c,
        cls=cn("font-mono bg-secondary px-2 py-1 rounded", cn(cls)),
        **kwargs,
    )


    
def PicSumImg(
    h: int = 200,  # Height in pixels
    w: int = 200,  # Width in pixels
    id: int = None,  # Optional specific image ID to use
    grayscale: bool = False,  # Whether to return grayscale version
    blur: int = None,  # Optional blur amount (1-10)
    **kwargs,  # Additional args for Img tag
) -> HtmlString:  # Img tag with picsum image
    "Creates a placeholder image using https://picsum.photos/"
    url = f"https://picsum.photos"
    if id is not None:
        url = f"{url}/id/{id}"
    url = f"{url}/{w}/{h}"
    if grayscale:
        url = f"{url}?grayscale"
    if blur is not None:
        url = f"{url}{'?' if not grayscale else '&'}blur={max(1, min(10, blur))}"
    return rt.Img(src=url, loading="lazy", **kwargs)