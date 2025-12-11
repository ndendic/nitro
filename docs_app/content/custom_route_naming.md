# Custom Route Naming Guide

> **Phase 2.2 Priority 2** - Advanced routing features for Nitro Framework

This guide covers Nitro's custom routing features that let you control how URLs are generated for your entities and actions.

---

## Table of Contents

1. [Overview](#overview)
2. [Custom Entity Names](#custom-entity-names)
3. [Custom Action Paths](#custom-action-paths)
4. [Combined Customization](#combined-customization)
5. [Use Cases](#use-cases)
6. [Best Practices](#best-practices)
7. [Migration Guide](#migration-guide)
8. [API Reference](#api-reference)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

Nitro's auto-routing system generates RESTful URLs based on your entity and method names. By default:

```python
class Product(Entity):
    @action()
    def restock(self):
        ...

# Generated URL: POST /product/{id}/restock
```

Custom routing lets you override these defaults for better API design.

### What You Can Customize

1. **Entity Name** - Use `__route_name__` to change the entity portion of the URL
2. **Action Path** - Use `@action(path="...")` to change the action portion of the URL
3. **Both** - Combine them for complete control

### Why Customize?

- **Plural forms**: `/users` instead of `/user`
- **Shorter URLs**: `/add` instead of `/increment`
- **Cleaner naming**: `/publish` instead of `/make_public`
- **API conventions**: Match REST conventions or organizational standards
- **Backward compatibility**: Keep old URLs when refactoring

---

## Custom Entity Names

### The Problem

By default, Nitro uses the class name (lowercase) as the entity name in URLs:

```python
class User(Entity):
    @action()
    def activate(self):
        ...

# URL: POST /user/{id}/activate
#           ^^^^ singular - not ideal
```

### The Solution

Use `__route_name__` to override the entity name:

```python
class User(Entity):
    __route_name__ = "users"  # Custom entity name

    @action()
    def activate(self):
        ...

# URL: POST /users/{id}/activate
#           ^^^^^ plural - better!
```

### How It Works

1. Define `__route_name__` as a class attribute
2. Nitro uses this instead of the class name
3. All actions on this entity use the custom name
4. Works with all adapters (FastAPI, Flask, FastHTML)

### Complete Example

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action, get

class User(Entity, table=True):
    __tablename__ = "users"
    __route_name__ = "users"  # Custom URL entity name

    username: str = ""
    email: str = ""
    is_active: bool = False

    @action()
    def activate(self) -> dict:
        """Activate user account."""
        self.is_active = True
        self.save()
        return {"username": self.username, "is_active": True}

    @action()
    def deactivate(self) -> dict:
        """Deactivate user account."""
        self.is_active = False
        self.save()
        return {"username": self.username, "is_active": False}

    @get()
    def profile(self) -> dict:
        """Get user profile."""
        return {
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active
        }

# Generated URLs:
# POST /users/{id}/activate
# POST /users/{id}/deactivate
# GET  /users/{id}/profile
```

### When to Use

- **Pluralization**: Most REST APIs use plural resource names
- **Abbreviation**: Shorten long class names (`Organization` → `orgs`)
- **Clarity**: Use more descriptive names (`BlogPost` → `posts`)
- **Conventions**: Match your team's API naming standards

---

## Custom Action Paths

### The Problem

By default, Nitro uses the method name as the action segment:

```python
class Counter(Entity):
    @action()
    def increment(self, amount: int = 1):
        ...

# URL: POST /counter/{id}/increment
#                        ^^^^^^^^^ method name - verbose
```

### The Solution

Use `@action(path="...")` to customize the action segment:

```python
class Counter(Entity):
    @action(path="/add")  # Custom action path
    def increment(self, amount: int = 1):
        ...

# URL: POST /counter/{id}/add
#                        ^^^ custom - concise
```

### How It Works

1. Add `path` parameter to `@action()` decorator
2. Path replaces the method name in the URL
3. Single-segment paths (like `/add`) replace the action
4. Multi-segment paths override the entire path after entity

### Path Types

#### Single-Segment Paths (Relative)

Replace just the action portion:

```python
@action(path="/add")
def increment(self):
    ...

# URL: POST /counter/{id}/add
#           ^^^^^^^^^^^^^ kept ^^^ custom
```

#### Multi-Segment Paths (Absolute)

Replace everything after the entity name:

```python
@action(path="/operations/add")
def increment(self):
    ...

# URL: POST /counter/operations/add
#           ^^^^^^^ kept ^^^^^^^^^^^ custom
```

### Complete Example

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action, get, post

class Counter(Entity, table=True):
    __tablename__ = "counters"

    name: str = "Counter"
    count: int = 0

    @action(path="/add")
    def increment(self, amount: int = 1) -> dict:
        """Increment counter."""
        self.count += amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @action(path="/subtract")
    def decrement(self, amount: int = 1) -> dict:
        """Decrement counter."""
        self.count -= amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @post(path="/reset")
    def reset_to_zero(self) -> dict:
        """Reset counter to zero."""
        self.count = 0
        self.save()
        return {"counter": self.name, "count": 0}

    @get(path="/value")
    def get_current_value(self) -> dict:
        """Get current count."""
        return {"counter": self.name, "count": self.count}

# Generated URLs:
# POST /counter/{id}/add      (not /increment)
# POST /counter/{id}/subtract (not /decrement)
# POST /counter/{id}/reset    (not /reset_to_zero)
# GET  /counter/{id}/value    (not /get_current_value)
```

### When to Use

- **Brevity**: Shorter URLs (`/add` vs `/increment`)
- **Consistency**: Standardize action names across entities
- **Clarity**: Use common REST verbs (`/publish` vs `/make_public`)
- **Legacy support**: Maintain old URLs during refactoring

---

## Combined Customization

You can use both `__route_name__` and custom action paths together for maximum control:

### Example: Blog System

```python
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action, get, post
from typing import Optional
from datetime import datetime

class BlogPost(Entity, table=True):
    __tablename__ = "blog_posts"
    __route_name__ = "posts"  # Custom entity name

    title: str = ""
    content: str = ""
    is_published: bool = False
    views: int = 0
    published_at: Optional[str] = None

    @action(path="/publish")  # Custom action path
    def make_public(self) -> dict:
        """Publish the blog post."""
        if not self.is_published:
            self.is_published = True
            self.published_at = datetime.now().isoformat()
            self.save()
        return {
            "title": self.title,
            "is_published": True,
            "published_at": self.published_at
        }

    @action(path="/unpublish")  # Custom action path
    def make_private(self) -> dict:
        """Unpublish the blog post."""
        self.is_published = False
        self.published_at = None
        self.save()
        return {"title": self.title, "is_published": False}

    @get(path="/stats")  # Custom action path
    def get_statistics(self) -> dict:
        """Get post statistics."""
        return {
            "title": self.title,
            "views": self.views,
            "is_published": self.is_published,
            "published_at": self.published_at
        }

    @post(path="/view")  # Custom action path
    def record_view(self) -> dict:
        """Record a view."""
        self.views += 1
        self.save()
        return {"title": self.title, "views": self.views}

# Generated URLs:
# POST /posts/{id}/publish   (not /blogpost/{id}/make_public)
# POST /posts/{id}/unpublish (not /blogpost/{id}/make_private)
# GET  /posts/{id}/stats     (not /blogpost/{id}/get_statistics)
# POST /posts/{id}/view      (not /blogpost/{id}/record_view)
```

### Before vs After

```
# Before (defaults)
POST /blogpost/{id}/make_public
POST /blogpost/{id}/make_private
GET  /blogpost/{id}/get_statistics
POST /blogpost/{id}/record_view

# After (customized)
POST /posts/{id}/publish   ← Better!
POST /posts/{id}/unpublish ← Cleaner!
GET  /posts/{id}/stats     ← Shorter!
POST /posts/{id}/view      ← Standard!
```

---

## Use Cases

### 1. RESTful Resource Names

Use plural entity names for REST conventions:

```python
class Product(Entity):
    __route_name__ = "products"  # Plural

# POST /products/{id}/restock
# GET  /products/{id}/details
```

### 2. Short Action Names

Use concise verbs for common operations:

```python
class Task(Entity):
    __route_name__ = "tasks"

    @action(path="/start")
    def begin_work(self): ...

    @action(path="/stop")
    def end_work(self): ...

    @action(path="/finish")
    def mark_complete(self): ...

# POST /tasks/{id}/start
# POST /tasks/{id}/stop
# POST /tasks/{id}/finish
```

### 3. API Versioning

Combine with prefixes for versioned APIs:

```python
# V1 API
class UserV1(Entity):
    __route_name__ = "user"

    @action()
    def activate(self): ...

# V2 API (with better naming)
class UserV2(Entity):
    __route_name__ = "users"  # Improved!

    @action(path="/activate")  # Same name, cleaner
    def activate_account(self): ...

# V1: POST /api/v1/user/{id}/activate
# V2: POST /api/v2/users/{id}/activate
```

### 4. Nested Resources

Use multi-segment paths for hierarchy:

```python
class Comment(Entity):
    __route_name__ = "comments"

    @action(path="/posts/{post_id}/like")
    def like_on_post(self, post_id: str): ...

# POST /comments/{id}/posts/{post_id}/like
```

### 5. Legacy URL Support

Maintain old URLs during refactoring:

```python
class Order(Entity):
    __route_name__ = "orders"

    @action(path="/submit")  # Old URL
    def place_order(self): ...

    @action(path="/place")  # New URL, same function
    def place_order_v2(self):
        return self.place_order()  # Delegate

# Both work:
# POST /orders/{id}/submit (legacy)
# POST /orders/{id}/place  (new)
```

---

## Best Practices

### 1. Be Consistent

Use the same style across your API:

```python
# ✅ Good - consistent plural names
class User(Entity):
    __route_name__ = "users"

class Product(Entity):
    __route_name__ = "products"

# ❌ Avoid - mixing singular and plural
class User(Entity):
    __route_name__ = "user"  # Singular

class Product(Entity):
    __route_name__ = "products"  # Plural
```

### 2. Use Standard REST Verbs

Prefer common action names:

```python
# ✅ Good - standard verbs
@action(path="/publish")
@action(path="/archive")
@action(path="/activate")

# ❌ Avoid - verbose or unclear
@action(path="/make_published")
@action(path="/move_to_archive")
@action(path="/turn_on_activation")
```

### 3. Keep Paths Short

Shorter URLs are easier to use:

```python
# ✅ Good - concise
@action(path="/add")
@action(path="/remove")

# ❌ Avoid - unnecessarily long
@action(path="/add_item_to_collection")
@action(path="/remove_item_from_collection")
```

### 4. Document Custom Paths

Add docstrings explaining why you customized:

```python
class User(Entity):
    __route_name__ = "users"  # REST convention: plural resources

    @action(path="/activate")  # Shorter than method name
    def activate_user_account(self):
        """Activate user account.

        URL: POST /users/{id}/activate
        Custom path for brevity.
        """
        ...
```

### 5. Test Your URLs

Verify custom URLs work as expected:

```python
def test_custom_entity_name():
    """Verify User uses /users/ not /user/."""
    response = client.post("/users/john/activate")
    assert response.status_code == 200

def test_custom_action_path():
    """Verify Counter uses /add not /increment."""
    response = client.post("/counter/main/add?amount=5")
    assert response.status_code == 200
```

### 6. Update OpenAPI Docs

Custom paths should have clear descriptions:

```python
@action(path="/publish")
def make_public(self):
    """Publish the blog post.

    Makes the post visible to the public. Sets `is_published` to True
    and records the publication timestamp.

    URL: POST /posts/{id}/publish
    """
    ...
```

---

## Migration Guide

### Migrating from Default to Custom Routing

Follow these steps to add custom routing to existing entities:

#### Step 1: Identify Candidates

Look for entities where custom names would improve clarity:

```python
# Candidates for __route_name__:
class User(Entity): ...           # → "users" (plural)
class BlogPost(Entity): ...       # → "posts" (shorter)
class Organization(Entity): ...   # → "orgs" (abbreviated)

# Candidates for custom paths:
def increment(self): ...          # → path="/add"
def make_public(self): ...        # → path="/publish"
def activate_user_account(self): ... # → path="/activate"
```

#### Step 2: Add Custom Names

Start with `__route_name__`:

```python
class User(Entity):
    __route_name__ = "users"  # Add this

    # ... rest of class unchanged
```

#### Step 3: Add Custom Paths

Add `path` parameter to actions:

```python
@action()  # Before
def increment(self, amount: int = 1):
    ...

@action(path="/add")  # After
def increment(self, amount: int = 1):
    ...
```

#### Step 4: Test Changes

Run your test suite:

```bash
# Run tests
pytest tests/

# Test specific routes
curl -X POST "http://localhost:8000/users/john/activate"
```

#### Step 5: Update Documentation

Update API docs with new URLs:

```markdown
## Endpoints

- `POST /users/{id}/activate` - Activate user account
- `POST /posts/{id}/publish` - Publish blog post
- `POST /counter/{id}/add` - Increment counter
```

#### Step 6: Handle Breaking Changes

If you have existing clients, consider:

1. **Version your API** - Keep old URLs in v1, new in v2
2. **Add redirects** - Redirect old URLs to new ones
3. **Support both** - Create wrapper methods

Example - Supporting both URLs:

```python
class User(Entity):
    __route_name__ = "users"

    @action(path="/activate")  # New URL
    def activate_account(self):
        self.is_active = True
        self.save()
        return {"status": "activated"}

    @action(path="/activate_user_account")  # Legacy URL
    def legacy_activate(self):
        """Deprecated: Use /activate instead."""
        return self.activate_account()  # Delegate to new method

# Both work:
# POST /users/{id}/activate (new)
# POST /users/{id}/activate_user_account (legacy)
```

---

## API Reference

### `__route_name__` Class Attribute

**Type**: `str`
**Location**: Entity class level
**Purpose**: Override entity name in generated URLs

```python
class MyEntity(Entity):
    __route_name__ = "custom_name"
```

- **Default**: Lowercase class name (e.g., `MyEntity` → `myentity`)
- **Custom**: Any string you specify
- **Scope**: Applies to all actions on the entity
- **Case**: Automatically lowercased
- **Characters**: Use lowercase letters, numbers, hyphens, underscores

### `@action(path="...")` Decorator Parameter

**Type**: `str`
**Location**: Action method decorator
**Purpose**: Override action segment in generated URLs

```python
@action(path="/custom_path")
def my_method(self):
    ...
```

- **Default**: Method name
- **Custom**: Any string you specify
- **Format**: Should start with `/`
- **Types**:
  - Single-segment: `/action` - replaces method name
  - Multi-segment: `/path/to/action` - replaces entire path after entity

### Convenience Decorators

These also support `path` parameter:

```python
@get(path="/custom")    # HTTP GET
@post(path="/custom")   # HTTP POST
@put(path="/custom")    # HTTP PUT
@delete(path="/custom") # HTTP DELETE
```

---

## Examples

### Example 1: E-commerce API

```python
class Product(Entity, table=True):
    __route_name__ = "products"

    name: str = ""
    price: float = 0.0
    stock: int = 0

    @action(path="/restock")
    def add_inventory(self, quantity: int) -> dict:
        self.stock += quantity
        self.save()
        return {"stock": self.stock}

    @action(path="/discount")
    def apply_discount(self, percent: float) -> dict:
        self.price *= (1 - percent / 100)
        self.save()
        return {"price": self.price}

# URLs:
# POST /products/{id}/restock?quantity=100
# POST /products/{id}/discount?percent=15
```

### Example 2: Task Management

```python
class Task(Entity, table=True):
    __route_name__ = "tasks"

    title: str = ""
    status: str = "pending"
    assigned_to: Optional[str] = None

    @action(path="/start")
    def begin(self) -> dict:
        self.status = "in_progress"
        self.save()
        return {"status": self.status}

    @action(path="/complete")
    def finish(self) -> dict:
        self.status = "completed"
        self.save()
        return {"status": self.status}

    @action(path="/assign")
    def assign_to(self, user_id: str) -> dict:
        self.assigned_to = user_id
        self.save()
        return {"assigned_to": self.assigned_to}

# URLs:
# POST /tasks/{id}/start
# POST /tasks/{id}/complete
# POST /tasks/{id}/assign?user_id=john
```

### Example 3: Content Management

```python
class Article(Entity, table=True):
    __route_name__ = "articles"

    title: str = ""
    status: str = "draft"
    views: int = 0

    @action(path="/publish")
    def make_live(self) -> dict:
        self.status = "published"
        self.save()
        return {"status": "published"}

    @action(path="/archive")
    def move_to_archive(self) -> dict:
        self.status = "archived"
        self.save()
        return {"status": "archived"}

    @get(path="/analytics")
    def get_analytics(self) -> dict:
        return {
            "title": self.title,
            "views": self.views,
            "status": self.status
        }

# URLs:
# POST /articles/{id}/publish
# POST /articles/{id}/archive
# GET  /articles/{id}/analytics
```

---

## Troubleshooting

### Issue: Custom Path Not Working

**Problem**: Route still uses method name instead of custom path

```python
@action(path="/add")
def increment(self):
    ...

# Still generates: /counter/{id}/increment (wrong)
```

**Solution**: Ensure path starts with `/`:

```python
@action(path="/add")  # ✅ Correct
@action(path="add")   # ❌ Wrong - no leading slash
```

### Issue: 404 on Custom Entity Name

**Problem**: Getting 404 when using custom entity name

```python
class User(Entity):
    __route_name__ = "users"

# POST /users/john/activate → 404
```

**Solutions**:

1. Check spelling and case:
   ```python
   __route_name__ = "users"  # ✅ Lowercase
   __route_name__ = "Users"  # ❌ Will be lowercased to "users"
   ```

2. Verify configure_nitro includes entity:
   ```python
   configure_nitro(app, entities=[User])  # Must include
   ```

3. Check database initialization:
   ```python
   User.repository().init_db()  # Required
   ```

### Issue: Ambiguous Routes

**Problem**: Two actions generate the same URL

```python
class Product(Entity):
    @action(path="/update")
    def update_price(self, new_price: float):
        ...

    @action(path="/update")  # ❌ Conflict!
    def update_stock(self, new_stock: int):
        ...
```

**Solution**: Use distinct paths:

```python
@action(path="/update/price")
def update_price(self, new_price: float):
    ...

@action(path="/update/stock")
def update_stock(self, new_stock: int):
    ...

# URLs:
# POST /product/{id}/update/price
# POST /product/{id}/update/stock
```

### Issue: Multi-Segment Path Not Working

**Problem**: Multi-segment path doesn't work as expected

```python
@action(path="/admin/activate")
def admin_activate(self):
    ...

# Expected: /user/{id}/admin/activate
# Actual: Something else
```

**Solution**: Multi-segment paths replace the entire path after the entity:

```python
# This works:
@action(path="/admin/activate")
# URL: /user/admin/activate (no {id}!)

# If you need {id}, use single-segment:
@action(path="/activate")
# URL: /user/{id}/activate
```

### Issue: Tests Failing After Adding Custom Paths

**Problem**: Existing tests fail after adding custom names

```python
# Test before:
response = client.post("/user/john/activate")

# Now fails after adding __route_name__ = "users"
```

**Solution**: Update test URLs to match new routes:

```python
# Update test:
response = client.post("/users/john/activate")  # Note plural
```

---

## Summary

Custom routing in Nitro gives you complete control over URL generation:

### Key Features

1. **`__route_name__`** - Customize entity name in URLs
2. **`@action(path="...")`** - Customize action paths
3. **Combined** - Use both for maximum control

### Common Patterns

```python
# Pattern 1: Plural entity names
__route_name__ = "users"

# Pattern 2: Short action paths
@action(path="/add")

# Pattern 3: REST-style verbs
@action(path="/publish")

# Pattern 4: Combined
__route_name__ = "posts"
@action(path="/publish")
```

### Quick Reference

| Feature | Syntax | Example | Generated URL |
|---------|--------|---------|---------------|
| Default | None | `class User` → `activate()` | `/user/{id}/activate` |
| Custom entity | `__route_name__ = "users"` | `class User` → `activate()` | `/users/{id}/activate` |
| Custom path | `@action(path="/enable")` | `class User` → `activate()` | `/user/{id}/enable` |
| Combined | Both | `__route_name__ + path` | `/users/{id}/enable` |

### Next Steps

1. **Try the demo**: Run `examples/custom_routes_demo.py`
2. **Read the code**: Review example implementations
3. **Experiment**: Add custom routing to your entities
4. **Test**: Verify URLs in OpenAPI docs
5. **Refine**: Iterate based on API design feedback

---

**Related Documentation**:
- [Route Prefixes Guide](route_prefixes_guide.md) - API versioning with prefixes
- [Phase 2 Design](../PHASE_2_AUTO_ROUTING_DESIGN.md) - Complete auto-routing design
- [README](../README.md) - Nitro Framework overview

**Examples**:
- `examples/custom_routes_demo.py` - Interactive demo
- `tests/test_routing_custom_paths.py` - Test suite
- `examples/versioned_api_demo.py` - Versioned API with custom routing

---

*Last updated: 2025-12-10*
*Nitro Framework - Phase 2.2 Priority 2*
