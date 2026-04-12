"""Form validation helpers — render Pydantic errors as inline HTML fragments.

Provides utilities to catch Pydantic ValidationError and re-render forms
with inline error messages, fully server-side via SSE.
"""
from typing import Any, Dict, List, Optional, Callable
from pydantic import ValidationError


def extract_errors(exc: ValidationError) -> Dict[str, str]:
    """Extract field-level error messages from a Pydantic ValidationError.

    Returns:
        Dict mapping field names to their first error message.
    """
    errors = {}
    for error in exc.errors():
        field = str(error["loc"][0]) if error["loc"] else "_root"
        if field not in errors:  # Keep first error per field
            errors[field] = error["msg"]
    return errors


def error_message(field_name: str, errors: Dict[str, str], cls: str = "text-destructive text-sm mt-1") -> str:
    """Render an inline error message for a field if it has an error.

    Args:
        field_name: The field to check for errors
        errors: Dict from extract_errors()
        cls: CSS classes for the error element

    Returns:
        HTML string — error paragraph if field has error, empty string otherwise.
    """
    msg = errors.get(field_name)
    if not msg:
        return ""
    # Import here to avoid circular imports at module level
    from nitro.html import P
    return str(P(msg, cls=cls, id=f"error-{field_name}"))


def form_errors_fragment(
    exc: ValidationError,
    form_data: Dict[str, Any],
    render_form: Callable[[Dict[str, Any], Dict[str, str]], Any],
) -> Any:
    """Handle a ValidationError by re-rendering the form with errors.

    This is the main integration point. Pass your form renderer and it
    returns the re-rendered form with inline errors.

    Args:
        exc: The Pydantic ValidationError
        form_data: The original form data that failed validation
        render_form: A callable(data, errors) that returns the form HTML

    Returns:
        The result of render_form() with error messages injected.

    Example:
        @post()
        async def create_post(self, request, **signals):
            try:
                data = PostForm(**signals)
                # ... save logic
            except ValidationError as e:
                return form_errors_fragment(e, signals, render_post_form)
    """
    errors = extract_errors(exc)
    return render_form(form_data, errors)


def validated(form_class):
    """Decorator that auto-validates signals against a Pydantic model.

    If validation fails, looks for a `_render_form` method on the entity
    or a `render_form` function in the handler's module, and returns the
    re-rendered form with errors.

    Usage:
        class PostForm(BaseModel):
            title: str
            content: str

        class Post(Entity, table=True):
            title: str = ""
            content: str = ""

            @post()
            @validated(PostForm)
            async def create(self, request, form: PostForm):
                self.title = form.title
                self.content = form.content
                self.save()
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract signals from kwargs
            signals = {k: v for k, v in kwargs.items() if k not in ("self", "cls", "request", "sender")}
            try:
                form = form_class(**signals)
                kwargs["form"] = form
                return await func(*args, **kwargs)
            except ValidationError as e:
                errors = extract_errors(e)
                # Return errors dict for the handler to use
                kwargs["form_errors"] = errors
                kwargs["form"] = None
                return await func(*args, **kwargs)
        return wrapper
    return decorator
