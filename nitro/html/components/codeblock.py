from typing import Any
import rusty_tags as rt
from .utils import cn


def CodeSpan(
    *c,  # Contents of CodeSpan tag (inline text code snippets)
    cls="",  # Classes in addition to CodeSpan styling
    **kwargs,  # Additional args for CodeSpan tag
) -> rt.HtmlString:  # Code(..., cls='codespan')
    "A CodeSpan with Styling"
    return rt.Code(*c, cls=cn("codespan", cn(cls)), **kwargs)

DEFAULT_PRE_CLS = "grid text-sm overflow-auto rounded-xl scrollbar"

def CodeBlock(
    *content: str,  # Contents of Code tag (often text)
    cls: str = "",  # Classes for the outer container
    code_cls: str = "",  # Classes for the code tag
    pre_cls: str | None = None,  # Classes for the pre tag (None = use defaults)
    **kwargs: Any  # Additional args for Code tag
) -> rt.HtmlString:
    """
    CodeBlock with styling - wraps content in Div > Pre > Code structure.
    
    This is our first "anatomical pattern" component that provides a common
    structure for displaying code with proper semantic HTML and styling hooks.
    
    Args:
        *content: Text content to display in the code block
        cls: CSS classes for the outer container div
        code_cls: CSS classes for the inner code element
        pre_cls: CSS classes for the pre element (None uses defaults with rounded corners)
        **kwargs: Additional HTML attributes for the code element
    
    Returns:
        Styled code block with proper semantic structure
        
    Example:
        CodeBlock("print('Hello, World!')", 
                 cls="border rounded p-4", 
                 code_cls="language-python")
    """
    # Use default pre_cls if not specified
    effective_pre_cls = DEFAULT_PRE_CLS if pre_cls is None else pre_cls
    
    return rt.Div(
        rt.Pre(
            rt.Code(*content, cls=cn(code_cls), **kwargs),
            cls=cn(effective_pre_cls),
        ),
        cls=cn(cls)
    )