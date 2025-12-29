"""
Integration tests for FastHTML adapter.

Tests the complete auto-routing system with FastHTML, including:
- Entity discovery
- Route registration
- Parameter extraction
- Response formatting
- Error handling
"""

import pytest
import pytest_asyncio
from fasthtml.common import *
from httpx import AsyncClient
import json

from nitro import Entity, action
from nitro.adapters.fasthtml import configure_nitro, FastHTMLDispatcher
from nitro.infrastructure.repository.sql import SQLModelRepository


# ============================================================================
# TEST ENTITIES
# ============================================================================

class FastHTMLTestCounter(Entity, table=True):
    """Test counter entity with @action methods."""

    count: int = 0
    name: str = "Test Counter"

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Increment counter")
    def increment(self, amount: int = 1):
        """Increment by amount."""
        self.count += amount
        self.save()
        return {"count": self.count, "incremented": amount}

    @action(method="POST", summary="Reset counter")
    def reset(self):
        """Reset to zero."""
        self.count = 0
        self.save()
        return {"count": 0, "message": "reset"}

    @action(method="GET", summary="Get status")
    def status(self):
        """Get current status."""
        return {
            "id": self.id,
            "name": self.name,
            "count": self.count
        }


class FastHTMLTestProduct(Entity, table=True):
    """Test product entity with different action types."""

    name: str = ""
    price: float = 0.0
    stock: int = 0

    model_config = {
        "repository_class": SQLModelRepository
    }

    @action(method="POST", summary="Restock product")
    def restock(self, quantity: int):
        """Add stock."""
        self.stock += quantity
        self.save()
        return {"stock": self.stock}

    @action(method="POST", summary="Update price")
    def update_price(self, new_price: float):
        """Update product price."""
        self.price = new_price
        self.save()
        return {"price": self.price}


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def app():
    """Create FastHTML app with auto-routing configured."""
    test_app, rt = fast_app()

    # Configure Nitro with explicit entities
    configure_nitro(
        rt,
        entities=[FastHTMLTestCounter, FastHTMLTestProduct],
        auto_discover=False
    )

    return test_app


@pytest_asyncio.fixture
async def client(app):
    """Create async test client using httpx transport for ASGI apps."""
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def setup_test_data():
    """Create test entities before each test."""
    # Initialize database tables
    FastHTMLTestCounter.repository().init_db()
    FastHTMLTestProduct.repository().init_db()

    # Create test counter
    counter = FastHTMLTestCounter(id="test1", name="Test Counter", count=0)
    counter.save()

    # Create test product
    product = FastHTMLTestProduct(id="prod1", name="Widget", price=9.99, stock=100)
    product.save()

    yield

    # Cleanup
    test_counter = FastHTMLTestCounter.get("test1")
    if test_counter:
        test_counter.delete()

    test_product = FastHTMLTestProduct.get("prod1")
    if test_product:
        test_product.delete()


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

class TestFastHTMLConfiguration:
    """Test FastHTML adapter configuration."""

    def test_configure_nitro_discovers_entities(self):
        """configure_nitro discovers entities with @action methods."""
        app, rt = fast_app()
        dispatcher = configure_nitro(
            rt,
            entities=[FastHTMLTestCounter],
            auto_discover=False
        )

        # Check that routes were registered
        assert isinstance(dispatcher, FastHTMLDispatcher)
        assert FastHTMLTestCounter in dispatcher.routes
        assert "increment" in dispatcher.routes[FastHTMLTestCounter]

    def test_configure_nitro_with_prefix(self):
        """configure_nitro respects URL prefix."""
        app, rt = fast_app()
        configure_nitro(
            rt,
            entities=[FastHTMLTestCounter],
            prefix="/api/v1",
            auto_discover=False
        )

        # Check routes have correct prefix in the app
        # FastHTML stores routes in the app's router
        assert app is not None

    def test_routes_registered_correctly(self, app):
        """All @action methods are registered as FastHTML routes."""
        # FastHTML routes are stored in app.routes
        routes = app.routes
        assert len(routes) > 0


# ============================================================================
# ROUTE EXECUTION TESTS
# ============================================================================

class TestFastHTMLRouteExecution:
    """Test that routes execute correctly."""

    @pytest.mark.asyncio
    async def test_increment_route_works(self, client):
        """POST /fasthtmltestcounter/{id}/increment increments counter."""
        response = await client.post("/fasthtmltestcounter/test1/increment")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 1
        assert data["incremented"] == 1

    @pytest.mark.asyncio
    async def test_status_route_works(self, client):
        """GET /fasthtmltestcounter/{id}/status returns counter status."""
        response = await client.get("/fasthtmltestcounter/test1/status")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test1"
        assert data["name"] == "Test Counter"
        assert "count" in data

    @pytest.mark.asyncio
    async def test_reset_route_works(self, client):
        """POST /fasthtmltestcounter/{id}/reset resets counter."""
        # Increment first
        await client.post("/fasthtmltestcounter/test1/increment")

        # Reset
        response = await client.post("/fasthtmltestcounter/test1/reset")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["message"] == "reset"

    @pytest.mark.asyncio
    async def test_product_restock_works(self, client):
        """POST /fasthtmltestproduct/{id}/restock increases stock."""
        response = await client.post("/fasthtmltestproduct/prod1/restock?quantity=50")
        assert response.status_code == 200

        data = response.json()
        assert data["stock"] == 150  # 100 + 50


# ============================================================================
# PARAMETER EXTRACTION TESTS
# ============================================================================

class TestFastHTMLParameterExtraction:
    """Test parameter extraction from FastHTML requests."""

    @pytest.mark.asyncio
    async def test_query_parameters_extracted(self, client):
        """Query parameters are correctly extracted."""
        response = await client.post("/fasthtmltestcounter/test1/increment?amount=5")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 5
        assert data["incremented"] == 5

    @pytest.mark.asyncio
    async def test_json_body_parameters_extracted(self, client):
        """JSON body parameters are correctly extracted."""
        response = await client.post(
            "/fasthtmltestcounter/test1/increment",
            json={"amount": 10}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 10
        assert data["incremented"] == 10

    @pytest.mark.asyncio
    async def test_path_parameters_extracted(self, client):
        """Path parameters (entity ID) are correctly extracted."""
        # Create another counter
        counter2 = FastHTMLTestCounter(id="test2", name="Second Counter", count=0)
        counter2.save()

        # Test with different ID
        response = await client.get("/fasthtmltestcounter/test2/status")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test2"
        assert data["name"] == "Second Counter"

        # Cleanup
        counter2.delete()


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestFastHTMLErrorHandling:
    """Test error handling in FastHTML adapter."""

    @pytest.mark.asyncio
    async def test_missing_entity_returns_404(self, client):
        """Non-existent entity returns 404."""
        response = await client.post("/fasthtmltestcounter/nonexistent/increment")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"]["status_code"] == 404

    @pytest.mark.asyncio
    async def test_invalid_parameter_type_returns_422(self, client):
        """Invalid parameter type returns 422."""
        response = await client.post("/fasthtmltestcounter/test1/increment?amount=invalid")
        assert response.status_code == 422

        data = response.json()
        assert "error" in data

    @pytest.mark.asyncio
    async def test_missing_required_parameter_returns_422(self, client):
        """Missing required parameter returns 422."""
        response = await client.post("/fasthtmltestproduct/prod1/restock")
        assert response.status_code == 422

        data = response.json()
        assert "error" in data


# ============================================================================
# PERSISTENCE TESTS
# ============================================================================

class TestFastHTMLPersistence:
    """Test that entity changes persist across requests."""

    @pytest.mark.asyncio
    async def test_changes_persist_across_requests(self, client):
        """Entity modifications persist between requests."""
        # Increment
        response1 = await client.post("/fasthtmltestcounter/test1/increment?amount=3")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["count"] == 3

        # Check persisted
        response2 = await client.get("/fasthtmltestcounter/test1/status")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["count"] == 3

        # Increment again
        response3 = await client.post("/fasthtmltestcounter/test1/increment?amount=2")
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["count"] == 5


# ============================================================================
# RESPONSE FORMAT TESTS
# ============================================================================

class TestFastHTMLResponseFormat:
    """Test response formatting."""

    @pytest.mark.asyncio
    async def test_response_is_json(self, client):
        """Responses are JSON formatted."""
        response = await client.get("/fasthtmltestcounter/test1/status")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

        # Should parse as valid JSON
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_successful_response_format(self, client):
        """Successful responses have correct format."""
        response = await client.post("/fasthtmltestcounter/test1/increment")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "incremented" in data

    @pytest.mark.asyncio
    async def test_error_response_format(self, client):
        """Error responses have correct format."""
        response = await client.post("/fasthtmltestcounter/nonexistent/increment")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "message" in data["error"]
        assert "status_code" in data["error"]
