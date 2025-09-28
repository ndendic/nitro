from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from nitro import *

from pages.accordion import router as accordion_router
from pages.codeblock import router as codeblock_router
from pages.dialog import router as dialog_router
from pages.tabs import router as tabs_router

from pages.base import page

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="docs/static"), name="static")

app.include_router(codeblock_router)
app.include_router(tabs_router)
app.include_router(accordion_router)
app.include_router(dialog_router)

@app.get("/")
@page(title="RustyTags Documentation", wrap_in=HTMLResponse)
def index():
    return Main(
        H1("RustyTags Documentation", cls="text-4xl font-bold"),
        P("A high-performance HTML generation library that combines Rust-powered performance with modern Python web development."),
        
        Section("Component Documentation",
            P("Explore the RustyTags Xtras components:"),
            Ul(
                Li(A("CodeBlock Component", href="/xtras/codeblock", cls="color-blue-6 text-decoration-underline")),
                Li(A("Tabs Component", href="/xtras/tabs", cls="color-blue-6 text-decoration-underline")),
                Li(A("Accordion Component (Simplified)", href="/xtras/accordion", cls="color-blue-6 text-decoration-underline")),
                Li(A("Dialog Component", href="/xtras/dialog", cls="color-blue-6 text-decoration-underline")),
            ),
        ),
        
        Section("Architecture Principles",
            P("RustyTags components follow key principles:"),
            Ul(
                Li("🏗️ Native HTML First - Use browser-native features when available"),
                Li("⚡ Focus on Anatomical Patterns - Solve complex DOM coordination problems"),
                Li("♿️ Accessibility by Default - Built-in WCAG compliance"),
                Li("🎨 Open Props Integration - Semantic design tokens"),
                Li("📊 Datastar Reactivity - Modern reactive web development"),
            ),
        ),
        Section("anchor",
            P("Anchor tag."),
            Button("Click me", id="myButton", on_click="$anchorOpen = !$anchorOpen"),
            Div("default", data_anchor="'#myButton'", show="$anchorOpen", cls="bg-red-500"),
        ),
        
        signals=Signals(message=""),
    )


@app.get("/playground")
@page(title="RustyTags Playground", wrap_in=HTMLResponse)
def playground():
    popover_style="background: var(--gray-2); padding: var(--size-1); border-radius: var(--radius-1); border: solid var(--border-size-1);"
    return Main(
        H1("RustyTags Playground"),
        P("This is a playground for RustyTags."),
        Div(Button("Click me",id="myButton", on_click="$anchorOpen = !$anchorOpen", style="width: 300px; height: 100px;"), cls="anchor-container"),

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8800, reload=True)




