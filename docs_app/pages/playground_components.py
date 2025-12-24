from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from .templates.base import *  # noqa: F403
from .templates.components import PicSumImg, DiceBearAvatar

router: APIRouter = APIRouter()


# ============================================================================
# HELPER COMPONENTS
# ============================================================================

def StatCard(label, value, change=None, icon=None, trend="up"):
    """Metric card with optional trend indicator."""
    trend_color = "text-green-600 dark:text-green-400" if trend == "up" else "text-red-600 dark:text-red-400"
    trend_icon = "trending-up" if trend == "up" else "trending-down"

    return Card(
        CardContent(
            Div(
                P(label, cls="text-sm font-medium text-muted-foreground"),
                LucideIcon(icon, cls="size-4 text-muted-foreground") if icon else None,
                cls="flex items-center justify-between"
            ),
            P(value, cls="text-2xl font-bold tracking-tight mt-2"),
            Div(
                LucideIcon(trend_icon, cls="size-3"),
                Span(change, cls="text-xs font-medium"),
                cls=f"flex items-center gap-1 mt-1 {trend_color}"
            ) if change else None,
        ),
    )


def FeatureCard(icon, title, description):
    """Feature highlight card with icon."""
    return Card(
        CardContent(
            Div(
                LucideIcon(icon, cls="size-5"),
                cls="size-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-4"
            ),
            H3(title, cls="font-semibold mb-2"),
            P(description, cls="text-sm text-muted-foreground leading-relaxed"),
        ),
        cls="hover:shadow-md transition-shadow"
    )


def TeamMember(name, role, avatar_seed):
    """Team member card with avatar."""
    return Div(
        DiceBearAvatar(avatar_seed, h=64, w=64),
        Div(
            P(name, cls="font-medium"),
            P(role, cls="text-sm text-muted-foreground"),
            cls="mt-3 text-center"
        ),
        cls="flex flex-col items-center"
    )


def ActivityItem(icon, title, description, time, color="primary"):
    """Activity feed item."""
    color_classes = {
        "primary": "bg-primary/10 text-primary",
        "success": "bg-green-500/10 text-green-600 dark:text-green-400",
        "warning": "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
        "destructive": "bg-destructive/10 text-destructive",
    }
    return Div(
        Div(
            LucideIcon(icon, cls="size-4"),
            cls=f"size-8 rounded-full flex items-center justify-center shrink-0 {color_classes.get(color, color_classes['primary'])}"
        ),
        Div(
            P(title, cls="font-medium text-sm"),
            P(description, cls="text-xs text-muted-foreground"),
            cls="flex-1 min-w-0"
        ),
        Span(time, cls="text-xs text-muted-foreground shrink-0"),
        cls="flex items-start gap-3 py-3"
    )


def PricingCard(name, price, period, features, popular=False, cta="Get Started"):
    """Pricing tier card."""
    return Card(
        Badge("Most Popular", cls="absolute -top-3 left-1/2 -translate-x-1/2") if popular else None,
        CardHeader(
            CardTitle(name),
            CardDescription(
                Span(price, cls="text-3xl font-bold text-foreground"),
                Span(f"/{period}", cls="text-muted-foreground"),
            ),
        ),
        CardContent(
            Ul(
                *[Li(
                    LucideIcon("check", cls="size-4 text-primary shrink-0"),
                    Span(feature, cls="text-sm"),
                    cls="flex items-center gap-2"
                ) for feature in features],
                cls="space-y-3"
            ),
        ),
        CardFooter(
            Button(cta, variant="primary" if popular else "outline", cls="w-full"),
        ),
        cls=f"relative {'border-primary shadow-lg' if popular else ''}"
    )


# ============================================================================
# MAIN PAGE
# ============================================================================

@router.get("/playground_components")
@template(title="Component Playground")
def playground_components():
    state = Signals(
        tab="overview",
        accordion_open="item-1",
        form_name="",
        form_email="",
        notifications=True,
        marketing=False,
    )

    return Div(
        # ========== HERO SECTION ==========
        Section(
            Div(
                Badge("Design System Showcase", variant="secondary", cls="mb-4"),
                H1(
                    "Build Beautiful Apps",
                    Br(),
                    Span("With Nitro Components", cls="text-primary"),
                    cls="text-4xl md:text-5xl font-bold tracking-tight"
                ),
                P(
                    "Explore the complete component library. Every element designed for consistency, accessibility, and visual harmony.",
                    cls="text-lg text-muted-foreground mt-4 max-w-2xl"
                ),
                Div(
                    Button(
                        LucideIcon("rocket"),
                        "Get Started",
                        variant="primary",
                        size="lg"
                    ),
                    Button(
                        LucideIcon("github"),
                        "View on GitHub",
                        variant="outline",
                        size="lg"
                    ),
                    cls="flex flex-wrap gap-4 mt-8"
                ),
                cls="text-center md:text-left"
            ),
            cls="py-12 md:py-16"
        ),

        # ========== STATS SECTION ==========
        Section(
            H2("Dashboard Metrics", cls="text-xl font-semibold mb-6"),
            Div(
                StatCard("Total Revenue", "$45,231.89", "+20.1%", "dollar-sign", "up"),
                StatCard("Subscriptions", "+2,350", "+180.1%", "users", "up"),
                StatCard("Active Now", "573", "+19%", "activity", "up"),
                StatCard("Bounce Rate", "24.5%", "-4.5%", "trending-down", "down"),
                cls="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
            ),
            cls="py-12 border-t"
        ),

        # ========== FEATURE CARDS ==========
        Section(
            Div(
                H2("Why Choose Nitro?", cls="text-2xl font-bold"),
                P("Everything you need to build modern web applications", cls="text-muted-foreground mt-2"),
                cls="mb-8"
            ),
            Div(
                FeatureCard(
                    "zap",
                    "Lightning Fast",
                    "Built on Rust-powered RustyTags for exceptional rendering performance."
                ),
                FeatureCard(
                    "palette",
                    "Beautiful Design",
                    "Pre-built components following modern design principles and accessibility standards."
                ),
                FeatureCard(
                    "code",
                    "Python Native",
                    "Write your entire frontend in Python. No JavaScript required."
                ),
                FeatureCard(
                    "moon",
                    "Dark Mode Ready",
                    "Automatic light and dark mode support with semantic color tokens."
                ),
                FeatureCard(
                    "layout",
                    "Responsive",
                    "Mobile-first design system with flexible layout primitives."
                ),
                FeatureCard(
                    "shield",
                    "Type Safe",
                    "Full type hints and IDE support for confident development."
                ),
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            cls="py-12 border-t"
        ),

        # ========== TABS SHOWCASE ==========
        Section(
            H2("Interactive Components", cls="text-xl font-semibold mb-6"),
            Tabs(
                TabsList(
                    TabsTrigger("Overview", id="overview"),
                    TabsTrigger("Analytics", id="analytics"),
                    TabsTrigger("Reports", id="reports"),
                    TabsTrigger("Settings", id="settings"),
                ),
                TabsContent(
                    Card(
                        CardHeader(
                            CardTitle("Welcome to Your Dashboard"),
                            CardDescription("Here's what's happening with your projects today."),
                        ),
                        CardContent(
                            Div(
                                Div(
                                    H4("Recent Activity", cls="font-medium mb-4"),
                                    ActivityItem("git-commit", "New commit pushed", "Updated authentication flow", "2m ago", "primary"),
                                    ActivityItem("check-circle", "Build succeeded", "Production deployment complete", "15m ago", "success"),
                                    ActivityItem("alert-triangle", "Warning detected", "High memory usage on server-2", "1h ago", "warning"),
                                    ActivityItem("user-plus", "New team member", "Sarah joined the project", "3h ago", "primary"),
                                    cls="divide-y"
                                ),
                                Div(
                                    H4("Quick Actions", cls="font-medium mb-4"),
                                    Div(
                                        Button(LucideIcon("plus"), "New Project", variant="outline", cls="justify-start"),
                                        Button(LucideIcon("upload"), "Deploy", variant="outline", cls="justify-start"),
                                        Button(LucideIcon("settings"), "Configure", variant="outline", cls="justify-start"),
                                        Button(LucideIcon("users"), "Invite Team", variant="outline", cls="justify-start"),
                                        cls="grid grid-cols-2 gap-2"
                                    ),
                                ),
                                cls="grid md:grid-cols-2 gap-8"
                            ),
                        ),
                    ),
                    id="overview"
                ),
                TabsContent(
                    Card(
                        CardHeader(
                            CardTitle("Analytics Overview"),
                            CardDescription("Track your performance metrics over time."),
                        ),
                        CardContent(
                            Div(
                                Div(
                                    P("Page Views", cls="text-sm text-muted-foreground"),
                                    P("142,847", cls="text-2xl font-bold"),
                                    Progress(value=75, cls="mt-2"),
                                    cls="space-y-1"
                                ),
                                Div(
                                    P("Unique Visitors", cls="text-sm text-muted-foreground"),
                                    P("54,329", cls="text-2xl font-bold"),
                                    Progress(value=62, cls="mt-2"),
                                    cls="space-y-1"
                                ),
                                Div(
                                    P("Conversion Rate", cls="text-sm text-muted-foreground"),
                                    P("3.24%", cls="text-2xl font-bold"),
                                    Progress(value=32, cls="mt-2"),
                                    cls="space-y-1"
                                ),
                                cls="grid md:grid-cols-3 gap-6"
                            ),
                        ),
                    ),
                    id="analytics"
                ),
                TabsContent(
                    Card(
                        CardHeader(
                            CardTitle("Generated Reports"),
                            CardDescription("Download your monthly and quarterly reports."),
                        ),
                        CardContent(
                            Table(
                                TableHeader(
                                    TableRow(
                                        TableHead("Report"),
                                        TableHead("Type"),
                                        TableHead("Date"),
                                        TableHead("Status"),
                                        TableHead(cls="w-12"),
                                    ),
                                ),
                                TableBody(
                                    TableRow(
                                        TableCell("Q4 Revenue Report", cls="font-medium"),
                                        TableCell("Financial"),
                                        TableCell("Dec 2024"),
                                        TableCell(Badge("Ready", variant="primary")),
                                        TableCell(Button(LucideIcon("download"), variant="ghost", size="sm")),
                                    ),
                                    TableRow(
                                        TableCell("User Growth Analysis", cls="font-medium"),
                                        TableCell("Analytics"),
                                        TableCell("Dec 2024"),
                                        TableCell(Badge("Ready", variant="primary")),
                                        TableCell(Button(LucideIcon("download"), variant="ghost", size="sm")),
                                    ),
                                    TableRow(
                                        TableCell("Security Audit", cls="font-medium"),
                                        TableCell("Security"),
                                        TableCell("Nov 2024"),
                                        TableCell(Badge("Processing", variant="secondary")),
                                        TableCell(Button(LucideIcon("loader"), variant="ghost", size="sm", disabled=True)),
                                    ),
                                ),
                                cls="table"
                            ),
                        ),
                    ),
                    id="reports"
                ),
                TabsContent(
                    Card(
                        CardHeader(
                            CardTitle("Account Settings"),
                            CardDescription("Manage your account preferences."),
                        ),
                        CardContent(
                            Fieldset(
                                Field(
                                    Input(type="text", placeholder="Your name", id="settings-name"),
                                    label="Display Name",
                                    label_for="settings-name",
                                ),
                                Field(
                                    Input(type="email", placeholder="your@email.com", id="settings-email"),
                                    label="Email Address",
                                    label_for="settings-email",
                                ),
                                Field(
                                    Select(
                                        Option("System", value="system"),
                                        Option("Light", value="light"),
                                        Option("Dark", value="dark"),
                                        id="settings-theme",
                                    ),
                                    label="Theme Preference",
                                    label_for="settings-theme",
                                ),
                                Field(
                                    Switch(id="settings-notifications", checked=True),
                                    label="Email Notifications",
                                    orientation="horizontal",
                                ),
                                cls="space-y-4"
                            ),
                        ),
                        CardFooter(
                            Button("Save Changes", variant="primary"),
                            cls="justify-end"
                        ),
                    ),
                    id="settings"
                ),
                default_tab="overview"
            ),
            cls="py-12 border-t"
        ),

        # ========== CARDS GRID ==========
        Section(
            H2("Card Variations", cls="text-xl font-semibold mb-6"),
            Div(
                # Image Card
                Card(
                    PicSumImg(w=400, h=200, id=1015, cls="w-full h-48 object-cover rounded-t-xl -mt-6 -mx-0"),
                    CardHeader(
                        CardTitle("Mountain Vista"),
                        CardDescription("Breathtaking views from the summit"),
                    ),
                    CardContent(
                        P("Explore the beauty of nature with our guided hiking tours through pristine mountain trails.", cls="text-sm text-muted-foreground"),
                    ),
                    CardFooter(
                        Button("Learn More", variant="outline", size="sm"),
                        Button("Book Now", variant="primary", size="sm"),
                        cls="gap-2"
                    ),
                ),
                # Profile Card
                Card(
                    CardContent(
                        Div(
                            DiceBearAvatar("Alex Thompson", h=80, w=80),
                            H3("Alex Thompson", cls="font-semibold mt-4"),
                            P("Senior Product Designer", cls="text-sm text-muted-foreground"),
                            Div(
                                Badge("Design", variant="secondary"),
                                Badge("UX", variant="secondary"),
                                Badge("Figma", variant="secondary"),
                                cls="flex flex-wrap gap-2 mt-4 justify-center"
                            ),
                            ButtonGroup(
                                Button(LucideIcon("mail"), variant="outline"),
                                Button(LucideIcon("phone"), variant="outline"),
                                Button(LucideIcon("linkedin"), variant="outline"),
                                cls="mt-4"
                            ),
                            cls="flex flex-col items-center text-center pt-6"
                        ),
                    ),
                ),
                # Stats Card
                Card(
                    CardHeader(
                        Div(
                            CardTitle("Project Progress"),
                            DropdownMenu(
                                DropdownTrigger(
                                    Button(LucideIcon("more-vertical"), variant="ghost", size="sm"),
                                ),
                                DropdownContent(
                                    DropdownItem(LucideIcon("eye"), "View Details"),
                                    DropdownItem(LucideIcon("pencil"), "Edit"),
                                    DropdownSeparator(),
                                    DropdownItem(LucideIcon("trash"), "Delete", cls="text-destructive"),
                                ),
                            ),
                            cls="flex items-center justify-between"
                        ),
                        CardDescription("Sprint 23 - Mobile App"),
                    ),
                    CardContent(
                        Div(
                            Div(
                                Span("Completed", cls="text-sm text-muted-foreground"),
                                Span("68%", cls="text-sm font-medium"),
                                cls="flex justify-between mb-2"
                            ),
                            Progress(value=68),
                            cls="space-y-1"
                        ),
                        Div(
                            Div(
                                P("24", cls="text-xl font-bold"),
                                P("Tasks Done", cls="text-xs text-muted-foreground"),
                            ),
                            Div(
                                P("12", cls="text-xl font-bold"),
                                P("In Progress", cls="text-xs text-muted-foreground"),
                            ),
                            Div(
                                P("4", cls="text-xl font-bold"),
                                P("Remaining", cls="text-xs text-muted-foreground"),
                            ),
                            cls="grid grid-cols-3 gap-4 mt-6 text-center"
                        ),
                    ),
                    CardFooter(
                        AvatarGroup(
                            Avatar(src="https://api.dicebear.com/8.x/lorelei/svg?seed=John", alt="John"),
                            Avatar(src="https://api.dicebear.com/8.x/lorelei/svg?seed=Jane", alt="Jane"),
                            Avatar(src="https://api.dicebear.com/8.x/lorelei/svg?seed=Bob", alt="Bob"),
                            Avatar(fallback="+3", alt="More"),
                        ),
                        Span("Due in 5 days", cls="text-sm text-muted-foreground ml-auto"),
                        cls="items-center"
                    ),
                ),
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            ),
            cls="py-12 border-t"
        ),

        # ========== FORM SHOWCASE ==========
        Section(
            H2("Form Controls", cls="text-xl font-semibold mb-6"),
            Div(
                Card(
                    CardHeader(
                        CardTitle("Contact Form"),
                        CardDescription("Fill out the form below and we'll get back to you."),
                    ),
                    CardContent(
                        Form(
                            Div(
                                Field(
                                    Input(type="text", placeholder="John", id="first-name"),
                                    label="First Name",
                                    label_for="first-name",
                                ),
                                Field(
                                    Input(type="text", placeholder="Doe", id="last-name"),
                                    label="Last Name",
                                    label_for="last-name",
                                ),
                                cls="grid md:grid-cols-2 gap-4"
                            ),
                            Field(
                                Input(type="email", placeholder="john@example.com", id="email"),
                                label="Email",
                                label_for="email",
                                description="We'll never share your email with anyone.",
                            ),
                            Field(
                                DatePicker(
                                    bind="appointment_date",
                                    placeholder="Select appointment date",
                                ),
                                label="Appointment Date",
                                description="Choose a date for your appointment",
                            ),
                            Field(
                                Select(
                                    Option("Select a topic...", value="", disabled=True, selected=True),
                                    Option("General Inquiry", value="general"),
                                    Option("Technical Support", value="support"),
                                    Option("Sales", value="sales"),
                                    Option("Partnership", value="partnership"),
                                    id="topic",
                                ),
                                label="Topic",
                                label_for="topic",
                            ),
                            Field(
                                Textarea(placeholder="Tell us more about your inquiry...", id="message", rows=4),
                                label="Message",
                                label_for="message",
                            ),
                            Field(
                                Checkbox("I agree to the terms and conditions", id="terms"),
                                orientation="horizontal",
                            ),
                            cls="space-y-4"
                        ),
                    ),
                    CardFooter(
                        Button("Cancel", variant="outline"),
                        Button(LucideIcon("send"), "Send Message", variant="primary"),
                        cls="justify-end gap-2"
                    ),
                    cls="lg:col-span-2"
                ),
                Card(
                    CardHeader(
                        CardTitle("Preferences"),
                        CardDescription("Customize your experience."),
                    ),
                    CardContent(
                        Fieldset(
                            Legend("Notification Settings", cls="text-base font-medium mb-4"),
                            Field(
                                Switch(id="email-notif", checked=True),
                                label="Email Notifications",
                                description="Receive updates via email",
                                orientation="horizontal",
                            ),
                            Field(
                                Switch(id="push-notif"),
                                label="Push Notifications",
                                description="Get notified on your device",
                                orientation="horizontal",
                            ),
                            Field(
                                Switch(id="marketing-notif"),
                                label="Marketing Emails",
                                description="Receive promotional content",
                                orientation="horizontal",
                            ),
                            cls="space-y-4"
                        ),
                        Hr(cls="my-6"),
                        Fieldset(
                            Legend("Appearance", cls="text-base font-medium mb-4"),
                            RadioGroup(
                                RadioItem("System Default", value="system", id="theme-system", checked=True),
                                RadioItem("Light Mode", value="light", id="theme-light"),
                                RadioItem("Dark Mode", value="dark", id="theme-dark"),
                                name="theme-preference",
                                cls="space-y-3"
                            ),
                        ),
                    ),
                ),
                cls="grid lg:grid-cols-3 gap-6"
            ),
            cls="py-12 border-t"
        ),

        # ========== ACCORDION ==========
        Section(
            H2("FAQ Section", cls="text-xl font-semibold mb-6"),
            Accordion(
                AccordionItem(
                    "What is Nitro Framework?",
                    P("Nitro is a modern Python web framework that lets you build beautiful, reactive web applications entirely in Python. It combines the power of Rust-based HTML generation with a comprehensive component library.", cls="text-muted-foreground"),
                    id="faq-1",
                    open=True,
                ),
                AccordionItem(
                    "Do I need to know JavaScript?",
                    P("No! Nitro is designed to be JavaScript-free. All interactivity is handled through Datastar signals and Python code. You write Python, and Nitro handles the rest.", cls="text-muted-foreground"),
                    id="faq-2",
                ),
                AccordionItem(
                    "Is Nitro production-ready?",
                    P("Nitro is actively developed and used in production applications. The component library follows accessibility best practices and is thoroughly tested across modern browsers.", cls="text-muted-foreground"),
                    id="faq-3",
                ),
                AccordionItem(
                    "How does theming work?",
                    P("Nitro uses CSS custom properties (variables) for theming. You can easily create custom themes by overriding the color tokens in your CSS. Dark mode is built-in and works automatically.", cls="text-muted-foreground"),
                    id="faq-4",
                ),
                cls="max-w-2xl"
            ),
            cls="py-12 border-t"
        ),

        # ========== PRICING SECTION ==========
        Section(
            Div(
                H2("Simple, Transparent Pricing", cls="text-2xl font-bold"),
                P("Choose the plan that's right for you", cls="text-muted-foreground mt-2"),
                cls="text-center mb-8"
            ),
            Div(
                PricingCard(
                    "Starter",
                    "$0",
                    "month",
                    ["Up to 3 projects", "Basic components", "Community support", "1GB storage"],
                    cta="Start Free"
                ),
                PricingCard(
                    "Pro",
                    "$29",
                    "month",
                    ["Unlimited projects", "All components", "Priority support", "50GB storage", "Custom themes", "API access"],
                    popular=True,
                    cta="Start Trial"
                ),
                PricingCard(
                    "Enterprise",
                    "$99",
                    "month",
                    ["Everything in Pro", "SSO authentication", "Dedicated support", "Unlimited storage", "Custom development", "SLA guarantee"],
                    cta="Contact Sales"
                ),
                cls="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto"
            ),
            cls="py-12 border-t"
        ),

        # ========== DIALOG & INTERACTIONS ==========
        Section(
            H2("Interactive Overlays", cls="text-xl font-semibold mb-6"),
            Div(
                # Dialog
                DialogTrigger(
                    LucideIcon("maximize-2"), "Open Dialog", variant="outline",
                    dialog_id="edit-dialog"
                ),
                Dialog(                    
                    DialogHeader(
                        DialogTitle("Edit Profile"),
                        DialogDescription("Make changes to your profile here. Click save when you're done."),
                    ),
                    DialogBody(
                        Fieldset(
                            Field(
                                Input(type="text", value="Alex Thompson", id="dialog-name"),
                                label="Name",
                                label_for="dialog-name",
                            ),
                            Field(
                                Input(type="text", value="@alexthompson", id="dialog-username"),
                                label="Username",
                                label_for="dialog-username",
                            ),
                            cls="space-y-4"
                        ),
                    ),
                    DialogFooter(
                        DialogClose("Cancel", variant="outline"),
                        DialogClose("Save Changes", variant="primary"),
                    ),
                    id="edit-dialog"
                ),
                # Alert Dialog
                AlertDialogTrigger(
                    LucideIcon("trash-2"), "Delete Item", 
                    variant="destructive",
                    dialog_id="delete-dialog"
                ),
                AlertDialog(
                    
                    AlertDialogHeader(
                        AlertDialogTitle("Are you absolutely sure?"),
                        AlertDialogDescription("This action cannot be undone. This will permanently delete your account and remove your data from our servers."),
                    ),
                    AlertDialogFooter(
                        AlertDialogCancel("Cancel", dialog_id="delete-dialog"),
                        AlertDialogAction("Delete", variant="destructive", dialog_id="delete-dialog", on_click="console.log('Delete item')"),
                    ),
                    id="delete-dialog"
                ),
                # Popover
                Popover(
                    PopoverTrigger(
                        Button(LucideIcon("settings-2"), "Settings", variant="outline"),
                    ),
                    PopoverContent(
                        Div(
                            H4("Dimensions", cls="font-medium mb-3"),
                            Div(
                                Field(
                                    Input(type="number", value="100", id="pop-width", cls="h-8"),
                                    label="Width",
                                    label_for="pop-width",
                                ),
                                Field(
                                    Input(type="number", value="100", id="pop-height", cls="h-8"),
                                    label="Height",
                                    label_for="pop-height",
                                ),
                                cls="grid grid-cols-2 gap-3"
                            ),
                        ),
                    ),
                ),
                # Dropdown
                DropdownMenu(
                    DropdownTrigger(
                        Button(LucideIcon("menu"), "Menu", variant="outline"),
                    ),
                    DropdownContent(
                        DropdownLabel("My Account"),
                        DropdownSeparator(),
                        DropdownItem(LucideIcon("user"), "Profile", kbd="⌘P"),
                        DropdownItem(LucideIcon("credit-card"), "Billing", kbd="⌘B"),
                        DropdownItem(LucideIcon("settings"), "Settings", kbd="⌘S"),
                        DropdownSeparator(),
                        DropdownItem(LucideIcon("log-out"), "Log out"),
                    ),
                ),
                # Tooltips
                Tooltip(
                    Button(LucideIcon("info"), variant="ghost", size="icon"),
                    content="This is helpful information",
                ),
                cls="flex flex-wrap gap-4 items-center"
            ),
            cls="py-12 border-t"
        ),

        # ========== BADGES & BUTTONS ==========
        Section(
            H2("Buttons & Badges", cls="text-xl font-semibold mb-6"),
            Div(
                Div(
                    H4("Button Variants", cls="font-medium mb-3"),
                    Div(
                        Button("Primary", variant="primary"),
                        Button("Secondary", variant="secondary"),
                        Button("Outline", variant="outline"),
                        Button("Ghost", variant="ghost"),
                        Button("Destructive", variant="destructive"),
                        Button("Link", variant="link"),
                        cls="flex flex-wrap gap-2"
                    ),
                ),
                Div(
                    H4("Button Sizes", cls="font-medium mb-3"),
                    Div(
                        Button("Small", variant="sm"),
                        Button("Default"),
                        Button("Large", variant="lg"),
                        Button(LucideIcon("star"), variant="icon-outline"),
                        cls="flex flex-wrap items-center gap-2"
                    ),
                ),
                Div(
                    H4("Button Groups", cls="font-medium mb-3"),
                    DivLAligned(
                        ButtonGroup(
                            Button(LucideIcon("bold"), variant="outline"),
                            Button(LucideIcon("italic"), variant="outline"),
                            Button(LucideIcon("underline"), variant="outline"),
                        ),
                        ButtonGroup(
                            Button("Left", variant="outline"),
                            Button("Center", variant="outline"),
                            Button("Right", variant="outline"),
                        ),
                        ButtonGroup(
                            Button("Top", variant="outline"),
                            Button("Middle", variant="outline"),
                            Button("Bottom", variant="outline"),
                            orientation="vertical",
                        ),
                    )
                ),
                Div(
                    H4("Badge Variants", cls="font-medium mb-3"),
                    Div(
                        Badge("Primary"),
                        Badge("Secondary", variant="secondary"),
                        Badge("Outline", variant="outline"),
                        Badge("Destructive", variant="destructive"),
                        Badge(LucideIcon("check"), "Success"),
                        Badge(LucideIcon("clock"), "Pending", variant="secondary"),
                        cls="flex flex-wrap gap-2"
                    ),
                ),
                cls="space-y-6"
            ),
            cls="py-12 border-t"
        ),

        # ========== ALERTS ==========
        Section(
            H2("Alerts & Notifications", cls="text-xl font-semibold mb-6"),
            Div(
                Alert(
                    AlertTitle("Heads up!"),
                    AlertDescription("You can add components to your app using the CLI."),
                    icon="info",
                    variant="default",
                ),
                Alert(
                    AlertTitle("Success!"),
                    AlertDescription("Your changes have been saved successfully."),
                    icon="check-circle",
                    variant="success",
                ),
                Alert(
                    AlertTitle("Warning"),
                    AlertDescription("Your subscription is about to expire in 3 days."),
                    icon="alert-triangle",
                    variant="warning",
                ),
                Alert(
                    AlertTitle("Error"),
                    AlertDescription("There was a problem with your request. Please try again."),
                    icon="x-circle",
                    variant="destructive",
                ),
                cls="space-y-4 max-w-2xl"
            ),
            cls="py-12 border-t"
        ),

        # ========== LOADING STATES ==========
        Section(
            H2("Loading States", cls="text-xl font-semibold mb-6"),
            Div(
                Div(
                    H4("Spinners", cls="font-medium mb-3"),
                    Div(
                        Spinner(size="sm"),
                        Spinner(),
                        Spinner(size="lg"),
                        cls="flex items-center gap-4"
                    ),
                ),
                Div(
                    H4("Progress Bars", cls="font-medium mb-3"),
                    Div(
                        Progress(value=25, cls="w-full"),
                        Progress(value=50, cls="w-full"),
                        Progress(value=75, cls="w-full"),
                        Progress(value=100, cls="w-full"),
                        cls="space-y-3 max-w-md"
                    ),
                ),
                Div(
                    H4("Skeleton Loading", cls="font-medium mb-3"),
                    Card(
                        CardContent(
                            Div(
                                Skeleton(cls="size-12 rounded-full"),
                                Div(
                                    Skeleton(cls="h-4 w-32"),
                                    Skeleton(cls="h-3 w-24 mt-2"),
                                ),
                                cls="flex gap-4 items-center"
                            ),
                            Skeleton(cls="h-4 w-full mt-4"),
                            Skeleton(cls="h-4 w-3/4 mt-2"),
                        ),
                    ),
                ),
                cls="grid md:grid-cols-3 gap-8"
            ),
            cls="py-12 border-t"
        ),

        # ========== TOAST DEMO ==========
        Section(
            H2("Toast Notifications", cls="text-xl font-semibold mb-6"),
            ToastProvider(
                Div(
                    ToastTrigger(
                        "Show Toast", 
                        button_variant="outline",
                        title="Notification",
                        description="This is a toast message.",
                        icon="bell",
                    ),
                    ToastTrigger(
                        "Success Toast", 
                        button_variant="outline",
                        title="Success!",
                        description="Your action was completed.",
                        icon="check-circle",
                        variant="success",
                    ),
                    ToastTrigger(
                        "Error Toast", 
                        button_variant="destructive",
                        title="Error",
                        description="Something went wrong.",
                        icon="x-circle",
                        variant="destructive",
                    ),
                    cls="flex flex-wrap gap-4"
                ),
                Toaster(),
            ),
            cls="py-12 border-t"
        ),

        # ========== NAVIGATION ==========
        Section(
            H2("Navigation Components", cls="text-xl font-semibold mb-6"),
            Div(
                Div(
                    H4("Breadcrumbs", cls="font-medium mb-3"),
                    Breadcrumb(
                        BreadcrumbItem(A("Home", href="#")),
                        BreadcrumbSeparator(),
                        BreadcrumbItem(A("Components", href="#")),
                        BreadcrumbSeparator(),
                        BreadcrumbItem(A("Navigation", href="#"), current=True),
                    ),
                ),
                Div(
                    H4("Pagination", cls="font-medium mb-3"),
                    Pagination(total=100, per_page=10, current_page=5),
                ),
                Div(
                    H4("Keyboard Shortcuts", cls="font-medium mb-3"),
                    Div(
                        Div(
                            Span("Save", cls="text-sm"),
                            Div(Kbd("⌘"), Kbd("S"), cls="flex gap-1"),
                            cls="flex items-center justify-between"
                        ),
                        Div(
                            Span("Search", cls="text-sm"),
                            Div(Kbd("⌘"), Kbd("K"), cls="flex gap-1"),
                            cls="flex items-center justify-between"
                        ),
                        Div(
                            Span("New File", cls="text-sm"),
                            Div(Kbd("⌘"), Kbd("N"), cls="flex gap-1"),
                            cls="flex items-center justify-between"
                        ),
                        cls="space-y-2 p-4 bg-muted rounded-lg max-w-xs"
                    ),
                ),
                cls="grid md:grid-cols-3 gap-8"
            ),
            cls="py-12 border-t"
        ),

        # ========== TEAM SECTION ==========
        Section(
            Div(
                H2("Meet the Team", cls="text-2xl font-bold"),
                P("The talented people behind Nitro", cls="text-muted-foreground mt-2"),
                cls="text-center mb-8"
            ),
            Div(
                TeamMember("Sarah Chen", "Lead Designer", "sarah"),
                TeamMember("Alex Kim", "Core Developer", "alex"),
                TeamMember("Jordan Lee", "DevOps Engineer", "jordan"),
                TeamMember("Taylor Swift", "Product Manager", "taylor"),
                TeamMember("Morgan Blake", "Frontend Developer", "morgan"),
                TeamMember("Casey Rivers", "Backend Developer", "casey"),
                cls="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8"
            ),
            cls="py-12 border-t"
        ),

        signals=state,
        cls="pb-12"
    )
