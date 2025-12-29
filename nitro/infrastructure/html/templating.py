"""
Nitro Templates - Advanced templating system for web applications.

This module provides enhanced templating functionality moved from the core utils
to provide better separation of concerns in the Nitro.
"""

from asyncio import iscoroutinefunction
from typing import Optional, Callable, ParamSpec, TypeVar
from functools import wraps
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
    "franken_js_core": "https://cdn.jsdelivr.net/npm/franken-ui@2.1.1/dist/js/core.iife.js",
    "franken_chart": "https://cdn.jsdelivr.net/npm/franken-ui@2.0.0/dist/js/chart.iife.js",
    # Highlight.js
    "highlight_js": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js",
    "highlight_python": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/languages/python.min.js",
    "highlight_copy": "https://cdn.jsdelivr.net/gh/arronhunt/highlightjs-copy/dist/highlightjs-copy.min.js",
    "highlight_copy_css": "https://cdn.jsdelivr.net/gh/arronhunt/highlightjs-copy/dist/highlightjs-copy.min.css",
}

def template(func):
    func_is_async = iscoroutinefunction(func)
    
    def make_wrapper(inner, *args, **kwargs):
        inner_is_async = iscoroutinefunction(inner)
        
        if func_is_async or inner_is_async:
            @wraps(inner)
            async def wrapped(*inner_args, **inner_kwargs):
                content = await inner(*inner_args, **inner_kwargs) if inner_is_async else inner(*inner_args, **inner_kwargs)
                return await func(content, *args, **kwargs) if func_is_async else func(content, *args, **kwargs)
            return wrapped
        else:
            @wraps(inner)
            def wrapped(*inner_args, **inner_kwargs):
                content = inner(*inner_args, **inner_kwargs)
                return func(content, *args, **kwargs)
            return wrapped
    
    @wraps(func)
    def decorator(*args, **kwargs):
        if not args:
            return lambda inner: make_wrapper(inner, **kwargs)
        
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return make_wrapper(args[0])
        
        return func(*args, **kwargs)
    
    return decorator

def add_nitro_components(hdrs: tuple, htmlkw: dict, bodykw: dict, ftrs: tuple):
    hdrs += (
        Script(src='https://cdn.jsdelivr.net/npm/basecoat-css@0.3.7/dist/js/basecoat.min.js', defer=''),
        Script(src='https://cdn.jsdelivr.net/npm/vanillajs-datepicker@1.3.4/dist/js/datepicker-full.min.js', type='module'),
        Script("""const datastar = JSON.parse(localStorage.getItem('datastar') || '{}');
    const htmlElement = document.documentElement;
    if ("darkMode" in datastar) {
    if (datastar.darkMode === true) {
        htmlElement.classList.add('dark');
    } else {
        htmlElement.classList.remove('dark');
    }
    } else {
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
    ftrs += (Div(Div(data_persist="darkMode, theme"),**{"data-signals:darkMode__ifmissing": "true", "data-signals:theme__ifmissing": "'nitro'"}),)
    return hdrs, htmlkw, bodykw, ftrs

def add_highlightjs(hdrs: tuple, ftrs: tuple):
    hdrs += (  # pyright: ignore[reportOperatorIssue]
        Script(src=HEADER_URLS["highlight_js"]),
        Script(src=HEADER_URLS["highlight_python"]),
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
    charts: bool = False,
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
    if charts:
        hdrs += (Script(src=HEADER_URLS["franken_js_core"], type="module"),)
        hdrs += (Script(src=HEADER_URLS["franken_chart"], type="module"),)
    if datastar:
        hdrs = (   
        Script(f"""{{"imports": {{"datastar": "https://cdn.jsdelivr.net/gh/starfederation/datastar@{ds_version}/bundles/datastar.js"}}}}""", type='importmap'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-persist@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-anchor@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-resize@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-scroll@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-split@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/gh/ndendic/data-drag@latest/dist/index.js'),
        Script(type='module', src='https://cdn.jsdelivr.net/npm/@mbolli/datastar-attribute-on-keys@1/dist/index.js'),
        ) + hdrs
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


def page_template(
    page_title: str = "Nitro",
    hdrs: Optional[tuple] = None,
    ftrs: Optional[tuple] = None,
    htmlkw: Optional[dict] = None,
    bodykw: Optional[dict] = None,
    datastar: bool = True,
    ds_version: str = "1.0.0-RC.6",
    nitro_components: bool = True,
    charts: bool = False,
    tailwind4: bool = False,
    lucide: bool = False,
    highlightjs: bool = False,
):
    """Create a page template that can be used as both a decorator and a direct call.

    Returns a template function that supports three usage patterns:

    1. Direct call:
        template = page_template("My App")
        html = template(Div("content"), title="Home")

    2. Decorator without args:
        @template
        def index():
            return Div("Home")

    3. Decorator with args:
        @template(title="About", wrap_in=HTMLResponse)
        def about():
            return Div("About")
    """
    @template
    def page(
        *content,
        title: str | None = None,
        wrap_in: Callable | None = None,
    ):
        result = Page(
            *content,
            title=title if title else page_title,
            hdrs=hdrs,
            ftrs=ftrs,
            htmlkw=htmlkw,
            bodykw=bodykw,
            datastar=datastar,
            ds_version=ds_version,
            nitro_components=nitro_components,
            charts=charts,
            lucide=lucide,
            highlightjs=highlightjs,
            tailwind4=tailwind4,
        )
        if wrap_in:
            return wrap_in(result)
        return result

    return page

# legacy function for backwards compatibility
create_template = page_template