#!/usr/bin/env python3
"""Test imports after fix."""

try:
    from nitro import Entity, action
    from nitro.adapters.fastapi import configure_nitro
    print("✅ All imports working!")
    print(f"  - Entity: {Entity}")
    print(f"  - action: {action}")
    print(f"  - configure_nitro: {configure_nitro}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
