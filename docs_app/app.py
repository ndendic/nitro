from datastar_py.fastapi import ReadSignals, datastar_response
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from nitro import Client, event, Signals

from pages.accordion import router as accordion_router
from pages.anchor import router as anchor_router
from pages.codeblock import router as codeblock_router
from pages.dialog import router as dialog_router
from pages.docs import router as docs_router
from pages.index import router as index_router
from pages.playground import router as playground_router
from pages.rustytags import router as rustytags_router
from pages.tabs import router as tabs_router

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(index_router)
app.include_router(docs_router)
app.include_router(accordion_router)
app.include_router(anchor_router)
app.include_router(codeblock_router)
app.include_router(dialog_router)
app.include_router(playground_router)
app.include_router(rustytags_router)
app.include_router(tabs_router)


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

    uvicorn.run("app:app", host="0.0.0.0", port=8800, reload=True)
