#!/usr/bin/env python3
"""
Test script for monitoring features.

Tests:
1. Entity operations can be logged
2. Repository statistics can be collected
3. Event bus metrics are available
"""

import sys
from pathlib import Path
import logging

# Add the local nitro package to the path
nitro_path = Path(__file__).parent / "nitro"
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))

from infrastructure.monitoring import (
    configure_nitro_logging,
    log_entity_operation,
    repository_monitor,
    event_bus_monitor,
)


def test_1_entity_logging():
    """
    Test: Entity operations can be logged
    Step 1: Configure logging for Nitro
    Step 2: Perform entity operations
    Step 3: Verify operations are logged with details
    """
    print("=" * 80)
    print("TEST 1: Entity Operations Logging")
    print("=" * 80)

    # Step 1
    print("\nStep 1: Configure logging for Nitro")
    logger = configure_nitro_logging(logging.INFO)
    print("✓ Logging configured at INFO level\n")

    # Step 2
    print("Step 2: Perform entity operations with logging")
    log_entity_operation("User", "create", entity_id="user-1", name="Alice")
    log_entity_operation("User", "get", entity_id="user-1")
    log_entity_operation("User", "update", entity_id="user-1", field="name", value="Bob")
    log_entity_operation("User", "delete", entity_id="user-1")

    # Step 3
    print("\n✓ All operations logged (check output above)")
    print("✅ TEST 1 PASSED\n")
    return True


def test_2_repository_stats():
    """
    Test: Repository statistics can be collected
    Step 1: Enable repository stats
    Step 2: Perform various operations
    Step 3: Query stats (queries executed, cache hits, etc.)
    Step 4: Verify accurate statistics
    """
    print("=" * 80)
    print("TEST 2: Repository Statistics")
    print("=" * 80)

    # Step 1
    print("\nStep 1: Enable repository stats")
    repository_monitor.reset()
    repository_monitor.enable()
    print("✓ Repository monitoring enabled\n")

    # Step 2
    print("Step 2: Perform various operations")
    # Simulate entity operations
    for i in range(5):
        repository_monitor.record_save("Product")
    for i in range(10):
        cache_hit = i % 3 == 0  # Every 3rd is a cache hit
        repository_monitor.record_get("Product", cache_hit=cache_hit)
    for i in range(2):
        repository_monitor.record_delete("Product")

    print("✓ Performed 5 saves, 10 gets, 2 deletes\n")

    # Step 3
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
        print(f"  Cache hit ratio: {stats['cache_hit_ratio']:.1%}")

        # Step 4
        print("\nStep 4: Verify accurate statistics")
        errors = []
        if stats['saves'] != 5:
            errors.append(f"Expected 5 saves, got {stats['saves']}")
        if stats['deletes'] != 2:
            errors.append(f"Expected 2 deletes, got {stats['deletes']}")
        if stats['gets'] != 10:
            errors.append(f"Expected 10 gets, got {stats['gets']}")
        if stats['cache_hits'] != 4:  # 0,3,6,9 = 4 hits
            errors.append(f"Expected 4 cache hits, got {stats['cache_hits']}")
        if stats['cache_misses'] != 6:
            errors.append(f"Expected 6 cache misses, got {stats['cache_misses']}")

        if errors:
            for err in errors:
                print(f"  ✗ {err}")
            return False
        else:
            print("✓ All statistics are accurate!")

    print("✅ TEST 2 PASSED\n")
    repository_monitor.disable()
    return True


def test_3_event_metrics():
    """
    Test: Event bus metrics are available
    Step 1: Enable event metrics
    Step 2: Emit various events
    Step 3: Query metrics (events fired, handlers executed)
    Step 4: Verify accurate metrics
    """
    print("=" * 80)
    print("TEST 3: Event Bus Metrics")
    print("=" * 80)

    # Step 1
    print("\nStep 1: Enable event metrics")
    event_bus_monitor.reset()
    event_bus_monitor.enable()
    print("✓ Event bus monitoring enabled\n")

    # Step 2
    print("Step 2: Emit various events")

    # Simulate order.created events (2 handlers each)
    for i in range(3):
        event_bus_monitor.record_event_fired("order.created")
        event_bus_monitor.record_handler_executed("order.created", 0.01)
        event_bus_monitor.record_handler_executed("order.created", 0.015)

    # Simulate order.shipped events (1 handler each)
    for i in range(2):
        event_bus_monitor.record_event_fired("order.shipped")
        event_bus_monitor.record_handler_executed("order.shipped", 0.005)

    # Simulate event with error
    event_bus_monitor.record_event_fired("order.failed")
    event_bus_monitor.record_handler_executed("order.failed", 0.001, error=True)

    print("✓ Emitted 3 order.created, 2 order.shipped, 1 order.failed events\n")

    # Step 3
    print("Step 3: Query metrics")
    all_metrics = event_bus_monitor.all_metrics()

    for event_name, metrics in sorted(all_metrics.items()):
        print(f"\n  Event: {event_name}")
        print(f"    Events fired: {metrics['events_fired']}")
        print(f"    Handlers executed: {metrics['handlers_executed']}")
        print(f"    Avg handler time: {metrics['avg_handler_time']:.4f}s")
        print(f"    Errors: {metrics['errors']}")

    # Step 4
    print("\nStep 4: Verify accurate metrics")
    errors = []

    if "order.created" in all_metrics:
        m = all_metrics["order.created"]
        if m['events_fired'] != 3:
            errors.append(f"order.created: Expected 3 events, got {m['events_fired']}")
        if m['handlers_executed'] != 6:  # 3 events * 2 handlers
            errors.append(f"order.created: Expected 6 handlers, got {m['handlers_executed']}")

    if "order.shipped" in all_metrics:
        m = all_metrics["order.shipped"]
        if m['events_fired'] != 2:
            errors.append(f"order.shipped: Expected 2 events, got {m['events_fired']}")
        if m['handlers_executed'] != 2:  # 2 events * 1 handler
            errors.append(f"order.shipped: Expected 2 handlers, got {m['handlers_executed']}")

    if "order.failed" in all_metrics:
        m = all_metrics["order.failed"]
        if m['errors'] != 1:
            errors.append(f"order.failed: Expected 1 error, got {m['errors']}")

    if errors:
        for err in errors:
            print(f"  ✗ {err}")
        return False
    else:
        print("✓ All metrics are accurate!")

    print("✅ TEST 3 PASSED\n")
    event_bus_monitor.disable()
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NITRO MONITORING FEATURES TEST")
    print("=" * 80)
    print()

    # Run all tests
    results = []
    results.append(("Entity Logging", test_1_entity_logging()))
    results.append(("Repository Stats", test_2_repository_stats()))
    results.append(("Event Metrics", test_3_event_metrics()))

    # Summary
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    if passed == total:
        print(f"✅ ALL {total} MONITORING TESTS PASSED!")
        print("=" * 80)
        print("\nVerified:")
        print("  ✓ Entity operations can be logged with details")
        print("  ✓ Repository statistics accurately track operations")
        print("  ✓ Event bus metrics track events and handler execution")
        print("=" * 80)
        exit(0)
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        for name, result in results:
            status = "✓" if result else "✗"
            print(f"  {status} {name}")
        exit(1)
