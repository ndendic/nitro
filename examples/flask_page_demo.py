"""
Flask + Nitro Page() Integration Demo

This example demonstrates:
1. Using Nitro's Page() component with Flask
2. Rendering Page to HTML string
3. Returning from Flask routes
4. Tailwind CSS integration

Run: python examples/flask_page_demo.py
Then visit: http://localhost:5004
"""

import sys
from pathlib import Path

# Add the local nitro package to the path (for development)
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from flask import Flask
from rusty_tags import Div, H1, H2, P, Button, Ul, Li, A, Br
from nitro.infrastructure.html import Page


# Initialize Flask app
app = Flask(__name__)


@app.route("/")
def homepage():
    """Homepage demonstrating Page() integration."""
    page = Page(
        Div(
            H1("Flask + Nitro Page() Demo", class_="text-4xl font-bold text-green-600 mb-4"),
            H2("HTML Generation with RustyTags", class_="text-2xl mb-6"),

            P(
                "This page is generated using Nitro's Page() component with RustyTags HTML generation.",
                class_="text-lg mb-4"
            ),

            Div(
                H2("Features:", class_="text-xl font-bold mb-2"),
                Ul(
                    Li("✓ RustyTags HTML generation (3-10x faster than pure Python)"),
                    Li("✓ Tailwind CSS integration via CDN"),
                    Li("✓ Clean, declarative syntax"),
                    Li("✓ Type-safe HTML elements"),
                    Li("✓ No template files needed"),
                    class_="list-disc list-inside space-y-2 mb-6"
                ),
                class_="mb-6"
            ),

            Div(
                H2("Try these routes:", class_="text-xl font-bold mb-2"),
                Ul(
                    Li(A("Homepage", href="/", class_="text-blue-500 hover:underline")),
                    Li(A("About Page", href="/about", class_="text-blue-500 hover:underline")),
                    Li(A("Contact Page", href="/contact", class_="text-blue-500 hover:underline")),
                    class_="list-disc list-inside space-y-2 mb-6"
                ),
                class_="mb-6"
            ),

            class_="container mx-auto p-8 max-w-2xl"
        ),
        title="Flask + Nitro Page() Demo",
        tailwind4=True
    )

    # Convert Page to string and return
    return str(page)


@app.route("/about")
def about():
    """About page."""
    page = Page(
        Div(
            H1("About", class_="text-4xl font-bold text-green-600 mb-4"),

            P(
                "Nitro is a set of abstraction layers for building Python web applications.",
                class_="text-lg mb-4"
            ),

            P(
                "It works on top of any Python web framework (Flask, FastAPI, Django, etc.) and provides the following features:",
                class_="text-lg mb-4"
            ),

            Ul(
                Li("Rich domain entities with Active Record pattern"),
                Li("Hybrid persistence (SQL, Memory, Redis, etc.)"),
                Li("Event-driven architecture with Blinker"),
                Li("High-performance HTML generation with RustyTags"),
                Li("Reactive UI with Datastar SDK"),
                Li("Tailwind CSS CLI for building modern web interfaces"),
                class_="list-disc list-inside space-y-2 mb-6"
            ),

            Br(),
            A("← Back to Home", href="/", class_="text-blue-500 hover:underline"),

            class_="container mx-auto p-8 max-w-2xl"
        ),
        title="About - Flask + Nitro",
        tailwind4=True
    )

    return str(page)


@app.route("/contact")
def contact():
    """Contact page."""
    page = Page(
        Div(
            H1("Contact", class_="text-4xl font-bold text-green-600 mb-4"),

            P(
                "Get in touch with the Nitro team:",
                class_="text-lg mb-4"
            ),

            Div(
                P("Email: nitro@example.com", class_="mb-2"),
                P("GitHub: github.com/your-org/nitro", class_="mb-2"),
                P("Docs: nitro-framework.dev", class_="mb-2"),
                class_="mb-6"
            ),

            Button(
                "Send Message",
                class_="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded mb-6"
            ),

            Br(),
            A("← Back to Home", href="/", class_="text-blue-500 hover:underline"),

            class_="container mx-auto p-8 max-w-2xl"
        ),
        title="Contact - Flask + Nitro",
        tailwind4=True
    )

    return str(page)


if __name__ == "__main__":
    print("✓ Flask + Nitro Page() Demo started")
    print("✓ Visit: http://localhost:5004")
    app.run(host="0.0.0.0", port=5004, debug=False)
