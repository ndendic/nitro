---
title: Welcome
category: Home
order: 0
---

# Nitro Framework Documentation

Nitro is a Python web framework that treats business logic as first-class citizens, providing rich domain entities with hybrid persistence, framework-agnostic design, and progressive complexity.

## Key Features

- **Entity-centric design** - Business logic lives in entity methods, not service layers
- **Hybrid persistence** - Each entity chooses its storage backend (SQL, memory, Redis)
- **Framework-agnostic** - Works seamlessly with FastAPI, Flask, FastHTML, Starlette
- **Event-driven architecture** - Decouple side effects with domain events using Blinker
- **High-performance HTML** - Rust-powered HTML generation via RustyTags (3-10x faster)
- **Reactive UI** - Datastar SDK integration for reactive components without JavaScript

## Getting Started

New to Nitro? Start here:

- [Installation](getting-started/installation.md) - Install Nitro and verify your setup
- [Quickstart Tutorial](getting-started/quickstart.md) - Build a todo app in 5 minutes

## Core Concepts

### Entity System

Learn how to build rich domain models with built-in persistence:

- [Entity Overview](entity/overview.md) - Introduction to entity-centric design
- [Active Record Patterns](entity/active-record.md) - Entity methods and lifecycle
- [Repository Patterns](entity/repository-patterns.md) - Persistence backends and configuration

### Event System

Decouple side effects and build event-driven applications:

- [Events Overview](events/overview.md) - Event-driven architecture in Nitro
- [Backend Events](events/backend-events.md) - Using Blinker for domain events
- [CQRS Patterns](events/cqrs-patterns.md) - Command Query Responsibility Segregation

## Framework Integrations

Use Nitro with your preferred Python web framework:

- [Overview](frameworks/overview.md) - How Nitro integrates with frameworks
- [FastAPI](frameworks/fastapi.md) - FastAPI integration guide
- [FastHTML](frameworks/fasthtml.md) - FastHTML integration guide
- [Flask](frameworks/flask.md) - Flask integration guide
- [Starlette](frameworks/starlette.md) - Starlette integration guide

## Frontend

### RustyTags

High-performance HTML generation powered by Rust:

- [Overview](frontend/rustytags/overview.md) - Why RustyTags and performance benefits
- [Usage Guide](frontend/rustytags/usage.md) - How to use RustyTags tags and components

### Datastar

Reactive UI without JavaScript complexity:

- [Philosophy](frontend/datastar/philosophy.md) - The Datastar approach to reactivity
- [Signals](frontend/datastar/signals.md) - Reactive state management
- [Attributes](frontend/datastar/attributes.md) - data-* attributes for interactivity
- [Expressions](frontend/datastar/expressions.md) - Expression syntax and evaluation
- [SSE Integration](frontend/datastar/sse-integration.md) - Server-Sent Events for real-time updates
- [Helpers](frontend/datastar/helpers.md) - Helper functions and utilities

### Components

Build beautiful UIs with Tailwind CSS and component patterns:

- [Overview](frontend/components/overview.md) - Component architecture and patterns
- [Basecoat Styling](frontend/components/basecoat-styling.md) - Using Basecoat CSS framework
- [Custom Themes](frontend/components/custom-themes.md) - Creating custom component themes
- [Tailwind CLI](frontend/components/nitro-tw-cli.md) - Nitro's Tailwind CSS CLI tool

## Reference

Quick reference and API documentation:

- [API Reference](reference/api.md) - Complete API documentation
- [CLI Reference](reference/cli.md) - Command-line tools and usage

## Philosophy

Nitro is designed around these principles:

1. **Rich Domain Models** - Business logic belongs in entity methods, not scattered across service layers
2. **Progressive Complexity** - Start simple, scale without rewrites
3. **Framework Agnostic** - Your domain model shouldn't depend on your web framework
4. **Hybrid Persistence** - Different data needs different storage - choose per entity
5. **Event-Driven by Default** - Decouple side effects naturally with domain events

## Quick Example

Here's a complete todo app in under 50 lines:

```python
from fastapi import FastAPI
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.events import on
from rusty_tags import H1, Div, Form, Input, Button, Ul, Li
from nitro.infrastructure.html import Page

class Todo(Entity, table=True):
    title: str
    completed: bool = False

app = FastAPI()
Todo._repository.init_db()

@on("todo.created")
def log_creation(sender, **kwargs):
    print(f"Created: {sender.title}")

@app.get("/")
def homepage():
    todos = Todo.all()
    return str(Page(
        H1("Todo App"),
        Form(
            Input(name="title", placeholder="What needs to be done?"),
            Button("Add", type="submit"),
            method="POST", action="/add"
        ),
        Ul(*[Li(t.title) for t in todos]),
        title="Todo App", tailwind4=True
    ))

@app.post("/add")
def add_todo(title: str):
    todo = Todo(id=str(len(Todo.all()) + 1), title=title)
    todo.save()
    return RedirectResponse("/", status_code=303)
```

See the [Quickstart Tutorial](getting-started/quickstart.md) for a detailed walkthrough.

## Next Steps

1. Follow the [Installation](getting-started/installation.md) guide
2. Complete the [Quickstart Tutorial](getting-started/quickstart.md)
3. Explore [Entity Patterns](entity/active-record.md)
4. Learn about [Events](events/backend-events.md)
5. Integrate with [your framework](frameworks/overview.md)
