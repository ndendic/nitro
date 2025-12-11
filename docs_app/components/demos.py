"""
Demo components for interactive documentation.

These components showcase Nitro's capabilities with live, interactive examples.
"""

from rusty_tags import Div, Button, P, H3, Span, Code
from rusty_tags.datastar import Signals


def ButtonDemo():
    """
    Interactive button demo showing different variants and states.
    """
    sigs = Signals(button_clicks=0)

    return Div(
        H3("Button Component Demo", cls="text-lg font-semibold mb-4"),
        P("Click the button to see it in action:", cls="mb-4 text-gray-600 dark:text-gray-400"),

        # Demo buttons
        Div(
            Button(
                "Click Me!",
                data_on_click=sigs.button_clicks.add(1),
                cls="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            ),
            P(
                "Button clicked: ",
                Span(
                    sigs.button_clicks.text(),
                    cls="font-bold text-blue-600 dark:text-blue-400"
                ),
                " times",
                cls="mt-4 text-sm"
            ),
            cls="space-y-4"
        ),

        # Code example
        Div(
            P("Code example:", cls="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 mt-6"),
            Div(
                Code(
                    'Button("Click Me!", cls="bg-blue-600 text-white rounded-md")',
                    cls="language-python"
                ),
                cls="bg-gray-100 dark:bg-gray-800 rounded p-3 text-sm"
            ),
            cls="mt-4"
        ),

        cls="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-800",
        signals=sigs
    )


def DialogDemo():
    """
    Interactive dialog demo showing modal functionality.
    """
    from nitro.infrastructure.html.components.dialog import (
        Dialog, DialogTrigger, DialogContent, DialogHeader,
        DialogTitle, DialogBody, DialogFooter, DialogClose
    )

    dialog_id = "demo-dialog"

    return Div(
        H3("Dialog Component Demo", cls="text-lg font-semibold mb-4"),
        P("Click the button to open a modal dialog:", cls="mb-4 text-gray-600 dark:text-gray-400"),

        # Trigger button
        DialogTrigger(
            "Open Dialog",
            dialog_id=dialog_id,
            cls="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        ),

        # Dialog component
        Dialog(
            DialogContent(
                DialogHeader(
                    DialogTitle("Example Dialog", cls="text-xl font-bold")
                ),
                DialogBody(
                    P(
                        "This is an example dialog built with Nitro components. "
                        "It demonstrates modal functionality with backdrop, ESC key support, and accessible markup.",
                        cls="text-gray-600 dark:text-gray-400"
                    ),
                    cls="mt-4"
                ),
                DialogFooter(
                    DialogClose(
                        "Close",
                        dialog_id=dialog_id,
                        cls="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    ),
                    cls="mt-6 flex justify-end"
                ),
                cls="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-md"
            ),
            id=dialog_id,
            cls="backdrop:bg-black backdrop:bg-opacity-50"
        ),

        # Code example
        Div(
            P("Code example:", cls="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 mt-6"),
            Div(
                Code(
                    'Dialog(\n'
                    '    DialogContent(...),\n'
                    '    id="my-dialog"\n'
                    ')',
                    cls="language-python"
                ),
                cls="bg-gray-100 dark:bg-gray-800 rounded p-3 text-sm"
            ),
            cls="mt-4"
        ),

        cls="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-800"
    )


def CodeBlockDemo():
    """
    Interactive code block demo showing syntax highlighting.
    """
    from nitro.infrastructure.html.components.codeblock import CodeBlock

    example_code = """def hello_world():
    print("Hello, World!")
    return True"""

    return Div(
        H3("CodeBlock Component Demo", cls="text-lg font-semibold mb-4"),
        P("Code blocks with syntax highlighting:", cls="mb-4 text-gray-600 dark:text-gray-400"),

        # Demo code block
        CodeBlock(
            example_code,
            code_cls="language-python",
            cls="mb-4"
        ),

        # Code example
        Div(
            P("Code example:", cls="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 mt-6"),
            Div(
                Code(
                    'CodeBlock(\n'
                    '    "def hello(): pass",\n'
                    '    code_cls="language-python"\n'
                    ')',
                    cls="language-python"
                ),
                cls="bg-gray-100 dark:bg-gray-800 rounded p-3 text-sm"
            ),
            cls="mt-4"
        ),

        cls="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-800"
    )


def UnknownDemo(component_name: str):
    """
    Error message for unknown demo components.

    Args:
        component_name: Name of the component that wasn't found
    """
    return Div(
        H3("Component Not Found", cls="text-lg font-semibold mb-2 text-red-600 dark:text-red-400"),
        P(
            f"The demo component '{component_name}' does not exist. "
            "Available demos: button, dialog, codeblock",
            cls="text-gray-600 dark:text-gray-400"
        ),
        cls="border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 rounded-lg p-6"
    )


# Registry of available demo components
DEMO_COMPONENTS = {
    'button': ButtonDemo,
    'dialog': DialogDemo,
    'codeblock': CodeBlockDemo,
}


def get_demo(component_name: str):
    """
    Get a demo component by name.

    Args:
        component_name: Name of the demo component (e.g., 'button', 'dialog')

    Returns:
        Demo component function or UnknownDemo if not found
    """
    if component_name in DEMO_COMPONENTS:
        return DEMO_COMPONENTS[component_name]()
    else:
        return UnknownDemo(component_name)
