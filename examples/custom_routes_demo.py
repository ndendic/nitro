"""
Custom Routes Demo - Nitro

Demonstrates all custom routing features:
1. Custom entity names with __route_name__
2. Custom action paths with @action(path="...")
3. Combined custom naming
4. Comparison with default routing

Run this app:
    uv run uvicorn examples.custom_routes_demo:app --reload --port 8095

Then visit:
    http://localhost:8095/            # Interactive documentation
    http://localhost:8095/docs        # OpenAPI docs
"""

from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# Import Nitro components
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.routing import action, get, post
from nitro.adapters.fastapi import configure_nitro


# =============================================================================
# EXAMPLE 1: Default Routing (for comparison)
# =============================================================================

class Product(Entity, table=True):
    """Entity with default routing - for comparison."""

    __tablename__ = "products"

    name: str = ""
    price: float = 0.0
    stock: int = 0

    @action()
    def restock(self, quantity: int) -> dict:
        """Restock the product."""
        self.stock += quantity
        self.save()
        return {"product": self.name, "new_stock": self.stock}

    @action()
    def update_price(self, new_price: float) -> dict:
        """Update product price."""
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
    """Entity with custom route name (plural form)."""

    __tablename__ = "users"
    __route_name__ = "users"  # Override default "user" → "users"

    username: str = ""
    email: str = ""
    is_active: bool = False
    last_login: Optional[str] = None

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
            "is_active": self.is_active,
            "last_login": self.last_login
        }


# =============================================================================
# EXAMPLE 3: Custom Action Paths with @action(path="...")
# =============================================================================

class Counter(Entity, table=True):
    """Entity with custom action paths."""

    __tablename__ = "counters"

    name: str = "Counter"
    count: int = 0

    @action(path="/add")  # Custom path instead of /increment
    def increment(self, amount: int = 1) -> dict:
        """Increment counter by amount."""
        self.count += amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @action(path="/subtract")  # Custom path instead of /decrement
    def decrement(self, amount: int = 1) -> dict:
        """Decrement counter by amount."""
        self.count -= amount
        self.save()
        return {"counter": self.name, "count": self.count}

    @get(path="/value")  # Custom path for getter
    def get_count(self) -> dict:
        """Get current count."""
        return {"counter": self.name, "count": self.count}


# =============================================================================
# EXAMPLE 4: Combined Custom Entity Name + Action Paths
# =============================================================================

class BlogPost(Entity, table=True):
    """Entity with both custom entity name and action paths."""

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


# =============================================================================
# FastAPI Application Setup
# =============================================================================

app = FastAPI(
    title="Nitro Custom Routes Demo",
    description="Demonstration of Nitro's custom routing features",
    version="1.0.0"
)


# Configure Nitro auto-routing for all entities
configure_nitro(
    app,
    entities=[Product, User, Counter, BlogPost]
)


# Initialize database tables
@app.on_event("startup")
async def startup():
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
        <title>Nitro Custom Routes Demo</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com/3.4.16"></script>
    </head>
    <body class="bg-gray-50">
        <div class="container mx-auto px-4 py-8 max-w-5xl">
            <header class="mb-12">
                <h1 class="text-4xl font-bold text-gray-900 mb-2">
                    Nitro Custom Routes Demo
                </h1>
                <p class="text-lg text-gray-600">
                    Explore custom entity names and action paths
                </p>
            </header>

            <!-- Example 1: Default Routing -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 1: Default Routing
                </h2>
                <p class="text-gray-600 mb-4">
                    Standard Nitro routing without customization.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: Product</p>
                    <code class="text-sm text-gray-700">
                        Entity name: product<br>
                        Action: restock → /product/{id}/restock
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/product/laptop/restock?quantity=5"
                    </code>
                    <code class="block bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/product/laptop/update_price?new_price=899.99"
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
                    to customize the entity name in URLs (e.g., "users" instead of "user").
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: User</p>
                    <code class="text-sm text-gray-700">
                        __route_name__ = "users"  # Override<br>
                        Action: activate → /users/{id}/activate
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-green-50 border border-green-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/users/john/activate"
                    </code>
                    <code class="block bg-green-50 border border-green-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/users/john/profile"
                    </code>
                </div>
            </section>

            <!-- Example 3: Custom Action Paths -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 3: Custom Action Paths
                </h2>
                <p class="text-gray-600 mb-4">
                    Use <code class="bg-gray-200 px-2 py-1 rounded">@action(path="...")</code>
                    to customize action URL segments.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: Counter</p>
                    <code class="text-sm text-gray-700">
                        @action(path="/add")<br>
                        def increment(): ...  # /counter/{id}/add
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/counter/main/add?amount=5"
                    </code>
                    <code class="block bg-purple-50 border border-purple-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/counter/main/value"
                    </code>
                </div>
            </section>

            <!-- Example 4: Combined -->
            <section class="mb-12 bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-4">
                    Example 4: Combined Customization
                </h2>
                <p class="text-gray-600 mb-4">
                    Use both <code class="bg-gray-200 px-2 py-1 rounded">__route_name__</code>
                    and <code class="bg-gray-200 px-2 py-1 rounded">@action(path="...")</code>
                    together.
                </p>

                <div class="bg-gray-100 rounded p-4 mb-4">
                    <p class="text-sm font-mono text-gray-800 mb-2">Class: BlogPost</p>
                    <code class="text-sm text-gray-700">
                        __route_name__ = "posts"<br>
                        @action(path="/publish")<br>
                        def make_public(): ...  # /posts/{id}/publish
                    </code>
                </div>

                <div class="space-y-2">
                    <h3 class="font-semibold text-gray-900">Try it:</h3>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/posts/welcome/publish"
                    </code>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl "http://localhost:8095/posts/welcome/stats"
                    </code>
                    <code class="block bg-orange-50 border border-orange-200 rounded p-3 text-sm">
                        curl -X POST "http://localhost:8095/posts/welcome/view"
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
                                    Default Route
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                    Custom Route
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
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    /product/{id}/restock
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    <span class="text-blue-600">Same (default)</span>
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    None
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    User
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    /user/{id}/activate
                                </td>
                                <td class="px-6 py-4 text-sm text-green-600 font-medium">
                                    /users/{id}/activate
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    __route_name__
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    Counter
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    /counter/{id}/increment
                                </td>
                                <td class="px-6 py-4 text-sm text-purple-600 font-medium">
                                    /counter/{id}/add
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    @action(path="/add")
                                </td>
                            </tr>
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    BlogPost
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    /blogpost/{id}/make_public
                                </td>
                                <td class="px-6 py-4 text-sm text-orange-600 font-medium">
                                    /posts/{id}/publish
                                </td>
                                <td class="px-6 py-4 text-sm text-gray-500">
                                    Both
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
                        Custom Entity Name
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>class User(Entity, table=True):
    __route_name__ = "users"  # Plural form

    username: str = ""

    @action()
    def activate(self):
        self.is_active = True
        self.save()
        return {"status": "activated"}

# Generated route: POST /users/{id}/activate</code></pre>
                </div>

                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Custom Action Path
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>class Counter(Entity, table=True):
    count: int = 0

    @action(path="/add")  # Custom path
    def increment(self, amount: int = 1):
        self.count += amount
        self.save()
        return {"count": self.count}

# Generated route: POST /counter/{id}/add</code></pre>
                </div>

                <div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                        Combined Customization
                    </h3>
                    <pre class="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto"><code>class BlogPost(Entity, table=True):
    __route_name__ = "posts"

    title: str = ""

    @action(path="/publish")
    def make_public(self):
        self.is_published = True
        self.save()
        return {"status": "published"}

# Generated route: POST /posts/{id}/publish</code></pre>
                </div>
            </section>

            <!-- Footer -->
            <footer class="text-center text-gray-600 mt-12 pt-8 border-t border-gray-200">
                <p class="mb-2">
                    <strong>Nitro</strong> - Custom Routing Demo
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
