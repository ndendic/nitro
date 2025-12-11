"""
Comprehensive feature verification script

This script tests all implemented markdown rendering features
and reports which tests pass.
"""

import sys
sys.path.insert(0, '/home/ndendic/Projects/auto-nitro/nitro/docs_app')

from pathlib import Path
from domain.page_model import DocPage
import mistletoe
from infrastructure.markdown.renderer import NitroRenderer


def test_h1_with_anchor():
    """Test 1: H1 headers with anchor links"""
    print("\nTest 1: H1 headers with anchor links")
    print("=" * 70)

    content = "# Test Header"
    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()
    print(f"  Input: {content}")
    print(f"  Output contains '<h1 id=\"test-header\"': {('<h1 id=\"test-header\"' in html)}")

    # Check for both requirements
    has_h1 = "<h1" in html
    has_id = 'id="test-header"' in html

    passed = has_h1 and has_id
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_h2_with_anchor():
    """Test 2: H2 headers with anchor links"""
    print("\nTest 2: H2 headers with anchor links")
    print("=" * 70)

    content = "## Second Level"
    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()
    print(f"  Input: {content}")

    has_h2 = "<h2" in html
    has_id = 'id="second-level"' in html

    passed = has_h2 and has_id
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_h3_h6_hierarchy():
    """Test 3: H3-H6 with proper hierarchy and unique IDs"""
    print("\nTest 3: H3-H6 headers with hierarchy")
    print("=" * 70)

    content = """### Third Level
#### Fourth Level
##### Fifth Level
###### Sixth Level"""

    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_h3 = "<h3" in html and 'id="third-level"' in html
    has_h4 = "<h4" in html and 'id="fourth-level"' in html
    has_h5 = "<h5" in html and 'id="fifth-level"' in html
    has_h6 = "<h6" in html and 'id="sixth-level"' in html

    passed = has_h3 and has_h4 and has_h5 and has_h6
    print(f"  H3: {'✓' if has_h3 else '✗'}")
    print(f"  H4: {'✓' if has_h4 else '✗'}")
    print(f"  H5: {'✓' if has_h5 else '✗'}")
    print(f"  H6: {'✓' if has_h6 else '✗'}")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_slugified_ids():
    """Test 4: Header IDs are properly slugified"""
    print("\nTest 4: Slugified header IDs")
    print("=" * 70)

    content = "# Hello World! & More?"
    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    # Should be "hello-world-more" (special chars removed)
    has_correct_id = 'id="hello-world-more"' in html

    passed = has_correct_id
    print(f"  Input: {content}")
    print(f"  Expected ID: hello-world-more")
    print(f"  Found: {'✓' if has_correct_id else '✗'}")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_code_block_with_language():
    """Test 5: Code blocks with syntax highlighting"""
    print("\nTest 5: Code blocks with language")
    print("=" * 70)

    content = """```python
print('hello')
```"""

    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_pre = "<pre>" in html
    has_code = "<code" in html
    has_language = "language-python" in html

    passed = has_pre and has_code and has_language
    print(f"  Has <pre>: {'✓' if has_pre else '✗'}")
    print(f"  Has <code>: {'✓' if has_code else '✗'}")
    print(f"  Has language class: {'✓' if has_language else '✗'}")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_inline_code():
    """Test 7: Inline code rendering"""
    print("\nTest 7: Inline code rendering")
    print("=" * 70)

    content = "This is `inline code` in text."
    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_code = "<code" in html
    has_text = "inline code" in html
    # Should not be in a pre block
    is_inline = "<pre>" not in html

    passed = has_code and has_text and is_inline
    print(f"  Has <code>: {'✓' if has_code else '✗'}")
    print(f"  Has text: {'✓' if has_text else '✗'}")
    print(f"  Is inline (no <pre>): {'✓' if is_inline else '✗'}")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_code_block_without_language():
    """Test 8: Code blocks without language specifier"""
    print("\nTest 8: Code blocks without language")
    print("=" * 70)

    content = """```
plain code
```"""

    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_pre = "<pre>" in html
    has_code = "<code" in html
    has_content = "plain code" in html

    passed = has_pre and has_code and has_content
    print(f"  Has <pre>: {'✓' if has_pre else '✗'}")
    print(f"  Has <code>: {'✓' if has_code else '✗'}")
    print(f"  Has content: {'✓' if has_content else '✗'}")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_unordered_list():
    """Test 9: Unordered lists"""
    print("\nTest 9: Unordered lists")
    print("=" * 70)

    content = """- Item 1
- Item 2
- Item 3"""

    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_ul = "<ul" in html
    has_li = "<li>" in html or "<li " in html
    item_count = html.count("<li")

    passed = has_ul and has_li and item_count == 3
    print(f"  Has <ul>: {'✓' if has_ul else '✗'}")
    print(f"  Has <li>: {'✓' if has_li else '✗'}")
    print(f"  Item count: {item_count} (expected 3)")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def test_ordered_list():
    """Test 10: Ordered lists"""
    print("\nTest 10: Ordered lists")
    print("=" * 70)

    content = """1. First
2. Second
3. Third"""

    page = DocPage(
        id="test",
        slug="test",
        title="Test",
        category="Test",
        content=content
    )

    html = page.render()

    has_ol = "<ol" in html
    has_li = "<li>" in html or "<li " in html
    item_count = html.count("<li")

    passed = has_ol and has_li and item_count == 3
    print(f"  Has <ol>: {'✓' if has_ol else '✗'}")
    print(f"  Has <li>: {'✓' if has_li else '✗'}")
    print(f"  Item count: {item_count} (expected 3)")
    print(f"  ✓ PASS" if passed else "  ✗ FAIL")
    return passed


def main():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("FEATURE VERIFICATION TESTS")
    print("=" * 70)

    tests = [
        (test_h1_with_anchor, "Test 1: H1 with anchor"),
        (test_h2_with_anchor, "Test 2: H2 with anchor"),
        (test_h3_h6_hierarchy, "Test 3: H3-H6 hierarchy"),
        (test_slugified_ids, "Test 4: Slugified IDs"),
        (test_code_block_with_language, "Test 5: Code block with language"),
        (test_inline_code, "Test 7: Inline code"),
        (test_code_block_without_language, "Test 8: Code block without language"),
        (test_unordered_list, "Test 9: Unordered list"),
        (test_ordered_list, "Test 10: Ordered list"),
    ]

    results = []
    for test_func, name in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed_count}/{total_count} tests passing")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} tests failed")

    return results


if __name__ == "__main__":
    main()
