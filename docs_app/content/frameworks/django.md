---
title: Django
category: Frameworks
order: 6
---

# Django Integration

> **Status: Planned**
>
> Django integration is planned for a future release of Nitro. This page will be updated when the adapter is implemented.

## Planned Features

When Django support is added, Nitro will provide:

- **DjangoDispatcher** - Auto-routing for `@action` decorated entity methods
- **URL routing integration** - Seamless integration with Django's URL configuration
- **Template integration** - Use RustyTags alongside Django templates
- **Admin panel integration** - Auto-generate admin interfaces for Nitro entities
- **Django ORM compatibility** - Work alongside Django models

## Current Workarounds

While the official Django adapter is in development, you can still use Nitro entities in Django applications:

### 1. Use Nitro Entities in Django Views

```python
from django.http import JsonResponse
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action

class Todo(Entity, table=True):
    title: str
    completed: bool = False

    @action(method="POST")
    def complete(self):
        self.completed = True
        self.save()
        return self.model_dump()

# Django view
def todo_complete(request, todo_id):
    """Manually call entity action from Django view."""
    todo = Todo.get(todo_id)
    if not todo:
        return JsonResponse({"error": "Not found"}, status=404)

    result = todo.complete()
    return JsonResponse(result)

# urls.py
from django.urls import path

urlpatterns = [
    path('todo/<str:todo_id>/complete/', todo_complete, name='todo_complete'),
]
```

### 2. Use Datastar with Django

The `datastar_py` library includes Django support for SSE integration:

```python
from datastar_py.django import datastar_response
from django.http import StreamingResponse

def sse_updates(request):
    """Stream updates to client using Datastar."""
    def event_stream():
        # Your SSE logic here
        pass

    return datastar_response(event_stream())
```

See the [datastar_py documentation](https://github.com/starfederation/datastar-py) for Django-specific examples.

### 3. Use SQLModel Entities Alongside Django Models

Nitro entities use SQLModel, which is compatible with SQLAlchemy. You can run both Django's ORM and Nitro's entities side-by-side:

```python
# Django model (uses Django ORM)
from django.db import models

class DjangoUser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()

# Nitro entity (uses SQLModel/SQLAlchemy)
from nitro.domain.entities.base_entity import Entity

class NitroProduct(Entity, table=True):
    name: str
    price: float

# Both can coexist in the same application
# Use separate database connections if needed
```

## Why Not Django Yet?

Django integration requires careful design considerations:

1. **ORM Compatibility** - Django has its own ORM; Nitro uses SQLModel/SQLAlchemy
2. **URL Routing** - Django's URL configuration is different from FastAPI/Flask
3. **Middleware Integration** - Need to properly integrate with Django's middleware system
4. **Admin Integration** - Django Admin is a core feature that should work with Nitro entities

We want to ensure the Django adapter is production-ready and follows Django best practices.

## Contributing

If you'd like to help implement Django support, contributions are welcome! Here's what needs to be done:

1. **Create DjangoDispatcher** - Extend `NitroDispatcher` for Django URL routing
2. **URL Pattern Generation** - Generate Django URL patterns from `@action` decorators
3. **Middleware Integration** - Ensure compatibility with Django middleware
4. **Admin Integration** - Auto-register Nitro entities in Django Admin
5. **Documentation** - Complete integration guide with examples

See the contribution guidelines in the [Nitro repository](https://github.com/your-repo/nitro) to get started.

## Timeline

Django integration is planned for **Phase 2** of Nitro's roadmap. Check the [project roadmap](https://github.com/your-repo/nitro/blob/main/docs/roadmap.md) for updates.

## Alternative: Use FastAPI Alongside Django

If you need Nitro's auto-routing features now, consider running FastAPI alongside Django:

```python
# main.py - Run both Django and FastAPI
from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

# FastAPI app with Nitro
api = FastAPI()
configure_nitro(api)

# Mount Django app under /django
from django.core.wsgi import get_wsgi_application
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django_app = get_wsgi_application()

# Use a reverse proxy (nginx) to route:
# /api/* → FastAPI (Nitro auto-routes)
# /* → Django (traditional views)
```

## Next Steps

- **[Framework Overview](./overview.md)** - Understand framework-agnostic design
- **[FastAPI Integration](./fastapi.md)** - Similar auto-routing pattern
- **[Starlette Integration](./starlette.md)** - SSE helpers (Django-compatible)

## Get Notified

Want to be notified when Django support is available? Star and watch the [Nitro repository](https://github.com/your-repo/nitro) on GitHub.
