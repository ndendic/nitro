"""
Event-Driven Routes Demo - Nitro

Demonstrates routing in Nitro's event-driven paradigm:
1. Default routing — routes based on EntityName.method_name
2. Custom entity names with __route_name__
3. No more custom paths — action strings are always EntityName:id.method
4. Entities self-register via __init_subclass__ (no manual entity list)

Route format: /post/EntityName:id.method_name  (instance actions)
              /get/EntityName:id.method_name   (instance getters)

Run this app:
    uv run uvicorn examples.custom_routes_demo:app --reload --port 8095

Then visit:
    http://localhost:8095/            # Interactive documentation
    http://localhost:8095/docs        # OpenAPI docs
"""
import os
os.environ.setdefault("NITRO_DB_URL", "sqlite:///custom_routes.db")


from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# Import Nitro components
from nitro import Entity, get, post, action
from nitro.adapters.fastapi import configure_nitro


# =============================================================================
# EXAMPLE 1: Default Routing (for comparison)
# =============================================================================

class Product(Entity, table=True):
    """Entity with default routing — class name becomes the event prefix."""

    __tablename__ = "products"

    name: str = ""
    price: float = 0.0
    stock: int = 0

    @post()
    def restock(self, quantity: int) -> dict:
        """Restock the product.
        Route: POST /post/Product:laptop.restock
        """
        self.stock += quantity
        self.save()
        return {"product": self.name, "new_stock": self.stock}

    @post()
    def update_price(self, new_price: float) -> dict:
        """Update product price.
        Route: POST /post/Product:laptop.update_price
        """
        old_price = self.price
        self.price = new_price
        self.save()
        return {
            "product": self.name,
            "old_price": old_price,
            "new_price": new_price
        }


# =============================================================================
# EXAMPLE 2: Custom Entity Name with __route_name__
# =============================================================================

class User(Entity, table=True):
    """Entity with custom route name — __route_name__ controls the entity
    name in action strings (e.g., 'users' instead of 'User')."""

    __tablename__ = "users"
    __route_name__ = "users"  # Override default "User" → "users"

    username: str = ""
    email: str = ""
    is_active: bool = False
    last_login: Optional[str] = None

    @post()
    def activate(self) -> dict:
        """Activate user account.
        Route: POST /post/users:john.activate
        """
        self.is_active = True
        self.save()
        return {"username": self.username, "is_active": True}

    @post()
    def deactivate(self) -> dict:
        """Deactivate user account.
        Route: POST /post/users:john.deactivate
        """
        self.is_active = False
        self.save()
        return {"username": self.username, "is_active": False}

    @get()
    def profile(self) -> dict:
        """Get user profile.
        Route: GET /get/users:john.profile
        """
        return {
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "last_login": self.last_login
        }


# =============================================================================
# EXAMPLE 3: Method Names ARE the Action Strings
# =============================================================================

class Counter(Entity, table=True):
    """Entity demonstrating that method names define the action string.
    There is no path parameter — routes are always EntityName:id.method_name."""

    __tablename__ = "counters"

    name: str = "Counter"
    count: int = 0

    @post()
    def increment(self, amount: int = 1) -> dict:
        """Increment counter by amount.
        Route: POST /post/Counter:main.increment
        """
        self.count += amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @post()
    def decrement(self, amount: int = 1) -> dict:
        """Decrement counter by amount.
        Route: POST /post/Counter:main.decrement
        """
        self.count -= amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @get()
    def get_count(self) -> dict:
        """Get current count.
        Route: GET /get/Counter:main.get_count
        """
        return {"counter": self.name, "count": self.count}


# =============================================================================
# EXAMPLE 4: __route_name__ with Multiple Actions
# =============================================================================

class BlogPost(Entity, table=True):
    """Entity with __route_name__ — the only customization available.
    Custom paths no longer exist; the method name is always the action."""

    __tablename__ = "blog_posts"
    __route_name__ = "posts"  # Custom entity name in action strings

    title: str = ""
    content: str = ""
    is_published: bool = False
    views: int = 0
    published_at: Optional[str] = None

    @post()
    def make_public(self) -> dict:
        """Publish the blog post.
        Route: POST /post/posts:welcome.make_public
        """
        if not self.is_published:
            self.is_published = True
            self.published_at = datetime.now().isoformat()
            self.save()
        return {
            "title": self.title,
            "is_published": True,
            "published_at": self.published_at
        }

    @post()
    def make_private(self) -> dict:
        """Unpublish the blog post.
        Route: POST /post/posts:welcome.make_private
        """
        self.is_published = False
        self.published_at = None
        self.save()
        return {"title": self.title, "is_published": False}

    @get()
    def get_statistics(self) -> dict:
        """Get post statistics.
        Route: GET /get/posts:welcome.get_statistics
        """
        return {
            "title": self.title,
            "views": self.views,
            "is_published": self.is_published,
            "published_at": self.published_at
        }

    @post()
    def record_view(self) -> dict:
        """Record a view.
        Route: POST /post/posts:welcome.record_view
        """
        self.views += 1
        self.save()
        return {"title": self.title, "views": self.views}


# =============================================================================
# FastAPI Application Setup
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    Product.repository().init_db()
    User.repository().init_db()
    Counter.repository().init_db()
    BlogPost.repository().init_db()

    # Create sample data if tables are empty
    try:
        products = Product.all()
    except Exception:
        # Schema mismatch - skip sample data
        products = []

    if not products:
        try:
            product = Product(id="laptop", name="Laptop", price=999.99, stock=10)
            product.save()
        except Exception:
            pass  # Skip if schema issue

    try:
        users = User.all()
    except Exception:
        users = []

    if not users:
        try:
            user = User(id="john", username="john", email="john@example.com")
            user.save()
        except Exception:
            pass

    try:
        counters = Counter.all()
    except Exception:
        counters = []

    if not counters:
        try:
            counter = Counter(id="main", name="Main Counter", count=0)
            counter.save()
        except Exception:
            pass

    try:
        posts = BlogPost.all()
    except Exception:
        posts = []

    if not posts:
        try:
            post = BlogPost(
                id="welcome",
                title="Welcome to Nitro",
                content="This is a demo blog post"
            )
            post.save()
        except Exception:
            pass

    yield


app = FastAPI(
    title="Nitro Event-Driven Routes Demo",
    description="Demonstration of Nitro's event-driven routing system",
    version="2.0.0",
    lifespan=lifespan
)


# Entities self-register via __init_subclass__ — no entity list needed
configure_nitro(app)


# =============================================================================
# Documentation Homepage
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Interactive documentation page."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nitro Event-Driven Routes Demo</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com/3.4.16"></script>
    </head>
    <body class="bg-gray-50">
        <div class="container mx-auto px-4 py-8 max-w-5xl">
            <header class="mb-12">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">
                    Nitro Event-Driven Routes Demo
                </h1>
                <p class="text-lg text-gray-600">
                    Routes are event names: <code class="bg-gray-200 px-2 py-1 rounded">EntityName:id.method_name</code>
                </p>
                <p class="text-sm text-gray-500 mt-2">
                    No custom paths. No entity lists. Entities self-register via <code class="bg-gray-200 px-1 rounded">__init_subclass__</code>.
                </p>
            </header>

            <!-- Example 1: Default Routing -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 1: Default Routing
                </h2>
                <p class="text-gray-600 mb-4">
                    No customization. Routes use the class name as the event prefix.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: Product</p>
                    <code class="text-sm text-gray-700">
                        Event name: Product:laptop.restock<br>
                        Route: POST /post/Product:laptop.restock
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/Product:laptop.restock?quantity=5"
                    </code>
                    <code class="block bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/Product:laptop.update_price?new_price=899.99"
                    </code>
                </div>
            </section>

            <!-- Example 2: Custom Entity Name -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 2: Custom Entity Name
                </h2>
                <p class="text-gray-600 mb-4">
                    Use <code class="bg-gray-200 px-2 py-1 rounded">__route_name__</code>
                    to control the entity name in action strings (e.g., "users" instead of "User").
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: User</p>
                    <code class="text-sm text-gray-700">
                        __route_name__ = "users"<br>
                        Event name: users:john.activate<br>
                        Route: POST /post/users:john.activate
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-green-50 border border-green-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/users:john.activate"
                    </code>
                    <code class="block bg-green-50 border border-green-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/get/users:john.profile"
                    </code>
                </div>
            </section>

            <!-- Example 3: Method Names as Actions -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 3: Method Names Are the Action
                </h2>
                <p class="text-gray-600 mb-4">
                    There is no <code class="bg-gray-200 px-2 py-1 rounded">path</code> parameter.
                    The method name <em>is</em> the action in the event string.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: Counter</p>
                    <code class="text-sm text-gray-700">
                        @post()<br>
                        def increment(): ...  # POST /post/Counter:main.increment<br>
                        <br>
                        @get()<br>
                        def get_count(): ...  # GET /get/Counter:main.get_count
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/Counter:main.increment?amount=5"
                    </code>
                    <code class="block bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/get/Counter:main.get_count"
                    </code>
                </div>
            </section>

            <!-- Example 4: __route_name__ Only -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 4: __route_name__ with Multiple Actions
                </h2>
                <p class="text-gray-600 mb-4">
                    <code class="bg-gray-200 px-2 py-1 rounded">__route_name__</code> is the
                    only routing customization. It controls the entity prefix in all action strings.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: BlogPost</p>
                    <code class="text-sm text-gray-700">
                        __route_name__ = "posts"<br>
                        Event name: posts:welcome.make_public<br>
                        Route: POST /post/posts:welcome.make_public
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/posts:welcome.make_public"
                    </code>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/get/posts:welcome.get_statistics"
                    </code>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/post/posts:welcome.record_view"
                    </code>
                </div>
            </section>

            <!-- API Documentation -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    API Documentation
                </h2>
                <p class="text-gray-600 mb-4">
                    Explore all generated routes in the interactive API documentation.
                </p>
                <div class="flex gap-4">
                    <a href="/docs"
                       class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition">
                        OpenAPI Docs
                    </a>
                    <a href="/redoc"
                       class="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition">
                        ReDoc
                    </a>
                </div>
            </section>

            <!-- Route Comparison Table -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Route Comparison
                </h2>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Entity
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Event Name
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Route
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Customization
                                </th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    Product
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 font-mono">
                                    Product:laptop.restock
                                </td>
                                <td class="px-6 py-4 text-sm text-blue-600 font-mono">
                                    POST /post/Product:laptop.restock
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    None (default)
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    User
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 font-mono">
                                    users:john.activate
                                </td>
                                <td class="px-6 py-4 text-sm text-green-600 font-medium font-mono">
                                    POST /post/users:john.activate
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    __route_name__ = "users"
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    Counter
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 font-mono">
                                    Counter:main.increment
                                </td>
                                <td class="px-6 py-4 text-sm text-purple-600 font-medium font-mono">
                                    POST /post/Counter:main.increment
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    None (default)
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    BlogPost
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500 font-mono">
                                    posts:welcome.make_public
                                </td>
                                <td class="px-6 py-4 text-sm text-orange-600 font-medium font-mono">
                                    POST /post/posts:welcome.make_public
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    __route_name__ = "posts"
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- Code Examples -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Code Examples
                </h2>

                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Default Routing (class name = event prefix)
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>from nitro import Entity, get, post, action

class Product(Entity, table=True):
    name: str = ""
    stock: int = 0

    @post()
    def restock(self, quantity: int):
        self.stock += quantity
        self.save()
        return {"new_stock": self.stock}

# Route: POST /post/Product:laptop.restock</code></pre>
                </div>

                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Custom Entity Name with __route_name__
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>class User(Entity, table=True):
    __route_name__ = "users"  # Controls event prefix

    username: str = ""

    @post()
    def activate(self):
        self.is_active = True
        self.save()
        return {"status": "activated"}

# Route: POST /post/users:john.activate</code></pre>
                </div>

                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Self-Registering Entities (no entity list needed)
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>from fastapi import FastAPI
from nitro.adapters.fastapi import configure_nitro

app = FastAPI()

# Entities register themselves via __init_subclass__
# No entities parameter, no auto_discover
configure_nitro(app)

# All Entity subclasses are already registered!</code></pre>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Action Strings for Datastar
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>from nitro import action

counter = Counter.get("main")
action(counter.increment, amount=5)
# Returns: @post('/post/Counter:main.increment')

post = BlogPost.get("welcome")
action(post.make_public)
# Returns: @post('/post/posts:welcome.make_public')</code></pre>
                </div>
            </section>

            <!-- Footer -->
            <footer class="text-center text-gray-600 mt-12 pt-8 border-t border-gray-200">
                <p class="mb-2">
                    <strong>Nitro</strong> - Event-Driven Routes Demo
                </p>
                <p class="text-sm">
                    View source:
                    <code class="bg-gray-200 px-2 py-1 rounded text-xs">
                        examples/custom_routes_demo.py
                    </code>
                </p>
            </footer>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8095)
