import inspect
from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *
from nitro.infrastructure.html import Section as HTMLSection
from datetime import datetime
from typing import Callable
from .sidebar import Sidebar

def Footer():
    """Footer component with links and attribution."""
    current_year = datetime.now().year
    return CustomTag(
        "footer",
        Div(
            # Left section - Branding
            Div(
                Span("Nitro", cls="font-bold text-lg"),
                Span("Framework", cls="text-muted-foreground ml-1"),
                cls="flex items-center",
            ),
            # Center section - Links
            Div(
                A(
                    "Documentation",
                    href="/",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                A(
                    "GitHub",
                    href="https://github.com/ndendic/nitro-systems",
                    target="_blank",
                    rel="noopener noreferrer",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                A(
                    "Basecoat UI",
                    href="https://basecoatui.com/",
                    target="_blank",
                    rel="noopener noreferrer",
                    cls="text-muted-foreground hover:text-foreground transition-colors",
                ),
                cls="flex gap-6",
            ),
            # Right section - Attribution
            Div(
                P(
                    f"© {current_year} Nitro Framework",
                    cls="text-muted-foreground text-sm",
                ),
                P(
                    "Built with ",
                    Span("Nitro", cls="font-medium text-foreground"),
                    " + ",
                    Span("RustyTags", cls="font-medium text-foreground"),
                    cls="text-muted-foreground text-sm",
                ),
                cls="text-right",
            ),
            cls="container mx-auto px-4 py-6 flex flex-col md:flex-row justify-between items-center gap-4",
        ),
        cls="border-t bg-background mt-auto",
    )


def Navbar():
    return Header(
        Div(
            # Sidebar toggle button
            Button(
                LucideIcon('panel-left'),
                type='button',
                onclick="document.dispatchEvent(new CustomEvent('basecoat:sidebar'))",
                variant="ghost",
            ),
            # Logo/Branding
            # A(
            #     LucideIcon('zap', cls="text-primary"),
            #     Span("Nitro", cls="font-bold"),
            #     href="/",
            #     cls="flex items-center gap-1 hover:opacity-80 transition-opacity",
            # ),
            # Site Search - centered with flex-grow
            Div(
                # SiteSearch(),
                cls="flex-1 flex justify-center mx-4",
            ),
            # Theme controls
            Div(
                Select(
                    Optgroup(
                        Option('Default', value='default'),
                        Option('Nitro', value='nitro'),
                        Option('Gruvbox', value='gruvbox'),
                        Option('Claude', value='claude'),
                        Option('Candy', value='candy'),
                        Option('Neo Brutalism', value='neo-brutal'),
                        Option('Dark Matter', value='darkmatter'),
                        label='Themes'
                    ),
                    bind='theme',
                    on_change="document.documentElement.setAttribute('data-theme', $theme);",
                    cls='select w-[180px]'
                ),
                Button(
                    LucideIcon('sun',  show="!$darkMode"),
                    LucideIcon('moon',  show="$darkMode"),
                    on_click="$darkMode = !$darkMode; $darkMode ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark');",
                    variant="outline"
                ),
                cls="flex gap-2"
            ),
            cls='flex h-14 w-full items-center gap-2 px-4'
        ),
        cls='bg-background sticky inset-x-0 top-0 isolate flex shrink-0 items-center gap-2 border-b z-10'
    )


def PicSumImg(
    h: int = 200,  # Height in pixels
    w: int = 200,  # Width in pixels
    id: int = None,  # Optional specific image ID to use
    grayscale: bool = False,  # Whether to return grayscale version
    blur: int = None,  # Optional blur amount (1-10)
    **kwargs,  # Additional args for Img tag
) -> HtmlString:  # Img tag with picsum image
    "Creates a placeholder image using https://picsum.photos/"
    url = f"https://picsum.photos"
    if id is not None:
        url = f"{url}/id/{id}"
    url = f"{url}/{w}/{h}"
    if grayscale:
        url = f"{url}?grayscale"
    if blur is not None:
        url = f"{url}{'?' if not grayscale else '&'}blur={max(1, min(10, blur))}"
    return Img(src=url, loading="lazy", **kwargs)

def DiceBearAvatar(
    seed_name: str,  # Seed name (ie 'Isaac Flath')
    h: int = 24,  # Height
    w: int = 24,  # Width
):  # Span with Avatar
    "Creates an Avatar using https://dicebear.com/"
    url = "https://api.dicebear.com/8.x/lorelei/svg?seed="
    return Span(    
        Img(
            cls="aspect-square",
            alt="Avatar",
            loading="lazy",
            src=f"{url}{seed_name}",
            style=f"width: {w}px; height: {h}px;",
        ),
        cls="relative flex shrink-0 overflow-hidden rounded-full bg-secondary"
    )

def TitledSection(title, *content, cls="fluid-flex bg-background"):
    """Utility function for creating documentation sections"""
    return HTMLSection(H2(title, cls="text-2xl font-bold my-4"), *content, cls=cls)


def BackLink(href="/", text="← Back to Home"):
    """Standard back navigation link"""
    return Div(
        A(text, href=href, cls="color-blue-6 text-decoration-underline"), cls="my-8"
    )


def get_code(component: Callable):
    code = ""
    for line in inspect.getsource(component).split("\n"):
        if not line.strip().startswith("def"):
            code += line[4:] + "\n"
    code = code.replace("return ", "")
    return code


def ComponentShowcase(component: Callable):
    return Tabs(
        TabsList(
            TabsTrigger("Preview", id="tab1"),
            TabsTrigger("Code", id="tab2"),
        ),
        TabsContent(
            component(),
            id="tab1",
            style="padding: 1rem; border: 1px solid; border-radius: 0.5rem;",
        ),
        TabsContent(
            CodeBlock(
                get_code(component),
                cls="language-python",
                style="border: 1px solid; border-radius: 0.5rem;",
                data_init="hljs.highlightAll()"
            ),
            id="tab2",
        ),
        default_tab="tab1",
        cls="mt-4",
    )