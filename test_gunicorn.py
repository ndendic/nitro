#!/usr/bin/env python3
"""
Test that Nitro apps can run with Gunicorn.
"""
import subprocess
import time
import sys

print("Testing Gunicorn compatibility with Nitro...")
print("=" * 80)

# Try to start gunicorn with the FastAPI example
print("\nStarting Gunicorn with Nitro FastAPI app on port 9999...")
print("Command: gunicorn examples.fastapi_todo_app:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9999")

try:
    # Start gunicorn process
    proc = subprocess.Popen(
        [
            "gunicorn",
            "examples.fastapi_todo_app:app",
            "--workers", "1",
            "--worker-class", "uvicorn.workers.UvicornWorker",
            "--bind", "0.0.0.0:9999"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait a few seconds for startup
    print("Waiting for server to start...")
    time.sleep(3)

    # Check if process is still running
    if proc.poll() is None:
        print("✅ SUCCESS: Gunicorn started successfully with Nitro app")
        print(f"   Process ID: {proc.pid}")
        print(f"   Server running on http://0.0.0.0:9999")

        # Kill the process
        proc.terminate()
        proc.wait(timeout=5)
        print("   Test server stopped.")
        sys.exit(0)
    else:
        # Process exited
        stdout, stderr = proc.communicate()
        print("❌ FAILED: Gunicorn process exited")
        print(f"\nStdout:\n{stdout}")
        print(f"\nStderr:\n{stderr}")
        sys.exit(1)

except FileNotFoundError:
    print("❌ FAILED: Gunicorn not found")
    sys.exit(1)
except Exception as e:
    print(f"❌ FAILED: {e}")
    if 'proc' in locals():
        try:
            proc.terminate()
        except:
            pass
    sys.exit(1)
