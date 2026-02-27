"""Boost main.py templates for each supported framework."""

SANIC_MAIN_TEMPLATE = '''\
from sanic import Sanic
from base import index

app = Sanic("NitroApp")
app.static("/static", "./static")


@app.route("/")
async def home(request):
    return index()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True, auto_reload=True)
'''

FASTAPI_MAIN_TEMPLATE = '''\
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from base import index

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def home():
    return index()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''

FRAMEWORK_MAIN_TEMPLATES = {
    "sanic": SANIC_MAIN_TEMPLATE,
    "fastapi": FASTAPI_MAIN_TEMPLATE,
}


def generate_boost_main(framework: str) -> str:
    """Generate the main.py template content for the chosen framework."""
    return FRAMEWORK_MAIN_TEMPLATES[framework]
