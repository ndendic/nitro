"""Tabs component documentation page"""

from .templates.base import *
from .templates.base import TitledSection as Section
from .templates.base import template
from fastapi import APIRouter
from .templates.components import Sidebar, Navbar
router: APIRouter = APIRouter()

@router.get("/")
@template(title="RustyTags Documentation")
def index():
    return Div(
        H1("RustyTags Documentation", cls="text-4xl font-bold mb-4"),
        P("A high-performance HTML generation library that combines Rust-powered performance with modern Python web development."),
        
        Section("Foundation Components",
            P("Basic building blocks for your UI:"),
            Ul(
                Li(A("Button", href="/xtras/button", cls="color-blue-6 text-decoration-underline"), " - Versatile button with variants and sizes"),
                Li(A("Card", href="/xtras/card", cls="color-blue-6 text-decoration-underline"), " - Container for grouping related content"),
                Li(A("Badge", href="/xtras/badge", cls="color-blue-6 text-decoration-underline"), " - Status indicators and labels"),
                Li(A("Alert", href="/xtras/alert", cls="color-blue-6 text-decoration-underline"), " - Contextual feedback messages"),
                Li(A("Label", href="/xtras/label", cls="color-blue-6 text-decoration-underline"), " - Form input labels"),
                Li(A("Kbd", href="/xtras/kbd", cls="color-blue-6 text-decoration-underline"), " - Keyboard shortcut display"),
                Li(A("Spinner", href="/xtras/spinner", cls="color-blue-6 text-decoration-underline"), " - Loading indicator"),
                Li(A("Skeleton", href="/xtras/skeleton", cls="color-blue-6 text-decoration-underline"), " - Loading placeholder"),
            ),
        ),

        Section("Form Controls",
            P("Form input components with Datastar binding:"),
            Ul(
                Li(A("Checkbox", href="/xtras/checkbox", cls="color-blue-6 text-decoration-underline"), " - Checkbox with two-way binding"),
                Li(A("Radio Group", href="/xtras/radio", cls="color-blue-6 text-decoration-underline"), " - Radio buttons with compound component pattern"),
            ),
        ),

        Section("Interactive Components",
            P("Complex components with state and behavior:"),
            Ul(
                Li(A("Tabs", href="/xtras/tabs", cls="color-blue-6 text-decoration-underline"), " - Tabbed content panels"),
                Li(A("Accordion", href="/xtras/accordion", cls="color-blue-6 text-decoration-underline"), " - Collapsible content sections"),
                Li(A("Dialog", href="/xtras/dialog", cls="color-blue-6 text-decoration-underline"), " - Modal dialogs"),
            ),
        ),

        Section("Utilities",
            P("Helper components and documentation:"),
            Ul(
                Li(A("RustyTags Datastar SDK", href="/xtras/rustytags", cls="color-blue-6 text-decoration-underline")),
                Li(A("CodeBlock", href="/xtras/codeblock", cls="color-blue-6 text-decoration-underline"), " - Syntax highlighted code"),
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
            cls="bg-background",
        ),
        cls="px-8 lg:px-16 xl:px-32 mt-16"
    )