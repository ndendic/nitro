"""Tabs component documentation page"""

from .base import *
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from nitro import HtmlString as html

router = APIRouter()


style: html = """
<style>
    .anchor-container {
        background: var(--gray-2);
        border: solid var(--border-size-1);
    }
</style>
"""

@router.get("/playground")
@page(title="Playground", wrap_in=HTMLResponse)
def tabs_docs():
    return Main(
        H1("Playground"),
        style,
        
        Button("Click me", id="myButton", on_mouseenter="$anchorOpen = !$anchorOpen", on_mouseleave__debounce_300ms="$anchorOpen = !$anchorOpen"),
        P("Anchor should appear over this text."),
        Div("default", data_anchor="'#myButton'", show="$anchorOpen", cls="anchor-container"),

        BackLink(),
        
        # signals=Signals(message=""),
    )