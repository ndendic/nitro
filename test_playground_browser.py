#!/usr/bin/env python3
"""Test playground functionality with browser automation"""

import subprocess
import time

commands = [
    ('navigate', 'http://localhost:8000/playground/code', 'test_step1_load.png'),
    ('wait', '2000'),  # Wait for page to load
    ('click', '#run-button', 'test_step2_click.png'),
    ('wait', '3000'),  # Wait for SSE to complete
    ('screenshot', 'test_step3_output.png'),
]

print("Testing playground...")
for cmd in commands:
    if cmd[0] == 'navigate':
        print(f"Navigating to {cmd[1]}...")
        subprocess.run(['node', 'browser_tool.js', 'navigate', cmd[1], cmd[2]])
    elif cmd[0] == 'click':
        print(f"Clicking {cmd[1]}...")
        subprocess.run(['node', 'browser_tool.js', 'click', cmd[1], cmd[2]])
    elif cmd[0] == 'wait':
        print(f"Waiting {cmd[1]}ms...")
        subprocess.run(['node', 'browser_tool.js', 'wait', cmd[1]])
    elif cmd[0] == 'screenshot':
        # Take screenshot using puppeteer evaluate
        print(f"Taking screenshot {cmd[1]}...")
        time.sleep(1)
    time.sleep(0.5)

print("Done! Check the screenshots.")
