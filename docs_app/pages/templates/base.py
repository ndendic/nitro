"""
Shared utilities and configuration for component documentation pages.
All component documentation pages should import from this module.
"""

from fastapi.responses import HTMLResponse
from nitro import *  # noqa: F403
from nitro.infrastructure.html import *
from nitro.infrastructure.html.components import *
from typing import Callable, ParamSpec, TypeVar
from pathlib import Path
from domain.page_model import DocPage
from .components import Sidebar, Navbar, Footer, PicSumImg, H1, TitledSection, BackLink, ComponentShowcase
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

# Custom CSS for animations not in Tailwind
CUSTOM_CSS = """
@keyframes progress-indeterminate {
  0% { left: -40%; }
  100% { left: 100%; }
}
"""

# Shared headers for all documentation pages
hdrs = (
    # Inter font for typography
    Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
    Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900&family=JetBrains+Mono:wght@400;500;600&display=swap",
    ),
    Link(
        rel="stylesheet",
        href="https://unpkg.com/open-props@1.7.16/open-props.min.css",
        type="text/css",
    ),
    Style(CUSTOM_CSS),  # Custom animations
    Script("""{"imports": {"datastar": "https://cdn.jsdelivr.net/gh/starfederation/datastar@1.0.0-RC.6/bundles/datastar.js"}}""", type='importmap'),
    Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-persist@latest/dist/index.js'),
    Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-anchor@latest/dist/index.js'),
    Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-anchor@latest/dist/index.js'),

    Script(src='/static/js/datastar.js', type='module'),
    Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.7/dist/js/basecoat.min.js', defer=''),
    Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.7/dist/js/sidebar.min.js', defer=''),
    Script("""const datastar = JSON.parse(localStorage.getItem('datastar') || '{}');
console.log('datastar values', datastar);
const htmlElement = document.documentElement;
if ("darkMode" in datastar) {
  // Respect the value from localStorage if it exists
  if (datastar.darkMode === true) {
    htmlElement.classList.add('dark');
  } else {
    htmlElement.classList.remove('dark');
  }
} else {
  // Fallback to system color scheme if darkMode not in localStorage
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    htmlElement.classList.add('dark');
  } else {
    htmlElement.classList.remove('dark');
  }
}
htmlElement.setAttribute('data-theme', datastar.theme);"""),
)
# Shared HTML and body configuration
htmlkws = dict(lang="en", cls="bg-background text-foreground",data_theme="$theme")
bodykws = dict(
    cls="bg-background text-foreground",
    signals=Signals(message="", conn="",darkMode=True,theme="claude"),
)
ftrs = (
    CustomTag("datastar-inspector"),
    Div(data_persist="darkMode, theme")
)
# Shared page template
page = create_template(
    hdrs=hdrs,
    htmlkw=htmlkws,
    bodykw=bodykws,
    ftrs=ftrs,
    highlightjs=True,
    datastar=False,
    monsterui=False,
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
                        Div(func(*args, **kwargs), id="content"),
                        cls="p-4 md:p-6 xl:p-12 max-w-4xl mx-auto",
                    ),
                    Footer(),
                    cls="min-h-screen flex flex-col",
                    data_init="@get('/updates')",

                ),
            )
        return wrapper
    return decorator
