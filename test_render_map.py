"""Check the render_map"""

import sys
sys.path.insert(0, '/home/ndendic/Projects/auto-nitro/nitro/docs_app')

from infrastructure.markdown.renderer import NitroRenderer

renderer = NitroRenderer()
print("Render map keys:")
for key in sorted(renderer.render_map.keys()):
    print(f"  {key}")

print("\nLooking for code_fence...")
if 'CodeFence' in renderer.render_map:
    print(f"  ✓ Found: {renderer.render_map['CodeFence']}")
else:
    print("  ✗ Not found")
