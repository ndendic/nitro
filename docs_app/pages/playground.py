"""Tabs component documentation page"""

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


@router.get("/playground")
@template(title="Playground")
def playground():
    state = Signals(btn_open=False, anchor_open=False, name="")
    return Div(
        H1("Playground", style="animation: var(--animation-fade-in) forwards;"),
        Div(            
            Div(
                Div(
                    LucideIcon("calendar"),
                    cls='absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none'
                ),
                # Input(datepicker='', id='default-datepicker', type='text', placeholder='Select date'),
                Input(
                    id='default-datepicker', 
                    type='text', 
                    placeholder='Select date',
                    data_init="new Datepicker(el, {autohide: true});"
                ),
                cls='relative max-w-sm'
            ),
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
