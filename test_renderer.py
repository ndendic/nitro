"""Test script for markdown rendering"""

import sys
sys.path.insert(0, '/home/ndendic/Projects/auto-nitro/nitro/docs_app')

from infrastructure.markdown.renderer import NitroRenderer
import mistletoe

def test_h1_header():
    """Test H1 header rendering with anchor link"""
    markdown = "# Test Header"

    with NitroRenderer() as renderer:
        result = renderer.render(mistletoe.Document(markdown))

    html_str = str(result)
    print("Test 1: H1 Header Rendering")
    print("=" * 50)
    print(f"Input: {markdown}")
    print(f"Output: {html_str}")
    print()

    # Check for H1 tag
    assert "<h1" in html_str.lower(), "H1 tag not found"

    # Check for id attribute (should be added for H1 too per spec)
    if 'id="test-header"' in html_str or 'id=test-header' in html_str or 'id="' in html_str:
        print("✓ Has ID attribute")
    else:
        print("✗ Missing ID attribute")

    print()
    return html_str

def test_h2_header():
    """Test H2 header rendering with anchor link"""
    markdown = "## Second Level"

    with NitroRenderer() as renderer:
        result = renderer.render(mistletoe.Document(markdown))

    html_str = str(result)
    print("Test 2: H2 Header Rendering")
    print("=" * 50)
    print(f"Input: {markdown}")
    print(f"Output: {html_str}")
    print()

    # Check for H2 tag
    assert "<h2" in html_str.lower(), "H2 tag not found"

    # Check for id="second-level"
    if 'id="second-level"' in html_str or 'id=second-level' in html_str:
        print("✓ Has correct ID attribute")
    else:
        print("✗ Missing or incorrect ID attribute")

    print()
    return html_str

def test_code_block():
    """Test code block rendering"""
    markdown = """```python
print('hello')
```"""

    with NitroRenderer() as renderer:
        result = renderer.render(mistletoe.Document(markdown))

    html_str = str(result)
    print("Test 3: Code Block Rendering")
    print("=" * 50)
    print(f"Input: {markdown}")
    print(f"Output: {html_str}")
    print()

    # Check for CodeBlock or pre tag
    if "codeblock" in html_str.lower() or "<pre" in html_str.lower():
        print("✓ Has code block component")
    else:
        print("✗ Missing code block component")

    # Check for language
    if "python" in html_str.lower():
        print("✓ Language attribute present")
    else:
        print("✗ Missing language attribute")

    print()
    return html_str

if __name__ == "__main__":
    print("Testing NitroRenderer\n")

    try:
        test_h1_header()
        test_h2_header()
        test_code_block()
        print("\n✓ All tests completed!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
