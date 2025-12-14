from datastar_py.fastapi import ReadSignals, datastar_response
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from nitro import Client, event, Signals

from pages.accordion import router as accordion_router
from pages.alert import router as alert_router
from pages.anchor import router as anchor_router
from pages.badge import router as badge_router
from pages.button import router as button_router
from pages.card import router as card_router
from pages.codeblock import router as codeblock_router
from pages.code_playground import router as code_playground_router
from pages.dialog import router as dialog_router
from pages.docs import router as docs_router
from pages.index import router as index_router
from pages.kbd import router as kbd_router
from pages.label import router as label_router
from pages.playground import router as playground_router
from pages.rustytags import router as rustytags_router
from pages.tabs import router as tabs_router
from pages.test_signals import router as test_signals_router
from pages.spinner import router as spinner_router
from pages.skeleton import router as skeleton_router
from pages.checkbox import router as checkbox_router
from pages.radio import router as radio_router
from pages.switch import router as switch_router
from pages.select import router as select_router
from pages.textarea import router as textarea_router
from pages.field import router as field_router
from pages.input_group import router as input_group_router
from pages.dropdown import router as dropdown_router
from pages.popover import router as popover_router
from pages.tooltip import router as tooltip_router
from pages.alert_dialog import router as alert_dialog_router
from pages.toast import router as toast_router
from pages.progress import router as progress_router
from pages.breadcrumb import router as breadcrumb_router
from pages.pagination import router as pagination_router
from pages.avatar import router as avatar_router
from pages.table import router as table_router

app: FastAPI = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(index_router)
app.include_router(docs_router)
app.include_router(accordion_router)
app.include_router(alert_router)
app.include_router(anchor_router)
app.include_router(badge_router)
app.include_router(button_router)
app.include_router(card_router)
app.include_router(codeblock_router)
app.include_router(code_playground_router)
app.include_router(dialog_router)
app.include_router(kbd_router)
app.include_router(label_router)
app.include_router(playground_router)
app.include_router(rustytags_router)
app.include_router(tabs_router)
app.include_router(test_signals_router)
app.include_router(spinner_router)
app.include_router(skeleton_router)
app.include_router(checkbox_router)
app.include_router(radio_router)
app.include_router(switch_router)
app.include_router(select_router)
app.include_router(textarea_router)
app.include_router(field_router)
app.include_router(input_group_router)
app.include_router(dropdown_router)
app.include_router(popover_router)
app.include_router(tooltip_router)
app.include_router(alert_dialog_router)
app.include_router(toast_router)
app.include_router(progress_router)
app.include_router(breadcrumb_router)
app.include_router(pagination_router)
app.include_router(avatar_router)
app.include_router(table_router)


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
