"""Tabs component documentation page"""

import pathlib
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter
from fastapi import Request
from nitro.domain import Entity
from nitro.infrastructure.html.datastar import Signals, get, ElementPatchMode
from nitro.utils import AttrDict
from nitro.infrastructure.events import on, emit_elements, emit_signals
from nitro.infrastructure.html.components import LucideIcon
from .templates.base import *  # noqa: F403

from mistletoe.html_renderer import HTMLRenderer
from mistletoe.span_token import Image
import mistletoe
from functools import partial
from lxml import html, etree

router: APIRouter = APIRouter()


class Person(Entity, table=True):
    name: str
    age: int

    @property
    def signals(self) -> Signals:
        return Signals(**self.model_dump())

    def __html__(self):
        print(self.model_dump())
        return Div(
            H2(text=self.signals.name, cls="text-lg font-bold"),
            Div(
                P(text="Name: " + self.signals.name),
                P(text="Age: " + self.signals.age),
                cls="grid gap-2 text-sm text-muted-foreground",
            ),
            signals=self.signals,
            cls="card p-4",
        )

    @classmethod
    def table(
        cls, search_value: Optional[str] = None, age: Optional[int] = None
    ) -> HtmlString:
        records: List[Person] = []
        expressions = []
        if search_value:
            expressions.append(cls.name.ilike(f"%{search_value}%"))
        if age:
            expressions.append(cls.age >= age)
        if expressions:
            records = cls.where(*expressions, order_by=cls.age.desc())
        else:
            records = cls.all()

        return Div(
            # Div(
            #     Input(type="text", bind="search", placeholder="Search...", on_keydown__debounce_400ms=f"{get("/cmds/search/nikola")}", cls="input"),
            #     Input(type="number", bind="age", placeholder="5", on_change=f"{get("/cmds/search/nikola")}", cls="input"),
            #     cls="grid grid-cols-2 gap-2",
            # ),
            Table(
                Caption("People"),
                Thead(
                    Th("Name"),
                    Th("Age"),
                    Th("Actions", cls="text-right"),
                    cls="text-bold",
                ),
                Tbody(
                    *[
                        Tr(
                            Td(person.name),
                            Td(person.age),
                            Td(
                                Button(
                                    LucideIcon("trash-2"),
                                    on_click=f"@get('/cmds/deletePerson/{person.id}')",
                                    cls="btn-icon-destructive",
                                ),
                                cls="text-right",
                            ),
                        )
                        for person in records
                    ],
                ),
                cls="table",
            ),
            cls="overflow-x-auto",
            id="people-table",
        )

    def form(self):
        return Div(
            Div(
                Label("Name:"),
                Input(type="text", bind=self.signals.name, cls="input"),
                cls="grid gap-2",
            ),
            Div(
                Label("Age:"),
                Input(type="number", bind=self.signals.age, cls="input"),
                cls="grid gap-2",
            ),
            Button("Add +", on_click="@get('/cmds/newPerson/nikola')", variant="outline"),
            cls="card p-4 grid gap-6",
        )


nik = Person(id="1", name="John Doe", age=25)







nitro_class_map = {
    "h1": "h1",
    "h2": "h2",
    "h3": "h3",
    "h4": "h4",
    # Body text and links
    "p": "text-lg leading-relaxed mb-6",
    "a": "link text-primary hover:text-primary-focus underline",
    # Lists with proper spacing
    "ul": "list list-bullet space-y-2 mb-6 ml-6 text-lg",
    "ol": "list list-decimal space-y-2 mb-6 ml-6 text-lg",
    "li": "leading-relaxed",
    # Code and quotes
    "pre": "bg-base-200 rounded-lg p-4 mb-6",
    "code": "codespan px-1",
    "pre code": "codespan px-1 block overflow-x-auto",
    "blockquote": "blockquote pl-4 border-l-4 border-primary italic mb-6",
    # Tables
    "table": "table table-divider table-hover table-small w-full mb-6",
    "th": "!text-left p-2 font-semibold",
    "td": "p-2",
    # Other elements
    "hr": "divider-icon my-8",
    "img": "max-w-full h-auto rounded-lg mb-6",
}


def apply_classes(
    html_str: str,  # Html string
    class_map=None,  # Class map
    class_map_mods=None,  # Class map that will modify the class map map (for small changes to base map)
) -> str:  # Html string with classes applied
    "Apply classes to html string"
    if not html_str:
        return html_str
    # Handles "Unicode strings with encoding declaration are not supported":
    if html_str[:100].lstrip().startswith("<?xml"):
        html_str = html_str.split("?>", 1)[1].strip()
    class_map = class_map or nitro_class_map
    if class_map_mods:
        class_map = {**class_map, **class_map_mods}
    try:
        html_str = html.fragment_fromstring(html_str, create_parent=True)
        for selector, classes in class_map.items():
            # Handle descendant selectors (e.g., 'pre code')
            xpath = "//" + "/descendant::".join(selector.split())
            for element in html_str.xpath(xpath):
                existing_class = element.get("class", "")
                new_class = f"{existing_class} {classes}".strip()
                element.set("class", new_class)
        return "".join(
            etree.tostring(c, encoding="unicode", method="html") for c in html_str
        )
    except (etree.ParserError, ValueError):
        return html_str


class NitroRenderer(HTMLRenderer):
    "Custom renderer for Nitro UI that handles image paths"

    def __init__(self, *args, img_dir=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.img_dir = img_dir

    def render_image(self, token):
        "Modify image paths if they're relative and self.img_dir is specified"
        template = '<img src="{}" alt="{}"{} class="max-w-full h-auto rounded-lg mb-6">'
        title = f' title="{token.title}"' if hasattr(token, "title") else ""
        src = token.src
        if self.img_dir and not src.startswith(
            ("http://", "https://", "/", "attachment:", "blob:", "data:")
        ):
            src = f"{pathlib.Path(self.img_dir)}/{src}"
        return template.format(
            src, token.children[0].content if token.children else "", title
        )


def render_md(
    md_content: str,  # Markdown content
    class_map=None,  # Class map
    class_map_mods=None,  # Additional class map
    img_dir: str = None,  # Directory containing images
    renderer=NitroRenderer,  # custom renderer
) -> HtmlString:  # Rendered markdown
    "Renders markdown using mistletoe and lxml with custom image handling"
    if md_content == "":
        return md_content
    html_content = mistletoe.markdown(md_content, partial(renderer, img_dir=img_dir))
    return apply_classes(html_content, class_map, class_map_mods)








@router.get("/playground")
@template(title="Playground")
def playground():
    state = Signals(btn_open=False, anchor_open=False, name="")
    return Div(
        H1("Playground", style="animation: var(--animation-fade-in) forwards;"),
        Div(
#             render_md(
# """
# # Hello World
# This is a test of the markdown **renderer**. It supports **bold**, *italic*, and [links](https://www.google.com).
# """),
            nik,
            nik.form(),
            Div(
                Input(
                    type="text",
                    bind="search",
                    placeholder="Search...",
                    on_keydown__debounce_400ms=f"@get('/cmds/search/nikola')",
                    cls="input",
                ),
                Input(
                    type="number",
                    bind="age",
                    placeholder="5",
                    on_change="@get('/cmds/search/nikola')",
                    cls="input",
                ),
                cls="grid grid-cols-2 gap-2",
            ),
            nik.table(),
            Div(
                Input(
                    type="text",
                    bind="message",
                    placeholder="Message with 2 second debounce...",
                    on_keydown__debounce_2s="@get('/cmds/message/nik')",
                    cls="input",
                ),
            ),
            cls="grid gap-4",
        ),
        Div(id="results"),
        Div(id="updates"),
        signals=state,
        data_persist="age,name",
    )

@on("newPerson")
async def new_person(sender, request: Request, signals: Signals):
    signals: AttrDict = AttrDict(**signals)
    new_person = Person(id=str(uuid4()), name=signals.name, age=signals.age)
    new_person.save()
    notification = Div(
        f"{new_person.name}, {new_person.age} was saved.",
        cls="text-green-500 mt-4",
        id="results",
    )
    yield emit_elements(notification, topic="updates.newPerson")
    yield emit_elements(Person.table(), topic="updates.newPerson")


@on("search")
async def search(sender, request: Request, signals: Signals):
    search_value = signals["search"]
    age = signals["age"]
    yield emit_elements(
        Person.table(search_value=search_value, age=age), topic="updates.person.search"
    )


@on("deletePerson")
async def delete_person(sender, request: Request, signals: Signals):
    signals: AttrDict = AttrDict(**signals)
    person = Person.find(sender)
    if person:
        person.delete()
        notification = Div(
            f"{person.name} was deleted.", cls="text-red-500 mt-4", id="results"
        )
        yield emit_elements(notification, topic="updates.deletePerson")
        yield emit_elements(Person.table(), topic="updates.deletePerson")


@on("message")
def notify(sender, request: Request, signals: Signals):
    message = signals["message"] or "No message provided"
    yield emit_elements(
        Div(f"Server processed message: {message}", cls="text-lg text-bold mt-4 mt-2"),
        selector="#updates",
        mode=ElementPatchMode.APPEND,
        topic="updates.person.message",
    )
    yield emit_signals({"message": ""}, topic="updates.person.message")
    yield Div(f"Server notification: {message}")
