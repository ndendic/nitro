"""Tabs component documentation page"""

from .templates.base import *
from .templates.base import TitledSection as Section
from .templates.base import template
from fastapi import APIRouter
from .templates.components import Sidebar, Navbar, PicSumImg
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
                Li(A("Field", href="/xtras/field", cls="color-blue-6 text-decoration-underline"), " - Form field wrapper with label, description, error"),
                Li(A("Input Group", href="/xtras/input-group", cls="color-blue-6 text-decoration-underline"), " - Input with prefix/suffix elements"),
                Li(A("Checkbox", href="/xtras/checkbox", cls="color-blue-6 text-decoration-underline"), " - Checkbox with two-way binding"),
                Li(A("Radio Group", href="/xtras/radio", cls="color-blue-6 text-decoration-underline"), " - Radio buttons with compound component pattern"),
                Li(A("Switch", href="/xtras/switch", cls="color-blue-6 text-decoration-underline"), " - Toggle switch with smooth animation"),
                Li(A("Select", href="/xtras/select", cls="color-blue-6 text-decoration-underline"), " - Native select dropdown with Datastar binding"),
                Li(A("Textarea", href="/xtras/textarea", cls="color-blue-6 text-decoration-underline"), " - Multi-line text input with binding"),
            ),
        ),

        Section("Interactive Components",
            P("Complex components with state and behavior:"),
            Ul(
                Li(A("Tabs", href="/xtras/tabs", cls="color-blue-6 text-decoration-underline"), " - Tabbed content panels"),
                Li(A("Accordion", href="/xtras/accordion", cls="color-blue-6 text-decoration-underline"), " - Collapsible content sections"),
                Li(A("Dialog", href="/xtras/dialog", cls="color-blue-6 text-decoration-underline"), " - Modal dialogs"),
                Li(A("Dropdown Menu", href="/xtras/dropdown", cls="color-blue-6 text-decoration-underline"), " - Accessible dropdown menu"),
                Li(A("Popover", href="/xtras/popover", cls="color-blue-6 text-decoration-underline"), " - Positioned overlay container"),
                Li(A("Tooltip", href="/xtras/tooltip", cls="color-blue-6 text-decoration-underline"), " - Pure CSS hover tooltip"),
                Li(A("Alert Dialog", href="/xtras/alert-dialog", cls="color-blue-6 text-decoration-underline"), " - Confirmation modal dialog"),
            ),
        ),

        Section("Feedback Components",
            P("User feedback and notification components:"),
            Ul(
                Li(A("Toast", href="/xtras/toast", cls="color-blue-6 text-decoration-underline"), " - Toast notifications with variants"),
                Li(A("Progress", href="/xtras/progress", cls="color-blue-6 text-decoration-underline"), " - Progress bar with determinate/indeterminate modes"),
            ),
        ),

        Section("Navigation & Display",
            P("Navigation and data display components:"),
            Ul(
                Li(A("Breadcrumb", href="/xtras/breadcrumb", cls="color-blue-6 text-decoration-underline"), " - Breadcrumb navigation with separators"),
                Li(A("Pagination", href="/xtras/pagination", cls="color-blue-6 text-decoration-underline"), " - Page navigation with Datastar signals"),
                Li(A("Avatar", href="/xtras/avatar", cls="color-blue-6 text-decoration-underline"), " - User avatars with image and fallback initials"),
                Li(A("Table", href="/xtras/table", cls="color-blue-6 text-decoration-underline"), " - Data tables with Basecoat styling"),
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