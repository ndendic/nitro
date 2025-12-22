from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from .templates.base import *  # noqa: F403

router: APIRouter = APIRouter()

@router.get("/playground_components")
@template(title="Playground Components")
def playground_components():
    state = Signals()
    return Div(
        H1("Playground", style="animation: var(--animation-fade-in) forwards;"),
        Div(
            H2("Basecoat Components"),
            P("This is a paragraph", cls="paragraph"),
            H3("This is a heading 3"),
            P("This is a blockquote", cls="blockquote"),
            H4("This is a heading 4"),
            P("This is a leading paragraph", cls="text-lead"),
            A("This is a link", href="https://www.google.com", cls="link"),
            P("This is a meta paragraph", cls="text-meta"),
            P("This is a background paragraph", cls="text-background"),

            H2("Hero Components", cls="h2"),
            H2("This is a hero 1", cls="hero-sm"),
            H2("This is a hero 2", cls="hero-md"),
            H2("This is a hero 3", cls="hero-lg"),
            H2("This is a hero 4", cls="hero-xl"),
            H2("This is a hero 5", cls="hero-2xl"),
            H2("This is a hero 6", cls="hero-3xl"),

            H2("Basecoat Layouts", cls="h2 mb-4"),

            Grid(
                Container(
                    P("This is a container"),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivCentered(
                    P("This is a centered container"),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivVStacked(
                    P("This is a"),
                    P("vertically "),
                    P("stacked container"),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivHStacked(
                    P("This is a"),
                    P("horizontally "),
                    P("stacked container"),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivFullySpaced(
                    P("This is a"),
                    P("fully spaced container"),
                    P("stacked container"),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivLAligned(
                    P("This is a left aligned container."),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
                DivRAligned(
                    P("This is a right aligned container."),
                    cls="border-2 border-primary rounded-md p-4 h-32",
                ),
            )
        ),
        signals=state,
    )