"""
Deprecation Warning Example

Demonstrates how Nitro handles deprecated features with clear warnings
and migration guidance.

Run: python examples/deprecation_example.py
"""

import warnings
import sys
from pathlib import Path

# Add the local nitro package to the path
nitro_path = Path(__file__).parent.parent
if str(nitro_path) not in sys.path:
    sys.path.insert(0, str(nitro_path))


def deprecated_api(func):
    """
    Decorator to mark functions as deprecated.

    This is an example of how Nitro handles deprecation:
    1. Function still works
    2. DeprecationWarning is raised
    3. Warning includes migration instructions
    """
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"{func.__name__} is deprecated and will be removed in Nitro v2.0.0. "
            f"Use the new API instead. See CHANGELOG.md for migration guide.",
            DeprecationWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper


# Example: Old API (deprecated)
@deprecated_api
def get_entity_signals(entity):
    """
    OLD API: Get entity signals (deprecated).

    This function is deprecated. Use entity.signals property instead.
    """
    return {"count": entity.count}


# Example: New API (current)
class ExampleEntity:
    """Example entity with new signals API."""

    def __init__(self, count: int = 0):
        self.count = count

    @property
    def signals(self):
        """NEW API: Get entity signals via property."""
        return {"count": self.count}


if __name__ == "__main__":
    print("=" * 70)
    print("DEPRECATION WARNING EXAMPLE")
    print("=" * 70)
    print()

    # Create entity
    entity = ExampleEntity(count=42)

    # Test 1: Using deprecated API
    print("Test 1: Using deprecated API")
    print("-" * 70)

    # Enable deprecation warnings
    warnings.filterwarnings("default", category=DeprecationWarning)

    try:
        result = get_entity_signals(entity)
        print(f"✓ Function still works: {result}")
        print(f"✓ DeprecationWarning was raised (check output above)")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # Test 2: Using new API
    print("Test 2: Using new API (recommended)")
    print("-" * 70)
    result = entity.signals
    print(f"✓ New API works: {result}")
    print(f"✓ No warnings raised")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✓ Deprecated features show clear warnings")
    print("✓ Warnings include migration instructions")
    print("✓ Features continue to work during grace period")
    print("✓ See CHANGELOG.md for deprecation policy")
    print()
    print("Migration Path:")
    print("  1. Deprecated feature works with warning (current)")
    print("  2. Grace period: at least 1 major version")
    print("  3. Removal in next major version (e.g., v2.0.0)")
