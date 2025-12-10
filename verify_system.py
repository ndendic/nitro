#!/usr/bin/env python3
"""Quick verification that core systems are working."""

import requests
import sys

def test_endpoint(name, url, method="GET", json_data=None):
    """Test an endpoint and report results."""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=5)

        if response.status_code < 400:
            print(f"✓ {name}: {response.status_code}")
            return True
        else:
            print(f"✗ {name}: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"✗ {name}: ERROR - {e}")
        return False

def main():
    """Run verification tests."""
    print("=" * 70)
    print("SYSTEM VERIFICATION - Testing Core Functionality")
    print("=" * 70)

    tests = [
        ("Starlette Counter (8000)", "http://localhost:8000/", "GET", None),
        ("FastAPI Todo (8080) - Status", "http://localhost:8080/counter/demo/status", "GET", None),
        ("FastAPI Todo (8080) - Increment", "http://localhost:8080/counter/demo/increment", "POST", None),
        ("FastAPI Memory (8081)", "http://localhost:8081/counter/test/status", "GET", None),
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test_endpoint(*test):
            passed += 1

    print("=" * 70)
    print(f"RESULTS: {passed}/{total} tests passed ({100*passed//total}%)")
    print("=" * 70)

    if passed == total:
        print("✅ All core systems working correctly!")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
