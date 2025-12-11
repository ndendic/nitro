"""Interactive Python code playground for executing code examples"""

import sys
import io
import json
import asyncio
import traceback
from contextlib import redirect_stdout, redirect_stderr
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse

from rusty_tags import Div, H1, H2, Textarea, Button, Pre, Code
from nitro.infrastructure.html import Page
from pages.templates.base import hdrs, htmlkws, bodykws, ftrs
from nitro.infrastructure.html.datastar import Signals, get

router = APIRouter()

# Default code template
DEFAULT_CODE = '''# Python Playground
# Write your Python code here and click "Run" to execute it

print("Hello from the Nitro Playground!")

# Try some examples:
for i in range(3):
    print(f"Count: {i}")
'''


@router.get("/playground/code", response_class=HTMLResponse)
def code_playground():
    """Display the interactive code playground"""

    page = Page(
        Div(
            H1("Python Code Playground", cls="text-4xl font-bold mb-4"),
            H2("Interactive Python Execution", cls="text-xl text-muted-foreground mb-8"),

            # Code editor area
            Div(
                Div(
                    Div("Code Editor", cls="text-sm font-medium mb-2"),
                    Textarea(
                        DEFAULT_CODE,
                        id="code-editor",
                        data_bind="code",
                        rows="15",
                        cls="w-full font-mono text-sm p-4 bg-muted rounded border",
                        placeholder="Write your Python code here..."
                    ),
                    cls="mb-4"
                ),

                # Control buttons
                Div(
                    Button(
                        "▶ Run Code",
                        data_on_click="$$get('/playground/execute?code=' + encodeURIComponent($code))",
                        cls="btn btn-primary",
                        id="run-button"
                    ),
                    Button(
                        "Clear Output",
                        data_on_click="$output = ''; $error = ''",
                        cls="btn"
                    ),
                    cls="flex gap-2 mb-6"
                ),

                # Output area
                Div(
                    Div("Output", cls="text-sm font-medium mb-2"),
                    Pre(
                        Code(
                            data_text="$output || 'No output yet. Click \"Run Code\" to execute.'",
                            cls="text-sm"
                        ),
                        id="output-console",
                        cls="bg-muted p-4 rounded border min-h-[200px] max-h-[400px] overflow-auto"
                    ),
                    cls="mb-4"
                ),

                # Error area
                Div(
                    Div("Errors", cls="text-sm font-medium mb-2"),
                    Pre(
                        Code(
                            data_text="$error || 'No errors'",
                            cls="text-sm text-red-500"
                        ),
                        id="error-console",
                        cls="bg-muted p-4 rounded border min-h-[100px] overflow-auto",
                        data_show="$error"
                    ),
                    data_show="$error",
                    cls="mb-4"
                ),

                cls="max-w-6xl mx-auto"
            ),

            cls="p-8",
            signals=Signals(code=DEFAULT_CODE, output="", error="")
        ),
        title="Code Playground - Nitro Documentation",
        datastar=True,
        highlightjs=True,
        tailwind4=True,
        lucide=True,
        hdrs=hdrs,
        htmlkw=htmlkws,
        bodykw=bodykws,
        ftrs=ftrs,
    )

    return str(page)


@router.get("/playground/execute")
async def execute_code(code: str = ""):
    """Execute Python code and return the output via SSE"""

    async def generate_output():
        """Generator that yields execution results as SSE events"""

        if not code or not code.strip():
            yield {
                "event": "output",
                "data": "Error: No code provided"
            }
            return

        # Create string buffers to capture output
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        try:
            # Check if code contains async functions
            is_async = 'async def' in code or 'await ' in code

            # Redirect stdout and stderr
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                if is_async:
                    # Execute async code
                    try:
                        # Create a new event loop for execution
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        # Compile and execute the code
                        compiled = compile(code, '<playground>', 'exec')
                        exec_globals = {
                            '__name__': '__main__',
                            'asyncio': asyncio,
                        }
                        exec(compiled, exec_globals)

                        # If there's a main() coroutine, run it
                        if 'main' in exec_globals and asyncio.iscoroutinefunction(exec_globals['main']):
                            loop.run_until_complete(exec_globals['main']())

                        loop.close()
                    except Exception as e:
                        stderr_buffer.write(f"Async execution error: {str(e)}\n")
                        stderr_buffer.write(traceback.format_exc())
                else:
                    # Execute synchronous code
                    exec_globals = {'__name__': '__main__'}
                    exec(code, exec_globals)

            # Get output
            stdout_output = stdout_buffer.getvalue()
            stderr_output = stderr_buffer.getvalue()

            # Send output
            if stdout_output:
                yield {
                    "event": "datastar-signal",
                    "data": json.dumps({"output": stdout_output})
                }

            # Send errors if any
            if stderr_output:
                yield {
                    "event": "datastar-signal",
                    "data": json.dumps({"error": stderr_output})
                }
            elif not stdout_output:
                # Code executed successfully but produced no output
                yield {
                    "event": "datastar-signal",
                    "data": json.dumps({"output": "Code executed successfully (no output)"})
                }

        except SyntaxError as e:
            error_msg = f"Syntax Error on line {e.lineno}: {e.msg}\n{e.text}"
            yield {
                "event": "datastar-signal",
                "data": json.dumps({"error": error_msg})
            }

        except Exception as e:
            error_msg = f"Execution Error: {str(e)}\n{traceback.format_exc()}"
            yield {
                "event": "datastar-signal",
                "data": json.dumps({"error": error_msg})
            }

    return EventSourceResponse(generate_output())
