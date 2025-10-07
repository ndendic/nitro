"""Tabs component documentation page"""

from .base import *
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from nitro import HtmlString as html
from rusty_tags.datastar import any as any_, if_
router = APIRouter()

style: html = """
<style>
    .anchor-container {
        background: var(--gray-2);
        display: block;
        border: solid var(--border-size-1);
        padding: var(--size-2);
        transition-behavior: allow-discrete;
    }
</style>
"""

@router.get("/playground")
@page(title="Playground", wrap_in=HTMLResponse)
def tabs_docs():
    state = Signals(btn_open=False, anchor_open=False, name="")
    return Main(
        H1("Playground", style="animation: var(--animation-fade-in) forwards;"),
        style,
        Button("Hover me", 
            id="myButton", 
            on_mouseenter=state.btn_open.toggle(), 
            on_mouseleave__debounce_500ms=state.btn_open.toggle(),
        ),
        P("Anchor should appear over this text."),
        Div("default", data_anchor="'#myButton'", 
            on_mouseenter=state.anchor_open.toggle(),
            on_mouseleave__debounce_300ms=state.anchor_open.toggle(), 
            show=any_(state.btn_open, state.anchor_open),
            data_class_open=any_(state.btn_open, state.anchor_open),
            cls="anchor-container"
        ),

        Label("Persistance check "),
        Input(placeholder="Enter your name", id="name", bind=state.name, data_persist="name"),
        P(text="Hello "+ state.name),
        # signals=Signals(message=""),
        Style("""
        .fade-box {
            background: var(--gray-3);
            border: 1px solid var(--gray-6);
            border-radius: var(--radius-2);
            padding: var(--size-2);
            width: fit-content;

            display: none;
            transition: display 1s allow-discrete;
            opacity: 1;
            animation: var(--animation-fade-out) forwards, var(--animation-scale-down);
        }
        .open {
            animation: var(--animation-fade-in) forwards;    
            opacity: 0;
            display: block;
        }

        """),
        H2("Fade demo"),
        Button("Toggle fade", on_click=state.btn_open.toggle(), id="myButton2"),
        Div(
            "I fade in and out",
            cls="fade-box",
            # when visible: run fade-in; when hidden: run fade-out
            data_class=f"{{open: {state.btn_open}, closed: !{state.btn_open}}}",
            data_anchor="'#myButton2'",
        ),
    )