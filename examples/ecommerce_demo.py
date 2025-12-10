"""
E-commerce Example - Event-Driven Workflow with Nitro

Demonstrates:
1. Event-driven architecture for order processing
2. Multiple entities with relationships
3. Decoupled business logic via events
4. Background task handling (email, inventory)

Run: uvicorn examples.ecommerce_demo:app --reload --port 8006
Then visit: http://localhost:8006/docs
"""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Add the local nitro package to the path (for development)
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository
from nitro.infrastructure.events import on, emit_async

# ============================================================================
# DOMAIN ENTITIES
# ============================================================================

class Product(Entity, table=True):
    """Product entity with inventory management."""
    name: str
    price: float
    stock: int = 0

    model_config = {"repository_class": SQLModelRepository}

    def reduce_stock(self, quantity: int) -> bool:
        """Reduce stock by quantity, return success."""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            print(f"📦 Reduced {self.name} stock by {quantity}. Remaining: {self.stock}")
            return True
        print(f"⚠️  Insufficient stock for {self.name}. Requested: {quantity}, Available: {self.stock}")
        return False


class OrderItem(BaseModel):
    """Order line item."""
    product_id: str
    quantity: int
    price: float


class Order(Entity, table=True):
    """Order entity with event-driven workflow."""
    customer_email: str
    items: str  # JSON-serialized list of items
    total: float = 0.0
    status: str = "pending"  # pending, placed, confirmed, cancelled
    created_at: Optional[str] = None

    model_config = {"repository_class": SQLModelRepository}

    def place(self) -> bool:
        """Place the order and trigger events."""
        if self.status != "pending":
            return False

        self.status = "placed"
        self.created_at = datetime.now().isoformat()
        self.save()

        print(f"🛒 Order {self.id} placed by {self.customer_email}")
        return True


# ============================================================================
# EVENT HANDLERS - Decoupled Business Logic
# ============================================================================

@on("order.placed")
async def send_confirmation_email(sender: Order, **kwargs):
    """Send order confirmation email (simulated)."""
    print(f"\n📧 EMAIL SERVICE")
    print(f"   To: {sender.customer_email}")
    print(f"   Subject: Order Confirmation #{sender.id}")
    print(f"   Order Total: ${sender.total:.2f}")
    print(f"   Status: {sender.status}")
    print(f"   ✓ Email sent successfully\n")


@on("order.placed")
async def update_inventory(sender: Order, **kwargs):
    """Update product inventory based on order items."""
    print(f"\n📦 INVENTORY SERVICE")
    print(f"   Processing order {sender.id}")

    # Parse items from JSON string
    import json
    items = json.loads(sender.items)

    all_updated = True
    for item_data in items:
        product = Product.get(item_data["product_id"])
        if product:
            success = product.reduce_stock(item_data["quantity"])
            if not success:
                all_updated = False
        else:
            print(f"   ⚠️  Product {item_data['product_id']} not found")
            all_updated = False

    if all_updated:
        print(f"   ✓ All inventory updated successfully\n")
    else:
        print(f"   ⚠️  Some inventory updates failed\n")


@on("order.placed")
async def log_analytics(sender: Order, **kwargs):
    """Log order for analytics (simulated)."""
    print(f"\n📊 ANALYTICS SERVICE")
    print(f"   Order ID: {sender.id}")
    print(f"   Customer: {sender.customer_email}")
    print(f"   Revenue: ${sender.total:.2f}")
    print(f"   Timestamp: {sender.created_at}")
    print(f"   ✓ Analytics logged\n")


@on("product.low_stock")
async def notify_restock(sender: Product, **kwargs):
    """Notify when product stock is low."""
    print(f"\n⚠️  LOW STOCK ALERT")
    print(f"   Product: {sender.name}")
    print(f"   Current Stock: {sender.stock}")
    print(f"   Action: Send notification to procurement team")
    print(f"   ✓ Restock notification sent\n")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(title="Nitro E-commerce Demo", version="1.0.0")

# Initialize database
SQLModelRepository().init_db()


# ============================================================================
# PRODUCT ENDPOINTS
# ============================================================================

@app.get("/products", response_model=List[Product])
async def list_products():
    """List all products."""
    return Product.all()


@app.post("/products", response_model=Product)
async def create_product(product: Product):
    """Create a new product."""
    product.save()
    print(f"✓ Product created: {product.name} (Stock: {product.stock})")
    return product


@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product."""
    product = Product.get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

class CreateOrderRequest(BaseModel):
    """Request to create an order."""
    customer_email: str
    items: List[OrderItem]


@app.post("/orders", response_model=Order)
async def create_order(request: CreateOrderRequest, background_tasks: BackgroundTasks):
    """
    Create and place an order.

    This demonstrates event-driven workflow:
    1. Order is created and placed
    2. order.placed event is emitted
    3. Three independent handlers execute:
       - send_confirmation_email
       - update_inventory
       - log_analytics
    """
    import json

    # Calculate total
    total = sum(item.price * item.quantity for item in request.items)

    # Create order
    order = Order(
        id=f"order-{datetime.now().timestamp()}",
        customer_email=request.customer_email,
        items=json.dumps([item.model_dump() for item in request.items]),
        total=total,
        status="pending"
    )
    order.save()

    # Place order (triggers events)
    order.place()

    # Emit order.placed event asynchronously
    # This will trigger all @on("order.placed") handlers
    background_tasks.add_task(emit_async, "order.placed", order)

    # Check for low stock
    for item in request.items:
        product = Product.get(item.product_id)
        if product and product.stock < 10:
            background_tasks.add_task(emit_async, "product.low_stock", product)

    return order


@app.get("/orders", response_model=List[Order])
async def list_orders():
    """List all orders."""
    return Order.all()


@app.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    """Get a specific order."""
    order = Order.get(order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


# ============================================================================
# DEMO INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def init_demo_data():
    """Initialize demo data on startup."""
    # Check if products already exist
    if len(Product.all()) == 0:
        # Create sample products
        products = [
            Product(id="prod-1", name="Laptop", price=999.99, stock=50),
            Product(id="prod-2", name="Mouse", price=29.99, stock=100),
            Product(id="prod-3", name="Keyboard", price=79.99, stock=75),
            Product(id="prod-4", name="Monitor", price=299.99, stock=8),  # Low stock
        ]

        for product in products:
            product.save()

        print("\n✓ Demo products initialized")
        print(f"  - {len(products)} products created")
        print(f"  - Visit http://localhost:8006/docs to try the API\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
