#!/usr/bin/env python3
"""Test the counter app endpoints using HTTP requests."""

import sys
import time
import subprocess
from pathlib import Path

# Add nitro to path
sys.path.insert(0, str(Path(__file__).parent))

import requests

def test_counter_app():
    """Test counter app endpoints."""
    base_url = "http://localhost:8090"

    print("Testing Counter App Endpoints")
    print("=" * 50)

    # Test 1: OpenAPI docs
    print("\n1. Testing OpenAPI docs at /docs")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   Status: {response.status_code}")
        assert response.status_code == 200, "Docs should return 200"
        print("   ✓ OpenAPI docs accessible")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test 2: Create counter via increment
    print("\n2. Testing POST /counter/demo/increment?amount=5")
    try:
        response = requests.post(f"{base_url}/counter/demo/increment?amount=5")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        assert response.status_code == 200, "Increment should return 200"
        data = response.json()
        assert "count" in data, "Response should contain count"
        print(f"   ✓ Counter incremented to {data['count']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test 3: Decrement
    print("\n3. Testing POST /counter/demo/decrement?amount=1")
    try:
        response = requests.post(f"{base_url}/counter/demo/decrement?amount=1")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        assert response.status_code == 200, "Decrement should return 200"
        print("   ✓ Counter decremented")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test 4: Status
    print("\n4. Testing GET /counter/demo/status")
    try:
        response = requests.get(f"{base_url}/counter/demo/status")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        assert response.status_code == 200, "Status should return 200"
        print("   ✓ Status retrieved")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Test 5: Reset
    print("\n5. Testing POST /counter/demo/reset")
    try:
        response = requests.post(f"{base_url}/counter/demo/reset")
        print(f"   Status: {response.status_code}")
        print(f"   Body: {response.json()}")
        assert response.status_code == 200, "Reset should return 200"
        data = response.json()
        assert data["count"] == 0, "Count should be 0 after reset"
        print("   ✓ Counter reset to 0")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n" + "=" * 50)
    print("✓ All tests passed!")
    return True

if __name__ == "__main__":
    # Give server time to start if just launched
    print("Waiting for server to be ready...")
    time.sleep(2)

    success = test_counter_app()
    sys.exit(0 if success else 1)
