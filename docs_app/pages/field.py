"""Field component documentation page"""

from .templates.base import *  # noqa: F403
from fastapi.requests import Request
from fastapi import APIRouter
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.events import on, emit_elements

from nitro.infrastructure.html.components import Field, Fieldset, Checkbox, Label

router: APIRouter = APIRouter()


def example_basic():
    return Div(
        Input(
            type="email", 
            id="email", 
            placeholder="you@example.com",
            label="Email",
            label_for="email",
        ),
        cls="max-w-sm"
    )


def example_with_description():
    return Div(
        Input(
            type="password", id="password", placeholder="Enter password",
            label="Password",
            label_for="password",
            supporting_text="Must be at least 8 characters with one number.",
        ),
        cls="max-w-sm"
    )


def example_with_error():
    return Div(
        Field(
            Input(type="text", id="username", placeholder="Enter username"),
            label="Username",
            label_for="username",
            error="Username is already taken. Please choose another.",
        ),
        cls="max-w-sm"
    )


def example_required():
    return Div(
        Field(
            Input(type="text", id="fullname", placeholder="Enter your name"),
            label="Full Name",
            label_for="fullname",
            required=True,
            description="Your legal name as it appears on official documents.",
        ),
        cls="max-w-sm"
    )


def example_horizontal():
    sigs = Signals(terms=False, newsletter=True)
    return Div(
        Field(
            Checkbox(id="agree-terms", bind=sigs.terms),
            Label("I agree to the terms and conditions", html_for="agree-terms"),
            orientation="horizontal",
        ),
        Field(
            Checkbox(id="newsletter-signup", bind=sigs.newsletter),
            Label("Subscribe to newsletter", html_for="newsletter-signup"),
            orientation="horizontal",
        ),
        Div(
            P("Terms: ", Span(data_text="$terms ? 'Accepted' : 'Not accepted'")),
            P("Newsletter: ", Span(data_text="$newsletter ? 'Subscribed' : 'Not subscribed'")),
            cls="mt-4 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="flex flex-col gap-4 max-w-md"
    )


def example_fieldset():
    return Div(
        Fieldset(
            Field(
                Input(type="text", id="first-name", placeholder="John"),
                label="First Name",
                label_for="first-name",
            ),
            Field(
                Input(type="text", id="last-name", placeholder="Doe"),
                label="Last Name",
                label_for="last-name",
            ),
            legend="Personal Information",
            description="Enter your full legal name.",
        ),
        cls="max-w-md"
    )


def example_complete_form():
    sigs = Signals(
        name="",
        email="",
        password="",
        terms=False
    )
    return Div(
        Fieldset(
            Field(
                Input(type="text", id="form-name", placeholder="Enter your name", data_bind="name"),
                label="Full Name",
                label_for="form-name",
                required=True,
            ),
            Field(
                Input(type="email", id="form-email", placeholder="you@example.com", data_bind="email"),
                label="Email Address",
                label_for="form-email",
                required=True,
                description="We'll never share your email with anyone.",
            ),
            Field(
                Input(type="password", id="form-password", placeholder="Create password", data_bind="password"),
                label="Password",
                label_for="form-password",
                required=True,
                description="Must be at least 8 characters.",
            ),
            legend="Create Account",
        ),
        Field(
            Checkbox(id="form-terms", bind=sigs.terms),
            Label("I agree to the ", A("terms of service", href="#"), html_for="form-terms"),
            orientation="horizontal",
            cls="mt-4",
        ),
        Button("Create Account", type="submit", cls="btn-primary mt-6"),
        Div(
            H4("Form State:", cls="font-medium mb-2"),
            P("Name: ", Span(data_text="$name || '(empty)'")),
            P("Email: ", Span(data_text="$email || '(empty)'")),
            P("Password: ", Span(data_text="$password ? '****' : '(empty)'")),
            P("Terms: ", Span(data_text="$terms ? 'Accepted' : 'Not accepted'")),
            cls="mt-6 p-4 bg-muted rounded text-sm"
        ),
        signals=sigs,
        cls="max-w-md"
    )


page = Div(
        H1("Field Component"),
        P(
            "Form field wrapper providing Basecoat context styling. All inputs inside Field "
            "are automatically styled via Basecoat CSS. Supports labels, descriptions, error "
            "states, and horizontal/vertical orientation."
        ),
        TitledSection(
            "Basic Field",
            P("A simple field with a label and input:"),
            ComponentShowcase(example_basic),
        ),
        TitledSection(
            "With Description",
            P("Field with helper text below the label:"),
            ComponentShowcase(example_with_description),
        ),
        TitledSection(
            "Error State",
            P("Field showing an error message with invalid styling:"),
            ComponentShowcase(example_with_error),
        ),
        TitledSection(
            "Required Field",
            P("Field with required indicator:"),
            ComponentShowcase(example_required),
        ),
        TitledSection(
            "Horizontal Orientation",
            P("Fields with horizontal layout, useful for checkboxes and toggles:"),
            ComponentShowcase(example_horizontal),
        ),
        TitledSection(
            "Fieldset",
            P("Group related fields with Fieldset and legend:"),
            ComponentShowcase(example_fieldset),
        ),
        TitledSection(
            "Complete Form Example",
            P("A realistic form using Field, Fieldset, and Datastar binding:"),
            ComponentShowcase(example_complete_form),
        ),
        TitledSection(
            "API Reference - Field",
            CodeBlock(
                """
def Field(
    *children,                    # Form input elements
    label: str = "",              # Field label text
    label_for: str = "",          # ID of associated input (for label)
    error: str = "",              # Error message (triggers invalid state)
    description: str = "",        # Helper text below label
    orientation: str = "vertical",# "vertical" or "horizontal"
    required: bool = False,       # Show required indicator (*)
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "API Reference - Fieldset",
            CodeBlock(
                """
def Fieldset(
    *children,                    # Field components to group
    legend: str = "",             # Fieldset title
    description: str = "",        # Helper text below legend
    cls: str = "",                # Additional CSS classes
    **attrs                       # Additional HTML attributes
) -> HtmlString
""",
                code_cls="language-python",
            ),
        ),
        TitledSection(
            "Basecoat CSS Structure",
            P("Field uses semantic HTML elements that Basecoat CSS targets:"),
            CodeBlock(
                """
<!-- Generated HTML structure -->
<div class="field" data-invalid="true">
    <label for="input-id">Label *</label>
    <p>Description text</p>
    <input id="input-id" type="text" />
    <p role="alert">Error message</p>
</div>

<!-- Horizontal orientation -->
<div class="field" data-orientation="horizontal">
    <input type="checkbox" id="cb" />
    <label for="cb">Label</label>
</div>
""",
                code_cls="language-html",
            ),
        ),
        TitledSection(
            "Usage with Datastar",
            CodeBlock(
                """
from nitro.infrastructure.html.datastar import Signals
from nitro.infrastructure.html.components import Field, Input

# Create signals for form state
form = Signals(email="", password="")

# Field with Datastar binding
Field(
    Input(type="email", id="email", data_bind="email"),
    label="Email",
    label_for="email",
    description="Enter your email address",
)

# Field with error (could be dynamically shown)
Field(
    Input(type="password", id="password", data_bind="password"),
    label="Password",
    label_for="password",
    error="Password is too short",  # Shows error state
)
""",
                code_cls="language-python",
            ),
        ),
        BackLink(),
        id="content"
    )

@router.get("/xtras/field")
@template(title="Field Component Documentation")
def field_page():
    return page

@on("page.field")
async def get_field(sender, request: Request, signals: Signals):
    yield emit_elements(page, topic="updates.page.field")