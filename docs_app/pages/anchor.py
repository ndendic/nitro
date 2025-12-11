from .templates.base import *  # noqa: F403
from fastapi.responses import HTMLResponse
from fastapi import APIRouter
router: APIRouter = APIRouter()


@router.get("/anchor")
@page(title="RustyTags Anchor", wrap_in=HTMLResponse)
async def anchor():
    popover_style="background: var(--gray-2); padding: var(--size-1); border-radius: var(--radius-1); border: solid var(--border-size-1);"
    return Main(
        H1("RustyTags Anchor"),
        P("This is a playground for RustyTags."),
        Div(Button("Click me",id="myButton", on_click="$anchorOpen = !$anchorOpen",cls="border border-gray-200 rounded-md p-2", style="width: 300px; height: 100px;"), cls="flex items-center justify-center mt-20"),

        Div("default", data_anchor="'#myButton'", show="$anchorOpen", style=popover_style),
        Div("bottom-start", data_anchor="'#myButton, bottom-start'", show="$anchorOpen", style=popover_style),
        Div("bottom-end", data_anchor="'#myButton, bottom-end'", show="$anchorOpen", style=popover_style),

        Div("top", data_anchor="'#myButton, top'", show="$anchorOpen", style=popover_style),
        Div("top-start", data_anchor="'#myButton, top-start'", show="$anchorOpen", style=popover_style),
        Div("top-end", data_anchor="'#myButton, top-end'", show="$anchorOpen", style=popover_style),

        Div("left", data_anchor="'#myButton, left'", show="$anchorOpen", style=popover_style),
        Div("left-start", data_anchor="'#myButton, left-start'", show="$anchorOpen", style=popover_style),
        Div("left-end", data_anchor="'#myButton, left-end'", show="$anchorOpen", style=popover_style),

        Div("right", data_anchor="'#myButton, right'", show="$anchorOpen", style=popover_style),
        Div("right-start", data_anchor="'#myButton, right-start'", show="$anchorOpen", style=popover_style),
        Div("right-end", data_anchor="'#myButton, right-end'", show="$anchorOpen", style=popover_style),
        
        
        signals=Signals(anchorOpen=False),
    )
