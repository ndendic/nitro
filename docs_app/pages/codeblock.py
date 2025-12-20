"""CodeBlock component documentation page"""

from .templates.base import *
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.events import on, emit_elements

router: APIRouter = APIRouter()


def example_1():
    return CodeBlock("print('Hello, World!')")

def example_2():
    return CodeBlock(
        "const greeting = 'Hello, World!';\nconsole.log(greeting);", 
        cls="border-1 border-radius-2 p-3 surface-2",
        code_cls="language-javascript"
    )
    
page = Div(
        H1("CodeBlock Component"),
        P("The CodeBlock component provides a semantic structure for displaying code with proper HTML markup and styling hooks."),
        
        TitledSection("Component Purpose",
            P("CodeBlock is an anatomical pattern that solves:"),
            Ul(
                Li("🏗️ Consistent semantic HTML structure (Div > Pre > Code)"),
                Li("🎨 Flexible styling with separate classes for container and code"),
                Li("⚡ Simple API for common code display patterns"),
                Li("🔧 Integration with syntax highlighting libraries"),
            ),
        ),
        
        TitledSection("Basic Usage",
            P("Simple code block without styling:"),
            ComponentShowcase(example_1),
        ),
        
        TitledSection("With Styling",
            P("CodeBlock with Open Props styling:"),
            ComponentShowcase(example_2),
        ),
        
        TitledSection("API Reference",
            P("CodeBlock component parameters:"),
            CodeBlock("""
def CodeBlock(
*content: str,      # Text content for the code block
cls: str = "",      # CSS classes for outer container
code_cls: str = "", # CSS classes for code element  
**kwargs: Any       # Additional HTML attributes for code element
) -> rt.HtmlString""", code_cls="language-python"),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/codeblock")
@template(title="CodeBlock Component Documentation")
def codeblock_page():
    return page

@on("page.codeblock")
async def get_codeblock(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.codeblock")