"""RustyTags Datastar SDK documentation page"""

from .base import *
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from nitro.datastar import Signal, Signals, if_, match, classes, collect, all as all_cond, any as any_cond, f

router = APIRouter()

def example_basic_counter():
    sigs = Signals(counter=0)
    return Div(
        Div(
            Button("-", on_click=sigs.counter.sub(1), style="padding: 0.5rem 1rem;"),
            Span(text=sigs.counter, style="font-size: 2rem; padding: 0 1rem; font-weight: bold;"),
            Button("+", on_click=sigs.counter.add(1), style="padding: 0.5rem 1rem;"),
            Button("Reset", on_click=sigs.counter.set(0), style="padding: 0.5rem 1rem; margin-left: 1rem;"),
            style="display: flex; gap: 0.5rem; align-items: center; justify-content: center;"
        ),
        signals=sigs
    )

def example_arithmetic():
    numbers = Signals(x=10, y=3)
    return Div(
        Div(
            Div(
                Label("X: "),
                Input(type="number", bind=numbers.x, style="width: 80px; padding: 0.25rem;"),
                style="display: flex; gap: 0.5rem; align-items: center;"
            ),
            Div(
                Label("Y: "),
                Input(type="number", bind=numbers.y, style="width: 80px; padding: 0.25rem;"),
                style="display: flex; gap: 0.5rem; align-items: center;"
            ),
            style="display: flex; gap: 1rem; margin-bottom: 1rem;"
        ),
        Div(
            P(text="Sum: " + (numbers.x + numbers.y)),
            P(text="Difference: " + (numbers.x - numbers.y)),
            P(text="Product: " + (numbers.x * numbers.y)),
            P(text="Division: " + (numbers.x / numbers.y)),
            P(text="Modulo: " + (numbers.x % numbers.y)),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        signals=numbers
    )

def example_conditional():
    score = Signal("score", 75)
    return Div(
        Div(
            Label("Score: "),
            Input(type="number", bind=score, style="width: 100px; padding: 0.25rem;"),
            style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1rem;"
        ),
        Div(
            P(text="Grade: " + if_(score >= 90, "A", if_(score >= 80, "B", if_(score >= 70, "C", "F")))),
            P(text="Status: " + if_(score >= 60, "Pass", "Fail")),
            Div(
                text=if_(score >= 90, "🎉 Excellent!", if_(score >= 70, "👍 Good", "📚 Keep trying")),
                style="font-size: 2rem; text-align: center; padding: 1rem;"
            ),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        Div(
            Button("-10", on_click=score.sub(10), style="padding: 0.5rem 1rem;"),
            Button("+10", on_click=score.add(10), style="padding: 0.5rem 1rem;"),
            style="display: flex; gap: 0.5rem; margin-top: 1rem;"
        ),
        signals={"score": 75}
    )

def example_pattern_matching():
    state = Signals(status="idle")
    return Div(
        Div(
            P(text="Current Status: " + state.status, style="font-weight: bold;"),
            Div(
                text=match(
                    state.status,
                    idle="⏸️ Ready to start",
                    loading="⏳ Processing...",
                    success="✅ Completed!",
                    error="❌ Failed!",
                    default="❓ Unknown"
                ),
                style="font-size: 1.5rem; text-align: center; padding: 1rem; background: var(--gray-2); border-radius: 0.5rem; margin: 1rem 0;"
            ),
        ),
        Div(
            Button("Idle", on_click=state.status.set("idle"), style="padding: 0.5rem 1rem;"),
            Button("Loading", on_click=state.status.set("loading"), style="padding: 0.5rem 1rem;"),
            Button("Success", on_click=state.status.set("success"), style="padding: 0.5rem 1rem;"),
            Button("Error", on_click=state.status.set("error"), style="padding: 0.5rem 1rem;"),
            style="display: flex; gap: 0.5rem; flex-wrap: wrap;"
        ),
        signals=state
    )

def example_string_methods():
    text = Signal("text", "Hello World")
    return Div(
        Div(
            Input(type="text", bind=text, placeholder="Enter text", style="width: 100%; padding: 0.5rem;"),
            style="margin-bottom: 1rem;"
        ),
        Div(
            P(text="Original: " + text),
            P(text="Uppercase: " + text.upper()),
            P(text="Lowercase: " + text.lower()),
            P(text="Length: " + text.length),
            P(text="Contains 'Hello': " + text.contains("Hello")),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        signals={"text": "Hello World"}
    )

def example_array_methods():
    items = Signal("items", ["Apple", "Banana"])
    new_item = Signal("new_item", "Orange")
    
    return Div(
        Div(
            Input(type="text", bind=new_item, placeholder="New item", style="padding: 0.5rem; margin-right: 0.5rem;"),
            Button("Add", data_on_click=items.append(new_item).to_js() + "; " + new_item.set("").to_js(), style="padding: 0.5rem 1rem;"),
            Button("Remove Last", data_on_click=items.pop(), style="padding: 0.5rem 1rem; margin-left: 0.5rem;"),
            Button("Clear", data_on_click=items.set([]), style="padding: 0.5rem 1rem;"),
            style="display: flex; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;"
        ),
        Div(
            P(text="Count: " + items.length),
            P(text="Items: " + items.join(", ")),
            P(text="Empty: " + (items.length == 0)),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        signals={"items": ["Apple", "Banana"], "new_item": ""}
    )

def example_math_methods():
    value = Signal("value", 7.825)
    return Div(
        Div(
            Label("Value: "),
            Input(type="number", bind=value, step="0.1", style="width: 120px; padding: 0.25rem;"),
            style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 1rem;"
        ),
        Div(
            P(text="Value: " + value),
            P(text="Rounded: " + value.round()),
            P(text="Rounded (2 decimals): " + value.round(2)),
            P(text="Absolute: " + value.abs()),
            P(text="Min with 5: " + value.min(5)),
            P(text="Max with 10: " + value.max(10)),
            P(text="Clamped (0-10): " + value.clamp(0, 10)),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        Div(
            Button("+0.5", on_click=value.add(0.5), style="padding: 0.5rem 1rem;"),
            Button("-0.5", on_click=value.sub(0.5), style="padding: 0.5rem 1rem;"),
            Button("Set to -3.14", on_click=value.set(-3.14), style="padding: 0.5rem 1rem;"),
            style="display: flex; gap: 0.5rem; margin-top: 1rem;"
        ),
        signals={"value": 7.825}
    )

def example_template_literals():
    usr = Signals(first_name="John", last_name="Doe", age_val=25)
    return Div(
        Div(
            Div(
                Label("First Name: "),
                Input(type="text", bind=usr.first_name, style="padding: 0.25rem;"),
                style="display: flex; gap: 0.5rem; align-items: center;"
            ),
            Div(
                Label("Last Name: "),
                Input(type="text", bind=usr.last_name, style="padding: 0.25rem;"),
                style="display: flex; gap: 0.5rem; align-items: center;"
            ),
            Div(
                Label("Age: "),
                Input(type="number", bind=usr.age_val, style="width: 80px; padding: 0.25rem;"),
                style="display: flex; gap: 0.5rem; align-items: center;"
            ),
            style="display: grid; gap: 0.5rem; margin-bottom: 1rem;"
        ),
        Div(
            P(text=f("Hello, {fn} {ln}!", fn=usr.first_name, ln=usr.last_name)),
            P(text=f("You are {age} years old.", age=usr.age_val)),
            P(text=f("In 10 years, you'll be {future}.", future=usr.age_val + 10)),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem;"
        ),
        signals=usr
    )

def example_property_access():
    user = Signal("user", {"name": "Alice", "age": 30, "email": "alice@example.com"})
    return Div(
        Div(
            P(text="Name: " + user.name, style="font-weight: bold;"),
            P(text="Age: " + user.age),
            P(text="Email: " + user.email),
            P(text="Is Adult (≥18): " + (user.age >= 18)),
            style="background: var(--gray-2); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;"
        ),
        Div(
            Button("Birthday", on_click=user.age.add(1), style="padding: 0.5rem 1rem;"),
            Button("Change Name to Bob", on_click=user.name.set("Bob"), style="padding: 0.5rem 1rem;"),
            style="display: flex; gap: 0.5rem;"
        ),
        signals={"user": {"name": "Alice", "age": 30, "email": "alice@example.com"}}
    )

def example_collect_classes():
    is_large = Signal("is_large", False)
    is_bold = Signal("is_bold", False)
    is_italic = Signal("is_italic", False)
    
    return Div(
        Div(
            Label(Input(type="checkbox", bind=is_large), " Large", style="margin-right: 1rem;"),
            Label(Input(type="checkbox", bind=is_bold), " Bold", style="margin-right: 1rem;"),
            Label(Input(type="checkbox", bind=is_italic), " Italic"),
            style="margin-bottom: 1rem;"
        ),
        Div(
            P(
                "Styled Text with collect()",
                data_class=collect([
                    (is_large, "large"),
                    (is_bold, "bold"),
                    (is_italic, "italic")
                ], join_with=" "),
                style="transition: all 0.3s; padding: 1rem; background: var(--gray-2); border-radius: 0.5rem;"
            ),
        ),
        Style("""
            .large { font-size: 2rem; }
            .bold { font-weight: bold; }
            .italic { font-style: italic; }
        """),
        signals={"is_large": False, "is_bold": False, "is_italic": False}
    )

def example_dynamic_classes():
    styles = Signals(cls_large=False, cls_bold=False, cls_italic=False, cls_blue=False)

    return Div(
        Div(
            Label(Input(type="checkbox", bind=styles.cls_large), " Large", style="margin-right: 1rem;"),
            Label(Input(type="checkbox", bind=styles.cls_bold), " Bold", style="margin-right: 1rem;"),
            Label(Input(type="checkbox", bind=styles.cls_italic), " Italic", style="margin-right: 1rem;"),
            Label(Input(type="checkbox", bind=styles.cls_blue), " Blue"),
            style="margin-bottom: 1rem;"
        ),
        Div(
            P(
                "Styled Text with classes()",
                data_class=classes(large=styles.cls_large, bold=styles.cls_bold, italic=styles.cls_italic, blue=styles.cls_blue),
                style="transition: all 0.3s; padding: 1rem; background: var(--gray-2); border-radius: 0.5rem;"
            ),
        ),
        Style("""
            .large { font-size: 2rem; }
            .bold { font-weight: bold; }
            .italic { font-style: italic; }
            .blue { color: var(--blue-9); }
        """),
        signals=styles,
    )

def example_form_validation():
    form_name = Signal("form_name", "")
    form_email = Signal("form_email", "")
    form_age = Signal("form_age", 0)
    form_agree = Signal("form_agree", False)

    name_valid = form_name.length >= 3
    email_valid = form_email.contains("@")
    age_valid = form_age >= 18
    can_submit = all_cond(name_valid, email_valid, age_valid, form_agree)

    return Div(
        Div(
            Div(
                Label("Name:", style="display: block; margin-bottom: 0.25rem;"),
                Input(type="text", bind=form_name, placeholder="Min 3 chars", style="width: 100%; padding: 0.5rem; margin-bottom: 0.25rem;"),
                P("✓ Valid", data_show=name_valid, style="color: green; margin: 0;"),
                P("✗ Too short", data_show=~name_valid, style="color: red; margin: 0;"),
                style="margin-bottom: 1rem;"
            ),
            Div(
                Label("Email:", style="display: block; margin-bottom: 0.25rem;"),
                Input(type="email", bind=form_email, placeholder="your@email.com", style="width: 100%; padding: 0.5rem; margin-bottom: 0.25rem;"),
                P("✓ Valid", data_show=email_valid, style="color: green; margin: 0;"),
                P("✗ Invalid", data_show=~email_valid, style="color: red; margin: 0;"),
                style="margin-bottom: 1rem;"
            ),
            Div(
                Label("Age:", style="display: block; margin-bottom: 0.25rem;"),
                Input(type="number", bind=form_age, placeholder="18+", style="width: 100%; padding: 0.5rem; margin-bottom: 0.25rem;"),
                P("✓ Valid", data_show=age_valid, style="color: green; margin: 0;"),
                P("✗ Must be 18+", data_show=~age_valid, style="color: red; margin: 0;"),
                style="margin-bottom: 1rem;"
            ),
            Div(
                Label(Input(type="checkbox", bind=form_agree), " I agree to terms"),
                style="margin-bottom: 1rem;"
            ),
        ),
        Div(
            Button(
                "Submit",
                data_disabled=~can_submit,
                data_attr_style=if_(can_submit, "opacity: 1; cursor: pointer;", "opacity: 0.5; cursor: not-allowed;"),
                style="padding: 0.5rem 1.5rem; background: var(--blue-6); color: white; border: none; border-radius: 0.25rem;"
            ),
            P(text=f("✓ Welcome, {name}!", name=form_name), data_show=can_submit, style="color: green; margin-left: 1rem;"),
            style="display: flex; align-items: center;"
        ),
        signals={"form_name": "", "form_email": "", "form_age": 0, "form_agree": False}
    )

@router.get("/xtras/rustytags")
@page(title="RustyTags Datastar SDK", wrap_in=HTMLResponse)
def rustytags_docs():
    return Main(
        H1("RustyTags Datastar SDK"),
        P("The RustyTags Datastar SDK provides a powerful, type-safe reactive system with Python operator overloading for building dynamic web interfaces."),
        
        Section("What is RustyTags?",
            P("RustyTags is a high-performance HTML generation library that combines Rust-powered performance with modern Python web development. The Datastar SDK adds reactive capabilities through type-safe Signals."),
            Ul(
                Li("🦀 Rust-powered HTML generation (3-10x faster than pure Python)"),
                Li("⚛️ Type-safe Signal system with Python operator overloading"),
                Li("📊 Reactive expressions that compile to JavaScript"),
                Li("🔧 Framework-agnostic and minimal dependencies"),
            ),
        ),

        Section("Basic Counter Demo",
            P("Signals provide reactive state management with methods like ", Code(".add()"), ", ", Code(".sub()"), ", and ", Code(".set()"), ":"),
            ComponentShowcase(example_basic_counter),
        ),

        Section("Arithmetic Operators Demo",
            P("Python operators work directly on Signals and generate JavaScript expressions:"),
            ComponentShowcase(example_arithmetic),
        ),

        Section("Conditional Expressions Demo",
            P("Use ", Code("if_()"), " for ternary expressions and conditional logic:"),
            ComponentShowcase(example_conditional),
        ),

        Section("Pattern Matching Demo",
            P("The ", Code("match()"), " function provides clean pattern matching similar to Python's match/case:"),
            ComponentShowcase(example_pattern_matching),
        ),

        Section("String Methods Demo",
            P("Work with text using string manipulation methods like ", Code(".upper()"), ", ", Code(".lower()"), ", ", Code(".contains()"), ", and ", Code(".length"), ":"),
            ComponentShowcase(example_string_methods),
        ),

        Section("Array Methods Demo",
            P("Manipulate lists with ", Code(".append()"), ", ", Code(".pop()"), ", ", Code(".join()"), ", and ", Code(".length"), ":"),
            ComponentShowcase(example_array_methods),
        ),

        Section("Math Methods Demo",
            P("Mathematical operations like ", Code(".round()"), ", ", Code(".abs()"), ", ", Code(".min()"), ", ", Code(".max()"), ", and ", Code(".clamp()"), ":"),
            ComponentShowcase(example_math_methods),
        ),

        Section("Template Literals Demo",
            P("Use ", Code("f()"), " for JavaScript template literals with embedded expressions:"),
            ComponentShowcase(example_template_literals),
        ),

        Section("Property Access Demo",
            P("Access nested object properties naturally with Python syntax:"),
            ComponentShowcase(example_property_access),
        ),

        # Section("Dynamic Classes with collect() Demo",
        #     P("Use ", Code("collect()"), " to conditionally join CSS classes as a string:"),
        #     ComponentShowcase(example_collect_classes),
        # ),

        Section("Dynamic Classes with classes() Demo",
            P("Use ", Code("classes()"), " for Datastar's ", Code("data-class"), " object literal format:"),
            ComponentShowcase(example_dynamic_classes),
        ),

        Section("Form Validation Demo",
            P("Combine ", Code("all()"), " and ", Code("any()"), " for complex validation logic:"),
            ComponentShowcase(example_form_validation),
        ),

        Section("API Reference",
            CodeBlock("""
from nitro.datastar import Signal, Signals, if_, match, collect, classes
from nitro.datastar import all, any, f
from nitro.datastar import post, get, put, patch, delete

# Create signals
sigs = Signals(counter=0, name="John", active=True)
sig = Signal("score", 75)

# Signal methods
sig.add(5)      # Increment
sig.sub(3)      # Decrement
sig.set(100)    # Set value
sig.toggle()    # Toggle boolean

# Operators
sig + 5         # Addition
sig - 3         # Subtraction
sig * 2         # Multiplication
sig / 4         # Division
sig % 3         # Modulo
sig >= 60       # Comparison
~sig            # Logical NOT
sig & other     # Logical AND
sig | other     # Logical OR

# String methods
text.upper()           # Uppercase
text.lower()           # Lowercase
text.contains("@")     # String includes
text.length            # String length

# Array methods
items.append(val)      # Add to array
items.pop()            # Remove last
items.join(", ")       # Join array
items.length           # Array length

# Conditionals
if_(score >= 90, "A", "B")                    # Ternary
match(status, idle="Ready", loading="Wait")   # Pattern match

# Templates
f("Hello, {name}!", name=sig)                 # Template literal

# Dynamic classes
collect([(large, "lg"), (bold, "b")])         # Join classes
classes(large=is_large, bold=is_bold)         # Object literal

# Validation
all(valid1, valid2, valid3)                   # All true
any(valid1, valid2, valid3)                   # Any true

# HTTP actions
post("/api/users", name=name, email=email)    # POST request
get("/api/data")                              # GET request
""", code_cls="language-python")
        ),

        Section("Key Features",
            Ul(
                Li(Strong("Type-Safe Signals: "), "Signal and Signals classes with automatic type inference"),
                Li(Strong("Python Operators: "), "Full operator overloading (+, -, *, /, %, ==, !=, <, >, <=, >=, &, |, ~)"),
                Li(Strong("Signal Methods: "), ".add(), .sub(), .set(), .toggle(), .append(), .pop()"),
                Li(Strong("String Methods: "), ".upper(), .lower(), .contains(), .length"),
                Li(Strong("Math Methods: "), ".round(), .abs(), .min(), .max(), .clamp()"),
                Li(Strong("Array Methods: "), ".append(), .pop(), .join(), .slice(), .length"),
                Li(Strong("Conditionals: "), "if_() for ternary, match() for pattern matching"),
                Li(Strong("Templates: "), "f() for JavaScript template literals"),
                Li(Strong("Dynamic Classes: "), "collect() for joining, classes() for object literals"),
                Li(Strong("Validation: "), "all() and any() for logical aggregation"),
                Li(Strong("HTTP Actions: "), "get(), post(), put(), patch(), delete()"),
            ),
        ),

        BackLink(),
        
        signals=Signals(message=""),
    )

