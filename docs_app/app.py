from datastar_py.fastapi import ReadSignals, datastar_response
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from nitro import Client, event, Signals

from .routes import all_routes

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

for route in all_routes:
    app.include_router(route)

# Exception handlers for custom error pages
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom error pages."""
    if exc.status_code == 404:
        return RedirectResponse(url="/404", status_code=302)
    elif exc.status_code == 500:
        return RedirectResponse(url="/500", status_code=302)
    # For other errors, return JSON response
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with custom 500 page."""
    import traceback
    traceback.print_exc()
    return RedirectResponse(url="/500", status_code=302)


@app.get("/cmds/{command}/{sender}")
async def commands(command: str, sender: str, request: Request, signals: ReadSignals):
    sig: Signals = Signals(**signals) if signals else {}
    results = await event(command).emit_async(sender, signals=sig, request=request)
    print(results)


@app.get("/updates")
@datastar_response
async def event_stream(request: Request, signals: ReadSignals):
    """SSE endpoint with automatic client management"""
    with Client(topics=["updates*"]) as client:
        async for update in client.stream():
            yield update


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
