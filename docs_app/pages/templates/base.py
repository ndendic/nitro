"""
Shared utilities and configuration for component documentation pages.
All component documentation pages should import from this module.
"""

import inspect
from fastapi.responses import HTMLResponse
from nitro import *  # noqa: F403
from nitro.infrastructure.html import Section as HTMLSection
from nitro.infrastructure.html.components import *
from typing import Callable, ParamSpec, TypeVar
from pathlib import Path
from domain.page_model import DocPage
from .components import Sidebar, Navbar
from functools import wraps


_P = ParamSpec("_P")
_R = TypeVar("_R")

def get_pages():
    content_dir = Path(__file__).parent.parent.parent / "content"
    md_files = list(content_dir.rglob("*.md"))
    all_pages = []
    for md_file in md_files:
        try:
            page_obj = DocPage.load_from_fs(md_file)
            all_pages.append(page_obj)
        except Exception as e:
            print(f"Error loading {md_file}: {e}")
            continue
    return all_pages

# Shared headers for all documentation pages
hdrs = (
    Link(
        rel="stylesheet",
        href="https://unpkg.com/open-props@1.7.16/open-props.min.css",
        type="text/css",
    ),
    Link(
        rel="stylesheet",
        href="https://github.com/argyleink/open-props/blob/main/src/props.fonts.css",
        type="text/css",
    ),
    Script("""{"imports": {"datastar": "https://cdn.jsdelivr.net/gh/starfederation/datastar@1.0.0-RC.6/bundles/datastar.js"}}""", type='importmap'),
    Script(type='module', src='https://cdn.jsdelivr.net/gh/starfederation/datastar@1.0.0-RC.6/bundles/datastar.js'),
    Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-persist@latest/dist/index.js'),

    Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.6/dist/js/basecoat.min.js', defer=''),
    Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.6/dist/js/sidebar.min.js', defer='')
)
# Shared HTML and body configuration
htmlkws = dict(lang="en", cls="bg-background text-foreground",data_theme="$theme")
bodykws = dict(
    cls="bg-background text-foreground",
    signals=Signals(message="", conn="",darkMode=True,theme="claude"),
)
ftrs = (
    CustomTag("datastar-inspector"),
    Div(
        cls="hidden",
        data_persist="darkMode, theme",
        data_effect="$darkMode ? document.documentElement.classList.add('dark') : document.documentElement.classList.remove('dark'); document.documentElement.setAttribute('data-theme', $theme);",
    )
)
# Shared page template
page = create_template(
    hdrs=hdrs,
    htmlkw=htmlkws,
    bodykw=bodykws,
    ftrs=ftrs,
    highlightjs=True,
    datastar=False,
    monsterui=True,
    lucide=True,
)


def template(title: str):
    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]:
        @page(title=title, wrap_in=HTMLResponse)
        @wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return Fragment(
                Sidebar(get_pages()),
                Main(
                    Navbar(),
                    Div(
                        func(*args, **kwargs),
                        cls="px-8 lg:px-16 xl:px-32 my-16"
                    ),
                ),
            )
        return wrapper
    return decorator


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
            ),
            id="tab2",
        ),
        default_tab="tab1",
    )
