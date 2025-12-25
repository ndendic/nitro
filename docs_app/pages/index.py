"""Nitro Framework Landing Page - Component Showcases"""

from .templates.base import *
from .templates.base import template
from fastapi import APIRouter
from nitro.infrastructure.html.components import (
    LucideIcon, Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
    Badge, Button, Avatar, Switch, Select, SelectOption,
    Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
    Tabs, TabsList, TabsTrigger, TabsContent,
    DropdownMenu, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator,
    Field, RadioGroup, RadioItem, Textarea, Progress,
)

router: APIRouter = APIRouter()

# =============================================================================
# HERO SECTION
# =============================================================================

def hero_section():
    """Clean hero with headline and CTAs."""
    return Section(
        Div(
            Badge("Python Web Framework", cls="mb-6"),
            H1(
                "Build with Pure Python.",
                Br(),
                Span("Ship at Lightning Speed.", cls="nitro-gradient"),
                cls="hero-display text-foreground mb-6"
            ),
            P(
                "Production-ready components. Zero JavaScript. ",
                "Rich domain entities with reactive UI.",
                cls="text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
            ),
            Div(
                Button(
                    LucideIcon("rocket", cls="size-4 mr-2"),
                    "Get Started",
                    variant="primary",
                    cls="px-6 py-3"
                ),
                Button(
                    LucideIcon("github", cls="size-4 mr-2"),
                    "View on GitHub",
                    variant="outline",
                    cls="px-6 py-3"
                ),
                cls="flex flex-wrap items-center justify-center gap-4"
            ),
            cls="text-center"
        ),
        cls="py-20 md:py-32"
    )

# =============================================================================
# SHOWCASE 1: DATA TABLE (Component Left, Code Right)
# =============================================================================

def team_table_demo():
    """Interactive team management table."""
    members = [
        {"name": "Sofia Chen", "email": "sofia@company.com", "role": "Owner", "avatar": "SC"},
        {"name": "Marcus Johnson", "email": "marcus@company.com", "role": "Developer", "avatar": "MJ"},
        {"name": "Aisha Patel", "email": "aisha@company.com", "role": "Viewer", "avatar": "AP"},
    ]

    return Card(
        CardHeader(
            Div(
                Div(
                    CardTitle("Team Members"),
                    CardDescription("Manage your team and their permissions"),
                ),
                Button(
                    LucideIcon("plus", cls="size-4 mr-2"),
                    "Add Member",
                    variant="primary",
                    size="sm"
                ),
                cls="flex items-center justify-between"
            ),
        ),
        CardContent(
            Table(
                TableHeader(
                    TableRow(
                        TableHead("Member"),
                        TableHead("Role"),
                        TableHead(cls="w-12"),
                    )
                ),
                TableBody(
                    *[
                        TableRow(
                            TableCell(
                                Div(
                                    Avatar(fallback=m["avatar"], size="sm"),
                                    Div(
                                        P(m["name"], cls="font-medium"),
                                        P(m["email"], cls="text-sm text-muted-foreground"),
                                    ),
                                    cls="flex items-center gap-3"
                                )
                            ),
                            TableCell(
                                Badge(
                                    m["role"],
                                    variant="secondary" if m["role"] == "Viewer" else "default"
                                )
                            ),
                            TableCell(
                                DropdownMenu(
                                    DropdownTrigger(
                                        Button(
                                            LucideIcon("more-horizontal", cls="size-4"),
                                            variant="ghost",
                                            size="icon"
                                        )
                                    ),
                                    DropdownContent(
                                        DropdownItem(LucideIcon("pencil", cls="size-4 mr-2"), "Edit"),
                                        DropdownItem(LucideIcon("mail", cls="size-4 mr-2"), "Email"),
                                        DropdownSeparator(),
                                        DropdownItem(
                                            LucideIcon("trash", cls="size-4 mr-2"),
                                            "Remove",
                                            cls="text-destructive"
                                        ),
                                    )
                                )
                            ),
                        )
                        for m in members
                    ]
                ),
                cls="table"
            ),
        ),
    )

def showcase_data_table():
    """Showcase 1: Data table with code."""
    code = '''from nitro import Card, Table, Avatar, Badge

def TeamTable(members):
    return Card(
        CardHeader(
            CardTitle("Team Members"),
            Button("Add Member", variant="primary"),
        ),
        CardContent(
            Table(
                TableHeader(
                    TableRow(
                        TableHead("Member"),
                        TableHead("Role"),
                    )
                ),
                TableBody(
                    *[MemberRow(m) for m in members]
                ),
            )
        ),
    )'''

    return Section(
        Div(
            # Section header
            Div(
                Badge("Data Display", variant="outline", cls="mb-4"),
                H2("Rich Data Tables", cls="text-3xl font-bold mb-3"),
                P(
                    "Build complex data interfaces with sorting, filtering, and actions. ",
                    "All in pure Python.",
                    cls="text-muted-foreground text-lg"
                ),
                cls="mb-10"
            ),
            # Component (left 60%) + Code (right 40%)
            Div(
                # Component
                Div(
                    team_table_demo(),
                    cls="w-full md:w-3/5"
                ),
                # Code
                Div(
                    Div(
                        Div(
                            Span(cls="size-3 rounded-full bg-red-500"),
                            Span(cls="size-3 rounded-full bg-yellow-500"),
                            Span(cls="size-3 rounded-full bg-green-500"),
                            cls="flex gap-2"
                        ),
                        Span("team_table.py", cls="text-xs text-muted-foreground ml-4"),
                        cls="flex items-center px-4 py-3 border-b"
                    ),
                    Pre(
                        Code(code, cls="text-sm language-python"),
                        cls="p-4 m-0 overflow-x-auto bg-muted/50"
                    ),
                    cls="rounded-lg border overflow-hidden w-full md:w-2/5"
                ),
                cls="flex flex-col md:flex-row gap-6 items-start"
            ),
            cls=""
        ),
        cls="py-20 md:py-28"
    )

# =============================================================================
# SHOWCASE 2: SETTINGS FORM (Code Left, Component Right)
# =============================================================================

def settings_demo():
    """Settings panel with various controls."""
    return Card(
        CardHeader(
            CardTitle("Notification Settings"),
            CardDescription("Configure how you receive updates"),
        ),
        CardContent(
            Div(
                # Email notifications
                Div(
                    Div(
                        P("Email Notifications", cls="font-medium"),
                        P("Receive updates via email", cls="text-sm text-muted-foreground"),
                    ),
                    Switch(id="email-notifs", checked=True),
                    cls="flex items-center justify-between py-3"
                ),
                # Push notifications
                Div(
                    Div(
                        P("Push Notifications", cls="font-medium"),
                        P("Receive push notifications", cls="text-sm text-muted-foreground"),
                    ),
                    Switch(id="push-notifs", checked=False),
                    cls="flex items-center justify-between py-3 border-t"
                ),
                # Frequency
                Div(
                    Div(
                        P("Digest Frequency", cls="font-medium"),
                        P("How often to send summaries", cls="text-sm text-muted-foreground"),
                    ),
                    Select(
                        SelectOption("Daily", value="daily"),
                        SelectOption("Weekly", value="weekly", selected=True),
                        SelectOption("Monthly", value="monthly"),
                        cls="w-32"
                    ),
                    cls="flex items-center justify-between py-3 border-t"
                ),
            ),
        ),
        CardFooter(
            Button("Save Changes", variant="primary"),
            cls="justify-end"
        ),
    )

def showcase_settings():
    """Showcase 2: Settings form with code."""
    code = '''from nitro import Card, Switch, Select, Field

def NotificationSettings():
    return Card(
        CardHeader(
            CardTitle("Notification Settings"),
        ),
        CardContent(
            Field(
                Switch(bind="$emailNotifs"),
                label="Email Notifications",
                description="Receive updates via email",
            ),
            Field(
                Select(
                    Option("Daily"),
                    Option("Weekly"),
                    bind="$frequency"
                ),
                label="Digest Frequency",
            ),
        ),
        CardFooter(
            Button("Save Changes", variant="primary"),
        ),
    )'''

    return Section(
        Div(
            # Section header (right aligned)
            Div(
                Badge("Form Controls", variant="outline", cls="mb-4"),
                H2("Reactive Forms", cls="text-3xl font-bold mb-3"),
                P(
                    "Two-way data binding with Datastar signals. ",
                    "No JavaScript, no state management boilerplate.",
                    cls="text-muted-foreground text-lg"
                ),
                cls="mb-10 md:text-right"
            ),
            # Code (left 40%) + Component (right 60%)
            Div(
                # Code
                Div(
                    Div(
                        Div(
                            Span(cls="size-3 rounded-full bg-red-500"),
                            Span(cls="size-3 rounded-full bg-yellow-500"),
                            Span(cls="size-3 rounded-full bg-green-500"),
                            cls="flex gap-2"
                        ),
                        Span("settings.py", cls="text-xs text-muted-foreground ml-4"),
                        cls="flex items-center px-4 py-3 border-b"
                    ),
                    Pre(
                        Code(code, cls="text-sm language-python"),
                        cls="p-4 m-0 overflow-x-auto bg-muted/50"
                    ),
                    cls="rounded-lg border overflow-hidden w-full md:w-2/5"
                ),
                # Component
                Div(
                    settings_demo(),
                    cls="w-full md:w-3/5"
                ),
                cls="flex flex-col md:flex-row gap-6 items-start"
            ),
            cls=""
        ),
        cls="py-20 md:py-28 bg-muted/30"
    )

# =============================================================================
# SHOWCASE 3: TABS + PROGRESS (Component Left, Code Right)
# =============================================================================

def dashboard_demo():
    """Dashboard card with tabs and progress."""
    return Card(
        CardHeader(
            Div(
                CardTitle("Project Analytics"),
                Badge("Live", variant="default", cls="bg-green-500/10 text-green-600"),
                cls="flex items-center gap-2"
            ),
            CardDescription("Track your project metrics in real-time"),
        ),
        CardContent(
            Tabs(
                TabsList(
                    TabsTrigger("Overview", id="overview"),
                    TabsTrigger("Tasks", id="tasks"),
                    TabsTrigger("Team", id="team"),
                ),
                TabsContent(
                    Div(
                        # Stats row
                        Div(
                            Div(
                                P("Total Tasks", cls="text-sm text-muted-foreground"),
                                P("248", cls="text-2xl font-bold"),
                                cls="text-center"
                            ),
                            Div(
                                P("Completed", cls="text-sm text-muted-foreground"),
                                P("186", cls="text-2xl font-bold text-green-600"),
                                cls="text-center"
                            ),
                            Div(
                                P("In Progress", cls="text-sm text-muted-foreground"),
                                P("42", cls="text-2xl font-bold text-blue-600"),
                                cls="text-center"
                            ),
                            cls="grid grid-cols-3 gap-4 mb-6"
                        ),
                        # Progress
                        Div(
                            Div(
                                P("Overall Progress", cls="text-sm font-medium"),
                                P("75%", cls="text-sm text-muted-foreground"),
                                cls="flex justify-between mb-2"
                            ),
                            Progress(value=75),
                        ),
                    ),
                    id="overview"
                ),
                TabsContent(
                    P("Task list would go here...", cls="text-muted-foreground py-8 text-center"),
                    id="tasks"
                ),
                TabsContent(
                    P("Team members would go here...", cls="text-muted-foreground py-8 text-center"),
                    id="team"
                ),
                default_tab="overview",
            ),
        ),
    )

def showcase_dashboard():
    """Showcase 3: Dashboard with tabs."""
    code = '''from nitro import Card, Tabs, Progress

def ProjectDashboard():
    return Card(
        CardHeader(
            CardTitle("Project Analytics"),
            Badge("Live", cls="bg-green-500"),
        ),
        CardContent(
            Tabs(
                TabsList(
                    TabsTrigger("Overview"),
                    TabsTrigger("Tasks"),
                ),
                TabsContent(
                    StatsGrid(
                        Stat("Total", "$total_tasks"),
                        Stat("Done", "$completed"),
                    ),
                    Progress(bind="$progress"),
                    id="overview"
                ),
                default_tab="overview",
            ),
        ),
    )'''

    return Section(
        Div(
            # Section header
            Div(
                Badge("Interactive", variant="outline", cls="mb-4"),
                H2("Complex Interactions", cls="text-3xl font-bold mb-3"),
                P(
                    "Tabs, accordions, modals, and more. ",
                    "Server-rendered with client-side interactivity.",
                    cls="text-muted-foreground text-lg"
                ),
                cls="mb-10"
            ),
            # Component (left 60%) + Code (right 40%)
            Div(
                # Component
                Div(
                    dashboard_demo(),
                    cls="w-full md:w-3/5"
                ),
                # Code
                Div(
                    Div(
                        Div(
                            Span(cls="size-3 rounded-full bg-red-500"),
                            Span(cls="size-3 rounded-full bg-yellow-500"),
                            Span(cls="size-3 rounded-full bg-green-500"),
                            cls="flex gap-2"
                        ),
                        Span("dashboard.py", cls="text-xs text-muted-foreground ml-4"),
                        cls="flex items-center px-4 py-3 border-b"
                    ),
                    Pre(
                        Code(code, cls="text-sm language-python"),
                        cls="p-4 m-0 overflow-x-auto bg-muted/50"
                    ),
                    cls="rounded-lg border overflow-hidden w-full md:w-2/5"
                ),
                cls="flex flex-col md:flex-row gap-6 items-start"
            ),
        ),
        cls="py-20 md:py-28"
    )

# =============================================================================
# FEATURES STRIP
# =============================================================================

def features_strip():
    """Compact features strip."""
    features = [
        ("zap", "3-10x Faster", "Rust-powered HTML"),
        ("code", "Zero JS", "Pure Python stack"),
        ("layers", "4+ Frameworks", "FastAPI, Flask, more"),
        ("activity", "Reactive", "Datastar signals"),
    ]
    return Section(
        Div(
            *[
                Div(
                    LucideIcon(icon, cls="size-5 text-primary mb-2"),
                    P(title, cls="font-semibold"),
                    P(desc, cls="text-sm text-muted-foreground"),
                    cls="text-center"
                )
                for icon, title, desc in features
            ],
            cls="grid grid-cols-2 md:grid-cols-4 gap-8"
        ),
        cls="py-12 border-y bg-muted/30"
    )

# =============================================================================
# CTA SECTION
# =============================================================================

def cta_section():
    """Call to action."""
    return Section(
        Div(
            H2("Ready to Build?", cls="text-3xl font-bold mb-4"),
            P(
                "Get started in under a minute with pip install.",
                cls="text-muted-foreground text-lg mb-8"
            ),
            Div(
                Code("pip install nitro", cls="text-sm"),
                cls="inline-block px-4 py-2 rounded-lg bg-muted font-mono mb-8"
            ),
            Div(
                A(
                    LucideIcon("book-open", cls="size-4 mr-2"),
                    "Documentation",
                    href="/xtras/button",
                    cls="inline-flex items-center px-6 py-3 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors no-underline"
                ),
                A(
                    LucideIcon("github", cls="size-4 mr-2"),
                    "GitHub",
                    href="https://github.com/ndendic/nitro-systems",
                    target="_blank",
                    cls="inline-flex items-center px-6 py-3 rounded-lg font-medium border hover:bg-muted transition-colors no-underline"
                ),
                cls="flex flex-wrap justify-center gap-4"
            ),
            cls="text-center"
        ),
        cls="py-20 md:py-28"
    )

# =============================================================================
# ROUTES
# =============================================================================

@router.get("/")
@template(title="Nitro - Build with Pure Python, Ship at Lightning Speed")
def index():
    """Nitro landing page."""
    return Div(
        hero_section(),
        features_strip(),
        showcase_data_table(),
        showcase_settings(),
        showcase_dashboard(),
        cta_section(),
    )
