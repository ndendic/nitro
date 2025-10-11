"""
Shared utilities and configuration for component documentation pages.
All component documentation pages should import from this module.
"""
import inspect
from nitro import *
from nitro import Section as HTMLSection
from nitro.starlette import *
from nitro.html.components import CodeBlock, Tabs, TabsList, TabsTrigger, TabsContent
from typing import Callable

# Shared headers for all documentation pages
hdrs = (
    Link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css", type="text/css"),
    Link(rel="stylesheet", href="https://unpkg.com/open-props@1.7.16/open-props.min.css", type="text/css"),
    Link(rel="stylesheet", href="https://github.com/argyleink/open-props/blob/main/src/props.fonts.css", type="text/css"),
    Script("""
        import { load, apply } from 'https://cdn.jsdelivr.net/gh/starfederation/datastar@main/bundles/datastar.js';
        import AnchorPlugin from 'https://cdn.jsdelivr.net/gh/ndendic/data-satelites@master/dist/min/anchor.min.js';
        import PersistPlugin from 'https://cdn.jsdelivr.net/gh/ndendic/data-satellites@master/dist/min/persist.min.js';
        load(AnchorPlugin, PersistPlugin);
        apply();""",
        type='module'
    ),
    Script(src="/static/js/datastar-inspector.js", type="module"),
    Style("""
html {
    min-height: 100vh;
    color: light-dark(var(--gray-9), var(--gray-1));
    font-family: var(--font-neo-grotesque);
    font-size: var(--font-size-fluid-0);
    letter-spacing: var(--font-letterspacing-1);
  }
  main {
    width: min(100% - 2rem, 45rem);
    margin-inline: auto;
  }
  .dialog {
    top: 0;
    bottom: 0;
    opacity: 0;
    transition: all;
    transition-behavior: allow-discrete;

    &:is([open],:popover-open) {
      opacity: 100;

      &::backdrop {
        opacity: 100;
      }
      > article {
        scale: 100;
      }

      @starting-style {
        opacity: 0;

        &::backdrop {
          opacity: 0;
        }
        > article {
          scale: 95;
        }
      }
    }
    &::backdrop {
      opacity: 0;
      transition: all;
      transition-behavior: allow-discrete;
    }
  }
}
    """),
)

# Shared HTML and body configuration
htmlkws = dict(lang="en")
bodykws = dict(signals=Signals(message="", conn=""))
ftrs = (
    CustomTag("datastar-inspector"),
)
# Shared page template
page = create_template(hdrs=hdrs, htmlkw=htmlkws, bodykw=bodykws, ftrs=ftrs, highlightjs=True, datastar=False, lucide=True)

def Section(title, *content):
    """Utility function for creating documentation sections"""
    return HTMLSection(
        H2(title),
        *content,
        cls="fluid-flex"
    )

def BackLink(href="/", text="← Back to Home"):
    """Standard back navigation link"""
    return Div(
        A(text, href=href, cls="color-blue-6 text-decoration-underline"),
        cls="mt-8"
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
                style="margin-bottom: 1rem;"
            ),
            TabsContent(component(), id="tab1", style="padding: 1rem; border: 1px solid; border-radius: 0.5rem;"),
            TabsContent(CodeBlock(get_code(component), cls="language-python", style="border: 1px solid; border-radius: 0.5rem;"), id="tab2"),
            default_tab="tab1",
        )