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


# Shared headers for all documentation pages
hdrs = (
    Script(src='/static/js/datastar.js', type='module'),
)
# Shared HTML and body configuration
htmlkws = dict(lang="en") # , cls="bg-background text-foreground",data_theme="$theme"
bodykws = dict()
ftrs = (CustomTag("datastar-inspector"),)
# Shared page template
page = create_template(
    hdrs=hdrs,
    htmlkw=htmlkws,
    bodykw=bodykws,
    ftrs=ftrs,
    highlightjs=True,
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
