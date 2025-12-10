#!/usr/bin/env python3
"""Test imports for FastAPI adapter."""

try:
    from nitro.adapters.fastapi import configure_nitro, FastAPIDispatcher
    print("✅ FastAPI adapter imports working")
    print(f"  - configure_nitro: {configure_nitro}")
    print(f"  - FastAPIDispatcher: {FastAPIDispatcher}")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
