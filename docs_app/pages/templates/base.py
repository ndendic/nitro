"""
Shared utilities and configuration for component documentation pages.
All component documentation pages should import from this module.
"""

from fastapi.responses import HTMLResponse
from nitro import *  # noqa: F403
from nitro.infrastructure.html import *
from nitro.infrastructure.html import template as templ
from nitro.infrastructure.html.components import *
from typing import Callable, ParamSpec, TypeVar
from pathlib import Path
from domain.page_model import DocPage
from .components import Sidebar, Navbar, Footer, PicSumImg, TitledSection, BackLink, ComponentShowcase
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
    Script(src='https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/js/datepicker-full.min.js', type='module'),
    Script(type='module', src='https://cdn.jsdelivr.net/npm/@mbolli/datastar-attribute-on-keys@1/dist/index.js')
)
# Shared HTML and body configuration
htmlkws = dict(lang="en") # , cls="bg-background text-foreground",data_theme="$theme"
bodykws = dict(signals=Signals(message="", conn=""))
ftrs = (CustomTag("datastar-inspector"),)

# Shared page template
page = page_template(
    hdrs=hdrs,
    htmlkw=htmlkws,
    bodykw=bodykws,
    ftrs=ftrs,
    highlightjs=True,
    lucide=True,
)

@templ
def template(content, title: str):
    return page(
        Fragment(
            Sidebar(get_pages()),
            Main(
                Navbar(),
                Div(
                    Div(content, id="content"),
                    # cls="p-4 md:p-6 xl:p-12 max-w-4xl",
                    cls="pt-4 md:p-6 xl:p-12 container",
                ),
                Footer(),
                cls="min-h-screen flex flex-col",
                data_init="@get('/updates')",

            ),
        ), 
        title=title,
        wrap_in=HTMLResponse
    )

