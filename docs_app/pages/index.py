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
        
        Section("Component Documentation",
            P("Explore the RustyTags Xtras components:"),
            Ul(
                Li(A("RustyTags Datastar SDK", href="/xtras/rustytags", cls="color-blue-6 text-decoration-underline")),
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
            cls="bg-background",
        ),
        cls="px-8 lg:px-16 xl:px-32 mt-16"
    )