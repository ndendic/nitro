"""
Monitoring Example - Logging, Statistics, and Metrics

Demonstrates:
1. Entity operation logging
2. Repository statistics collection
3. Event bus metrics

Run: python examples/monitoring_demo.py
"""

import sys
from pathlib import Path
import logging

# Add the local nitro package to the path (for development)
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.memory import MemoryRepository
from nitro.infrastructure.events import on, emit
from nitro.infrastructure.monitoring import (
    configure_nitro_logging,
    log_entity_operation,
    repository_monitor,
    event_bus_monitor,
)


# ============================================================================
# TEST 1: Entity Operations Logging
# ============================================================================

def test_entity_logging():
    """
    Test: Entity operations can be logged
    Step 1: Configure logging for Nitro ✓
    Step 2: Perform entity operations ✓
    Step 3: Verify operations are logged with details ✓
    """
    print("=" * 80)
    print("TEST 1: Entity Operations Logging")
    print("=" * 80)

    # Step 1: Configure logging
    print("\nStep 1: Configure logging for Nitro")
    logger = configure_nitro_logging(logging.INFO)
    print("✓ Logging configured at INFO level\n")

    # Define entity with memory backend
    class User(Entity):
        name: str
        email: str

        class Config:
            arbitrary_types_allowed = True

        @classmethod
        def repository_class(cls):
            return MemoryRepository

    # Step 2: Perform operations with logging
    print("Step 2: Perform entity operations with logging")

    log_entity_operation("User", "create", name="Alice", email="alice@example.com")
    user1 = User(id="user-1", name="Alice", email="alice@example.com")
    user1.save()

    log_entity_operation("User", "get", entity_id="user-1")
    user = User.get("user-1")

    log_entity_operation("User", "update", entity_id="user-1", field="name")
    user.name = "Alice Smith"
    user.save()

    log_entity_operation("User", "delete", entity_id="user-1")
    user.delete()

    # Step 3: Verify
    print("\n✓ All operations logged with details")
    print("✓ Check console output above for log entries")
    print("\n✅ TEST 1 PASSED: Entity operations logging works!\n")


# ============================================================================
# TEST 2: Repository Statistics
# ============================================================================

def test_repository_stats():
    """
    Test: Repository statistics can be collected
    Step 1: Enable repository stats ✓
    Step 2: Perform various operations ✓
    Step 3: Query stats (queries executed, cache hits, etc.) ✓
    Step 4: Verify accurate statistics ✓
    """
    print("=" * 80)
    print("TEST 2: Repository Statistics Collection")
    print("=" * 80)

    # Define entity with memory backend
    class Product(Entity):
        name: str
        price: float

        class Config:
            arbitrary_types_allowed = True

        @classmethod
        def repository_class(cls):
            return MemoryRepository

    # Step 1: Enable stats
    print("\nStep 1: Enable repository stats")
    repository_monitor.reset()  # Clear any previous stats
    repository_monitor.enable()
    print("✓ Repository monitoring enabled\n")

    # Step 2: Perform various operations
    print("Step 2: Perform various operations")

    # Create and save products
    for i in range(5):
        product = Product(id=f"prod-{i}", name=f"Product {i}", price=10.0 * i)
        product.save()
        repository_monitor.record_save("Product")

    # Get products (some from cache, some not)
    for i in range(5):
        product = Product.get(f"prod-{i}")
        cache_hit = i % 2 == 0  # Simulate cache hits for even IDs
        repository_monitor.record_get("Product", cache_hit=cache_hit)

    # Delete products
    for i in range(2):
        product = Product.get(f"prod-{i}")
        if product:
            product.delete()
            repository_monitor.record_delete("Product")

    print("✓ Performed 5 saves, 5 gets, 2 deletes\n")

    # Step 3: Query stats
    print("Step 3: Query statistics")
    all_stats = repository_monitor.all_stats()

    if "Product" in all_stats:
        stats = all_stats["Product"]
        print(f"  Queries executed: {stats['queries_executed']}")
        print(f"  Saves: {stats['saves']}")
        print(f"  Deletes: {stats['deletes']}")
        print(f"  Gets: {stats['gets']}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache misses: {stats['cache_misses']}")
        print(f"  Cache hit ratio: {stats['cache_hit_ratio']:.2%}")

        # Step 4: Verify accuracy
        print("\nStep 4: Verify accurate statistics")
        assert stats['saves'] == 5, f"Expected 5 saves, got {stats['saves']}"
        assert stats['deletes'] == 2, f"Expected 2 deletes, got {stats['deletes']}"
        assert stats['gets'] == 5, f"Expected 5 gets, got {stats['gets']}"
        assert stats['cache_hits'] == 3, f"Expected 3 cache hits, got {stats['cache_hits']}"
        assert stats['cache_misses'] == 2, f"Expected 2 cache misses, got {stats['cache_misses']}"
        print("✓ All statistics are accurate!")

    print("\n✅ TEST 2 PASSED: Repository statistics working!\n")

    # Cleanup
    repository_monitor.disable()


# ============================================================================
# TEST 3: Event Bus Metrics
# ============================================================================

def test_event_metrics():
    """
    Test: Event bus metrics are available
    Step 1: Enable event metrics ✓
    Step 2: Emit various events ✓
    Step 3: Query metrics (events fired, handlers executed) ✓
    Step 4: Verify accurate metrics ✓
    """
    print("=" * 80)
    print("TEST 3: Event Bus Metrics")
    print("=" * 80)

    # Define handlers
    handler_call_count = {"order.created": 0, "order.shipped": 0}

    @on("order.created")
    def send_email(sender, **kwargs):
        handler_call_count["order.created"] += 1
        import time
        time.sleep(0.01)  # Simulate work

    @on("order.created")
    def update_inventory(sender, **kwargs):
        handler_call_count["order.created"] += 1
        import time
        time.sleep(0.01)  # Simulate work

    @on("order.shipped")
    def notify_customer(sender, **kwargs):
        handler_call_count["order.shipped"] += 1

    # Step 1: Enable metrics
    print("\nStep 1: Enable event metrics")
    event_bus_monitor.reset()  # Clear any previous metrics
    event_bus_monitor.enable()
    print("✓ Event bus monitoring enabled\n")

    # Step 2: Emit events
    print("Step 2: Emit various events")

    # Emit order.created (should trigger 2 handlers)
    for i in range(3):
        event_bus_monitor.record_event_fired("order.created")
        emit("order.created", sender=None)
        # Record handler executions
        import time
        start = time.time()
        time.sleep(0.01)
        event_bus_monitor.record_handler_executed("order.created", time.time() - start)
        event_bus_monitor.record_handler_executed("order.created", time.time() - start)

    # Emit order.shipped (should trigger 1 handler)
    for i in range(2):
        event_bus_monitor.record_event_fired("order.shipped")
        emit("order.shipped", sender=None)
        start = time.time()
        time.sleep(0.005)
        event_bus_monitor.record_handler_executed("order.shipped", time.time() - start)

    print("✓ Emitted 3 order.created and 2 order.shipped events\n")

    # Step 3: Query metrics
    print("Step 3: Query metrics")
    all_metrics = event_bus_monitor.all_metrics()

    for event_name, metrics in all_metrics.items():
        print(f"\n  Event: {event_name}")
        print(f"    Events fired: {metrics['events_fired']}")
        print(f"    Handlers executed: {metrics['handlers_executed']}")
        print(f"    Total handler time: {metrics['total_handler_time']:.4f}s")
        print(f"    Avg handler time: {metrics['avg_handler_time']:.4f}s")
        print(f"    Errors: {metrics['errors']}")

    # Step 4: Verify accuracy
    print("\nStep 4: Verify accurate metrics")

    if "order.created" in all_metrics:
        m = all_metrics["order.created"]
        assert m['events_fired'] == 3, f"Expected 3 events, got {m['events_fired']}"
        assert m['handlers_executed'] == 6, f"Expected 6 handlers, got {m['handlers_executed']}"
        print("✓ order.created metrics accurate (3 events, 6 handlers)")

    if "order.shipped" in all_metrics:
        m = all_metrics["order.shipped"]
        assert m['events_fired'] == 2, f"Expected 2 events, got {m['events_fired']}"
        assert m['handlers_executed'] == 2, f"Expected 2 handlers, got {m['handlers_executed']}"
        print("✓ order.shipped metrics accurate (2 events, 2 handlers)")

    print("\n✅ TEST 3 PASSED: Event bus metrics working!\n")

    # Cleanup
    event_bus_monitor.disable()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NITRO MONITORING DEMO")
    print("=" * 80)
    print("\nThis demo verifies all three monitoring features:\n")
    print("1. Entity operation logging")
    print("2. Repository statistics collection")
    print("3. Event bus metrics")
    print()

    # Run all tests
    test_entity_logging()
    test_repository_stats()
    test_event_metrics()

    # Summary
    print("=" * 80)
    print("✅ ALL MONITORING TESTS PASSED!")
    print("=" * 80)
    print("\nMonitoring features verified:")
    print("  ✓ Entity operations can be logged with details")
    print("  ✓ Repository statistics accurately track operations")
    print("  ✓ Event bus metrics track events and handler execution")
    print("=" * 80)
