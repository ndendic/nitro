#!/usr/bin/env python3
"""
Manual test script for FastHTML adapter.
Tests JSON responses from auto-routed endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8094"

def test_endpoint(method, path, expected_status=200, data=None, params=None):
    """Test an endpoint and print results."""
    url = f"{BASE_URL}{path}"
    print(f"\n{'='*60}")
    print(f"{method} {path}")
    print(f"URL: {url}")

    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, params=params)
        elif method == "DELETE":
            response = requests.delete(url, params=params)
        else:
            print(f"❌ Unknown method: {method}")
            return False

        print(f"Status: {response.status_code} (expected: {expected_status})")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")

        # Check if JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            print("✅ Response is JSON")
            try:
                json_data = response.json()
                print(f"Response: {json.dumps(json_data, indent=2)}")
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Raw response: {response.text[:200]}")
                return False
        else:
            print(f"⚠️  Response is NOT JSON: {content_type}")
            print(f"Raw response (first 200 chars): {response.text[:200]}")
            return False

        # Check status code
        if response.status_code == expected_status:
            print(f"✅ Status code matches")
            return True
        else:
            print(f"❌ Status code mismatch")
            return False

    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed. Is the server running on port 8093?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("FastHTML Adapter - Manual Test Suite")
    print("="*60)

    tests = []

    # Test 1: GET status
    print("\n📋 Test 1: GET /testcounter/demo/status")
    tests.append(test_endpoint("GET", "/testcounter/demo/status"))

    # Test 2: POST increment (no params)
    print("\n📋 Test 2: POST /testcounter/demo/increment (default amount)")
    tests.append(test_endpoint("POST", "/testcounter/demo/increment"))

    # Test 3: POST increment with query param
    print("\n📋 Test 3: POST /testcounter/demo/increment?amount=5")
    tests.append(test_endpoint("POST", "/testcounter/demo/increment", params={"amount": 5}))

    # Test 4: POST decrement
    print("\n📋 Test 4: POST /testcounter/demo/decrement?amount=2")
    tests.append(test_endpoint("POST", "/testcounter/demo/decrement", params={"amount": 2}))

    # Test 5: GET status again (verify changes persisted)
    print("\n📋 Test 5: GET /testcounter/demo/status (verify persistence)")
    tests.append(test_endpoint("GET", "/testcounter/demo/status"))

    # Test 6: POST reset
    print("\n📋 Test 6: POST /testcounter/demo/reset")
    tests.append(test_endpoint("POST", "/testcounter/demo/reset"))

    # Test 7: GET status after reset
    print("\n📋 Test 7: GET /testcounter/demo/status (after reset)")
    tests.append(test_endpoint("GET", "/testcounter/demo/status"))

    # Test 8: 404 error (non-existent counter)
    print("\n📋 Test 8: GET /testcounter/nonexistent/status (should 404)")
    tests.append(test_endpoint("GET", "/testcounter/nonexistent/status", expected_status=404))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())
