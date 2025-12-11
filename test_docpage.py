"""Test DocPage entity"""

import sys
sys.path.insert(0, '/home/ndendic/Projects/auto-nitro/nitro/docs_app')

from pathlib import Path
from domain.page_model import DocPage

# Test loading from filesystem
test_file = Path("docs_app/content/test/test-page.md")

print("Testing DocPage.load_from_fs()...")
print("=" * 70)

try:
    page = DocPage.load_from_fs(test_file)

    print(f"✓ Page loaded successfully")
    print(f"  Slug: {page.slug}")
    print(f"  Title: {page.title}")
    print(f"  Category: {page.category}")
    print(f"  Order: {page.order}")
    print(f"  Content length: {len(page.content)} characters")
    print()

    print("Testing DocPage.render()...")
    print("=" * 70)

    html = page.render()
    print(f"✓ Page rendered successfully")
    print(f"  HTML length: {len(html)} characters")
    print()

    print("Rendered HTML (first 500 chars):")
    print("-" * 70)
    print(html[:500])
    print()

    # Check for key elements
    checks = [
        ("H1 with ID", 'id="test-header"' in html or 'id=test-header' in html),
        ("H2 with ID", 'id="second-level-header"' in html or 'id=second-level' in html),
        ("Code block", '<pre>' in html and '<code' in html),
        ("Bold text", '<strong' in html),
        ("Italic text", '<em' in html),
        ("List", '<ul' in html or '<li' in html),
        ("Blockquote", 'blockquote' in html.lower()),
        ("Inline code", 'inline' in html or '<code' in html),
    ]

    print("Element checks:")
    print("-" * 70)
    for name, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")

    print()
    print("✓ All tests completed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
