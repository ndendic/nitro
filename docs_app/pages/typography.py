"""Typography component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import *
from nitro.infrastructure.html.components.base import (
    H1, H2, H3, H4, H5, H6, Subtitle, Q, Em, Strong, I, Small, Mark, Del, Ins,
    Sub, Sup, Blockquote, Caption, Cite, Time, Address, Abbr, Dfn, Kbd, Samp,
    Var, Figure, Data, Meter, S, U, Output, TextT, TextPresets
)

router: APIRouter = APIRouter()


def example_headings():
    return Div(
        H1("Heading 1"),
        H2("Heading 2"),
        H3("Heading 3"),
        H4("Heading 4"),
        H5("Heading 5"),
        H6("Heading 6"),
        cls="space-y-2"
    )


def example_subtitle():
    return Div(
        H2("Main Title"),
        Subtitle("This is a subtitle that appears below the main heading"),
        cls="space-y-1"
    )


def example_text_styles():
    return Div(
        P(Em("Emphasized text"), " - for stress emphasis"),
        P(Strong("Strong text"), " - for importance"),
        P(I("Italic text"), " - for technical terms, foreign phrases"),
        P(Small("Small text"), " - for fine print, side comments"),
        P(Mark("Highlighted text"), " - for relevance"),
        cls="space-y-2"
    )


def example_text_modifications():
    return Div(
        P(Del("Deleted text"), " - shows removed content"),
        P(Ins("Inserted text"), " - shows added content"),
        P(S("Strikethrough text"), " - for no longer accurate info"),
        P(U("Underlined text"), " - for proper names, misspellings"),
        cls="space-y-2"
    )


def example_subscript_superscript():
    return Div(
        P("Water formula: H", Sub("2"), "O"),
        P("E = mc", Sup("2")),
        P("The 1", Sup("st"), " of January"),
        cls="space-y-2"
    )


def example_quotations():
    return Div(
        P("The author said ", Q("This is an inline quote"), " in the interview."),
        Blockquote(
            "This is a blockquote. It's perfect for longer quotations that need "
            "to stand out from the surrounding text and provide visual emphasis."
        ),
        cls="space-y-4"
    )


def example_citations():
    return Div(
        P("According to ", Cite("The Design of Everyday Things"), " by Don Norman..."),
        P("Source: ", Cite("Python Documentation"), ", section 4.2"),
        cls="space-y-2"
    )


def example_time_address():
    return Div(
        P("Event date: ", Time("December 25, 2024", datetime="2024-12-25")),
        Address(
            "John Doe",
            Br(),
            "123 Main Street",
            Br(),
            "San Francisco, CA 94102"
        ),
        cls="space-y-4"
    )


def example_abbreviations():
    return Div(
        P(
            "The ",
            Abbr("HTML", title="HyperText Markup Language"),
            " specification is maintained by the ",
            Abbr("W3C", title="World Wide Web Consortium"),
            "."
        ),
        P(
            "We use ",
            Abbr("CSS", title="Cascading Style Sheets"),
            " for styling."
        ),
        cls="space-y-2"
    )


def example_definitions():
    return Div(
        P(
            Dfn("Entity"),
            " - A domain object with identity and lifecycle."
        ),
        P(
            Dfn("Repository"),
            " - An abstraction for data persistence operations."
        ),
        cls="space-y-2"
    )


def example_code_elements():
    return Div(
        P("Press ", Kbd("Ctrl"), " + ", Kbd("C"), " to copy."),
        P("Keyboard shortcut: ", Kbd("Cmd"), " + ", Kbd("Shift"), " + ", Kbd("P")),
        P("Sample output: ", Samp("Hello, World!")),
        P("The variable ", Var("x"), " represents the input value."),
        cls="space-y-2"
    )


def example_figure():
    return Figure(
        Img(
            src="https://picsum.photos/400/200",
            alt="Sample placeholder image",
            cls="rounded-md"
        ),
        Caption("Figure 1: A sample placeholder image from Picsum"),
    )


def example_data_meter():
    return Div(
        P("Data element: ", Data("42", value="42"), " items in stock"),
        Div(
            P("Progress: 70%"),
            Meter(value=0.7, min=0, max=1),
            cls="space-y-1"
        ),
        Div(
            P("Battery: 30%"),
            Meter(value=0.3, min=0, max=1),
            cls="space-y-1"
        ),
        cls="space-y-4"
    )


def example_output():
    return Div(
        P("Calculation result: ", Output("42")),
        P("Form output: ", Output("Success!", form="my-form")),
        cls="space-y-2"
    )


def example_text_types():
    return Div(
        P("Muted text", cls=str(TextT.muted)),
        P("Primary text", cls=str(TextT.primary)),
        P("Lead text", cls=str(TextT.lead)),
        P("Meta text", cls=str(TextT.meta)),
        P("Bold text", cls=str(TextT.bold)),
        P("Italic text", cls=str(TextT.italic)),
        cls="space-y-2"
    )


def example_text_presets():
    return Div(
        P("Muted small text", cls=str(TextPresets.muted_sm)),
        P("Muted large text", cls=str(TextPresets.muted_lg)),
        P("Bold small text", cls=str(TextPresets.bold_sm)),
        P("Bold large text", cls=str(TextPresets.bold_lg)),
        cls="space-y-2"
    )


page = Div(
    H1("Typography Components"),
    P(
        "A comprehensive set of typography components for semantic HTML text "
        "formatting. These components provide consistent styling while maintaining "
        "proper semantic meaning."
    ),
    TitledSection(
        "Design Philosophy",
        P("The typography components follow these principles:"),
        Ul(
            Li("Semantic HTML elements with appropriate default styling"),
            Li("Consistent integration with Tailwind CSS utilities"),
            Li("Support for dark mode through CSS variables"),
            Li("Composable with other components via cls parameter"),
        ),
    ),
    TitledSection(
        "Headings",
        P("Six heading levels for document structure:"),
        ComponentShowcase(example_headings),
    ),
    TitledSection(
        "Subtitle",
        P("Styled muted text designed to appear below headings:"),
        ComponentShowcase(example_subtitle),
    ),
    TitledSection(
        "Text Styles",
        P("Semantic text styling components:"),
        ComponentShowcase(example_text_styles),
    ),
    TitledSection(
        "Text Modifications",
        P("Components for showing content changes:"),
        ComponentShowcase(example_text_modifications),
    ),
    TitledSection(
        "Subscript & Superscript",
        P("For chemical formulas, mathematical expressions, and ordinals:"),
        ComponentShowcase(example_subscript_superscript),
    ),
    TitledSection(
        "Quotations",
        P("Inline quotes and block quotations:"),
        ComponentShowcase(example_quotations),
    ),
    TitledSection(
        "Citations",
        P("For citing sources and references:"),
        ComponentShowcase(example_citations),
    ),
    TitledSection(
        "Time & Address",
        P("Semantic elements for dates and contact information:"),
        ComponentShowcase(example_time_address),
    ),
    TitledSection(
        "Abbreviations",
        P("Abbreviations with tooltip explanations:"),
        ComponentShowcase(example_abbreviations),
    ),
    TitledSection(
        "Definitions",
        P("For defining terms:"),
        ComponentShowcase(example_definitions),
    ),
    TitledSection(
        "Code Elements",
        P("Keyboard inputs, sample output, and variables:"),
        ComponentShowcase(example_code_elements),
    ),
    TitledSection(
        "Figure & Caption",
        P("For images and illustrations with captions:"),
        ComponentShowcase(example_figure),
    ),
    TitledSection(
        "Data & Meter",
        P("For machine-readable data and progress indicators:"),
        ComponentShowcase(example_data_meter),
    ),
    TitledSection(
        "Output",
        P("For form calculation results:"),
        ComponentShowcase(example_output),
    ),
    TitledSection(
        "Text Types (TextT Enum)",
        P("Predefined text style classes:"),
        ComponentShowcase(example_text_types),
    ),
    TitledSection(
        "Text Presets",
        P("Common typography combinations:"),
        ComponentShowcase(example_text_presets),
    ),
    TitledSection(
        "API Reference",
        CodeBlock(
            """
# Headings
def H1(*c, cls="h1", **kwargs) -> HtmlString
def H2(*c, cls="h2", **kwargs) -> HtmlString
def H3(*c, cls="h3", **kwargs) -> HtmlString
def H4(*c, cls="h4", **kwargs) -> HtmlString
def H5(*c, cls="h5", **kwargs) -> HtmlString
def H6(*c, cls="h6", **kwargs) -> HtmlString

# Subtitle
def Subtitle(*c, cls="mt-1.5", **kwargs) -> HtmlString

# Text Styles
def Q(*c, cls="q", **kwargs) -> HtmlString              # Inline quote
def Em(*c, cls="", **kwargs) -> HtmlString              # Emphasis
def Strong(*c, cls="", **kwargs) -> HtmlString          # Strong importance
def I(*c, cls="", **kwargs) -> HtmlString               # Italic
def Small(*c, cls="", **kwargs) -> HtmlString           # Small text
def Mark(*c, cls="", **kwargs) -> HtmlString            # Highlighted
def Del(*c, cls="", **kwargs) -> HtmlString             # Deleted
def Ins(*c, cls="", **kwargs) -> HtmlString             # Inserted
def Sub(*c, cls="", **kwargs) -> HtmlString             # Subscript
def Sup(*c, cls="", **kwargs) -> HtmlString             # Superscript
def S(*c, cls="", **kwargs) -> HtmlString               # Strikethrough
def U(*c, cls="", **kwargs) -> HtmlString               # Underline

# Quotations & Citations
def Blockquote(*c, cls="", **kwargs) -> HtmlString
def Cite(*c, cls="", **kwargs) -> HtmlString
def Caption(*c, cls="", **kwargs) -> HtmlString

# Semantic Elements
def Time(*c, cls="", datetime=None, **kwargs) -> HtmlString
def Address(*c, cls="", **kwargs) -> HtmlString
def Abbr(*c, cls="", title=None, **kwargs) -> HtmlString
def Dfn(*c, cls="", **kwargs) -> HtmlString

# Code Elements
def Kbd(*c, cls="", **kwargs) -> HtmlString             # Keyboard input
def Samp(*c, cls="", **kwargs) -> HtmlString            # Sample output
def Var(*c, cls="", **kwargs) -> HtmlString             # Variable

# Data Elements
def Figure(*c, cls="", **kwargs) -> HtmlString
def Data(*c, value=None, cls="", **kwargs) -> HtmlString
def Meter(*c, value=None, min=None, max=None, cls="", **kwargs) -> HtmlString
def Output(*c, form=None, for_=None, cls="", **kwargs) -> HtmlString

# Text Type Enums
class TextT(VEnum):
    # Style: lead, meta, gray, italic
    # Size: xs, sm, lg, xl
    # Weight: light, normal, medium, bold, extrabold
    # Color: muted, primary, secondary, success, warning, error, info
    # Alignment: left, right, center, justify, start, end
    # Other: truncate, break_, nowrap, underline, highlight

class TextPresets(VEnum):
    muted_sm, muted_lg, bold_sm, bold_lg, md_weight_sm, md_weight_muted
""",
            code_cls="language-python",
        ),
    ),
    BackLink(),
    id="content"
)


@router.get("/xtras/typography")
@template(title="Typography Components Documentation")
def typography_docs():
    return page


@on("page.typography")
async def get_typography(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.typography")
