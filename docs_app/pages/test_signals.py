"""Minimal test page for Datastar signals"""

from fastapi import APIRouter
from rusty_tags import Div, Button, Pre, Code, H1
from nitro.infrastructure.html.datastar import Signals
from pages.templates.base import template
from nitro.infrastructure.events import on, emit_elements

router = APIRouter()

@router.get("/test/signals")
@template(title="Test Signals")
def test_signals():
    """Test basic Datastar signal updating"""

    return Div(
        H1("Signal Test", cls="text-4xl font-bold mb-4"),
        Div(
            Button(
                "Increment",
                **{"data-on:click": "$counter = ($counter || 0) + 1"},
                cls="btn btn-primary mb-4"
            ),
            Pre(
                Code(
                    data_text="'Counter: ' + ($counter || 0)",
                    cls="text-2xl"
                ),
                cls="p-4 bg-muted rounded"
            ),
            signals=Signals(counter=0)
        ),
        cls="p-8"
    )
