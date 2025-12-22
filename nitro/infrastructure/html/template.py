"""
Nitro Templates - Advanced templating system for web applications.

This module provides enhanced templating functionality moved from the core utils
to provide better separation of concerns in the Nitro framework.
"""

from asyncio import iscoroutine, iscoroutinefunction
from typing import Optional, Callable, ParamSpec, TypeVar
from functools import partial, wraps
from rusty_tags import Html, Head, Title, Body, HtmlString, Script, Fragment, Link, Div
from rusty_tags.datastar import Signals
from nitro.config import NitroConfig
from nitro.infrastructure.html.components.utils import cn

P = ParamSpec("P")
R = TypeVar("R")

config = NitroConfig()

HEADER_URLS = {
    # Lucide icons
    "lucide": "https://unpkg.com/lucide@latest",
    # Tailwind 4
    "tailwind4": "https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4",
    # FrankenUI
    "franken_css": "https://cdn.jsdelivr.net/npm/franken-ui@2.1.1/dist/css/core.min.css",
    "franken_js_core": "https://cdn.jsdelivr.net/npm/franken-ui@2.1.1/dist/js/core.iife.js",
    "franken_icons": "https://cdn.jsdelivr.net/npm/franken-ui@2.1.1/dist/js/icon.iife.js",
    # Highlight.js
    "highlight_js": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js",
    "highlight_python": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/languages/python.min.js",
    "highlight_light_css": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/atom-one-light.css",
    "highlight_dark_css": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/atom-one-dark.css",
    "highlight_copy": "https://cdn.jsdelivr.net/gh/arronhunt/highlightjs-copy/dist/highlightjs-copy.min.js",
    "highlight_copy_css": "https://cdn.jsdelivr.net/gh/arronhunt/highlightjs-copy/dist/highlightjs-copy.min.css",
}

def add_nitro_components(hdrs: tuple, htmlkw: dict, bodykw: dict, ftrs: tuple):
    hdrs += (
        Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.7/dist/js/basecoat.min.js', defer=''),
        Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.7/dist/js/sidebar.min.js', defer=''),
        Script("""const datastar = JSON.parse(localStorage.getItem('datastar') || '{}');
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
    htmlElement.setAttribute('data-theme', datastar.theme);""")
    )
    htmlkw["data_theme"] = "$theme"
    htmlkw["cls"] = cn("bg-background text-foreground") if htmlkw.get("cls") is None else cn(htmlkw.get("cls"), "bg-background text-foreground")
    ftrs += (Div(Div(data_persist="darkMode, theme"),**{"data-signals__ifmissing:darkMode": "true", "data-signals__ifmissing:theme": "'claude'"}),)
    return hdrs, htmlkw, bodykw, ftrs

def add_highlightjs(hdrs: tuple, ftrs: tuple):
    hdrs += (  # pyright: ignore[reportOperatorIssue]
        Script(src=HEADER_URLS["highlight_js"]),
        Script(src=HEADER_URLS["highlight_python"]),
        Link(
            rel="stylesheet", href=HEADER_URLS["highlight_light_css"], id="hljs-light"
        ),
        Link(rel="stylesheet", href=HEADER_URLS["highlight_dark_css"], id="hljs-dark"),
        Script(src=HEADER_URLS["highlight_copy"]),
        Link(rel="stylesheet", href=HEADER_URLS["highlight_copy_css"]),
        Script(
            """
                    hljs.addPlugin(new CopyButtonPlugin());
                    hljs.configure({
                        cssSelector: 'pre code',
                        languages: ['python'],
                        ignoreUnescapedHTML: true
                    });
                    function updateTheme() {
                        const isDark = document.documentElement.classList.contains('dark');
                        document.getElementById('hljs-dark').disabled = !isDark;
                        document.getElementById('hljs-light').disabled = isDark;
                    }
                    new MutationObserver(mutations =>
                        mutations.forEach(m => m.target.tagName === 'HTML' &&
                            m.attributeName === 'class' && updateTheme())
                    ).observe(document.documentElement, { attributes: true });
                    updateTheme();
                    hljs.highlightAll();
                """,
            type="module",
        ),
    )
    ftrs += (Script("hljs.highlightAll();"),)
    return hdrs, ftrs


def Page(
    *content,
    title: str = "Nitro",
    hdrs: tuple | None = None,
    ftrs: tuple | None = None,
    htmlkw: dict | None = None,
    bodykw: dict | None = None,
    datastar: bool = True,
    ds_version: str = "1.0.0-RC.6",
    nitro_components: bool = True,
    monsterui: bool = False,
    tailwind4: bool = False,
    lucide: bool = False,
    highlightjs: bool = False,
) -> HtmlString:
    """Base page layout with common HTML structure."""
    # initialize empty tuple if None
    hdrs = hdrs if hdrs is not None else ()
    ftrs = ftrs if ftrs is not None else ()
    htmlkw = htmlkw if htmlkw is not None else {}
    bodykw = bodykw if bodykw is not None else {}
    tailwind_css = config.tailwind.css_output
    tw_configured = tailwind_css.exists()

    if tailwind4:
        hdrs += (Script(src=HEADER_URLS["tailwind4"]),)
    if highlightjs:
        hdrs, ftrs = add_highlightjs(hdrs, ftrs)
    if lucide:
        hdrs += (Script(src=HEADER_URLS["lucide"]),)
        ftrs += (Script("lucide.createIcons();"),)
    if monsterui:
        hdrs += (Link(rel="stylesheet", href=HEADER_URLS["franken_css"]),)
        hdrs += (Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/franken-ui@2.1.1/dist/css/utilities.min.css"),)
        hdrs += (Script(src=HEADER_URLS["franken_js_core"], type="module"),)
        hdrs += (Script(src=HEADER_URLS["franken_icons"], type="module"),)
    if datastar:
        hdrs = (   
        Script(f"""{{"imports": {{"datastar": "https://cdn.jsdelivr.net/gh/starfederation/datastar@{ds_version}/bundles/datastar.js"}}}}""", type='importmap'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-persist@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-anchor@latest/dist/index.js')) + hdrs
    if tw_configured:
        hdrs += (Link(rel="stylesheet", href=f"/{tailwind_css}", type="text/css"),)
    if nitro_components:
        hdrs, htmlkw, bodykw, ftrs = add_nitro_components(hdrs,htmlkw, bodykw, ftrs)

    return Html(
        Head(
            Title(title),
            *hdrs if hdrs else (),
        ),
        Body(
            *content,
            *ftrs if ftrs else (),
            **bodykw if bodykw else {},
        ),
        **htmlkw if htmlkw else {},
    )


def create_template(
    page_title: str = "MyPage",
    hdrs: Optional[tuple] = None,
    ftrs: Optional[tuple] = None,
    htmlkw: Optional[dict] = None,
    bodykw: Optional[dict] = None,
    datastar: bool = True,
    ds_version: str = "1.0.0-RC.6",
    nitro_components: bool = True,
    monsterui: bool = False,
    lucide: bool = True,
    highlightjs: bool = False,
    tailwind4: bool = False,
):
    """Create a decorator that wraps content in a Page layout.

    Returns a decorator function that can be used to wrap view functions.
    The decorator will take the function's output and wrap it in the Page layout.
    """
    page_func = partial(
        Page,
        hdrs=hdrs,
        ftrs=ftrs,
        htmlkw=htmlkw,
        bodykw=bodykw,
        datastar=datastar,
        ds_version=ds_version,
        nitro_components=nitro_components,
        monsterui=monsterui,
        lucide=lucide,
        highlightjs=highlightjs,
        tailwind4=tailwind4,
    )

    def page(title: str | None = None, wrap_in: Callable | None = None):
        def decorator(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                if iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                if wrap_in:
                    return wrap_in(
                        page_func(result, title=title if title else page_title)
                    )
                else:
                    return page_func(result, title=title if title else page_title)

            return wrapper

        return decorator

    return page


def page_template(
    page_title: str = "MyPage",
    hdrs: Optional[tuple] = None,
    ftrs: Optional[tuple] = None,
    htmlkw: Optional[dict] = None,
    bodykw: Optional[dict] = None,
    datastar: bool = True,
    ds_version: str = "1.0.0-RC.6",
    nitro_components: bool = True,
    monsterui: bool = False,
    tailwind4: bool = False,
    lucide: bool = False,
    highlightjs: bool = False,
):
    """Create a decorator that wraps content in a Page layout.

    Returns a decorator function that can be used to wrap view functions.
    The decorator will take the function's output and wrap it in the Page layout.
    """
    template = partial(
        Page,
        hdrs=hdrs,
        ftrs=ftrs,
        htmlkw=htmlkw,
        bodykw=bodykw,
        title=page_title,
        datastar=datastar,
        ds_version=ds_version,
        nitro_components=nitro_components,
        monsterui=monsterui,
        lucide=lucide,
        tailwind4=tailwind4,
        highlightjs=highlightjs,
    )
    return template
