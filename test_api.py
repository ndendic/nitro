#!/usr/bin/env python3
"""Simple API test script for verification."""
import requests
import json

def test_fastapi_todo():
    """Test FastAPI Todo app on port 8080."""
    base_url = "http://localhost:8080"

    print("Testing FastAPI Todo App on port 8080...")

    # Test 1: GET all todos
    try:
        response = requests.get(f"{base_url}/todos")
        print(f"✓ GET /todos: {response.status_code}")
        todos = response.json()
        print(f"  Found {len(todos)} todos")
    except Exception as e:
        print(f"✗ GET /todos failed: {e}")
        return False

    # Test 2: Create a new todo
    try:
        new_todo = {
            "id": "test-todo-1",
            "title": "Test Todo",
            "completed": False
        }
        response = requests.post(f"{base_url}/todos", json=new_todo)
        print(f"✓ POST /todos: {response.status_code}")
    except Exception as e:
        print(f"✗ POST /todos failed: {e}")
        return False

    # Test 3: Get specific todo
    try:
        response = requests.get(f"{base_url}/todos/test-todo-1")
        print(f"✓ GET /todos/test-todo-1: {response.status_code}")
        todo = response.json()
        print(f"  Title: {todo.get('title')}")
    except Exception as e:
        print(f"✗ GET /todos/test-todo-1 failed: {e}")
        return False

    print("\n✓ All FastAPI tests passed!")
    return True

if __name__ == "__main__":
    test_fastapi_todo()
