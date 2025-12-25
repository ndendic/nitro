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
from .components import Sidebar, Navbar, Footer, PicSumImg, TitledSection, BackLink, ComponentShowcase
from functools import wraps


_P = ParamSpec("_P")
_R = TypeVar("_R")

# Shared headers for all documentation pages
hdrs = (    
    Script(type='module', src='/static/js/datastar-inspector.js'),
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
            Sidebar(),
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

