#!/usr/bin/env python3
"""
Test script to verify DocPage entity functionality.
Tests: #30-35
"""

import sys
import os
from pathlib import Path

# Add docs_app to path
sys.path.insert(0, str(Path(__file__).parent / 'docs_app'))

from domain.page_model import DocPage


def test_entity_initialization():
    """Test #30: DocPage entity initializes with required fields"""
    print("Test #30: DocPage entity initialization...")

    # Initialize database
    DocPage.repository().init_db()

    # Create entity
    page = DocPage(
        id='test-page',
        slug='test-page',
        title='Test Page',
        category='guide',
        content='# Test Content',
        order=1
    )

    # Verify fields
    assert page.slug == 'test-page'
    assert page.title == 'Test Page'
    assert page.category == 'guide'
    assert page.content == '# Test Content'
    assert page.order == 1

    print("✅ PASS: DocPage initializes correctly")
    return True


def test_load_from_fs():
    """Test #31: DocPage.load_from_fs reads markdown file correctly"""
    print("\nTest #31: DocPage.load_from_fs...")

    # Use existing test-page.md
    test_file = Path(__file__).parent / 'docs_app' / 'content' / 'test' / 'test-page.md'

    if not test_file.exists():
        print(f"❌ FAIL: Test file not found: {test_file}")
        return False

    # Load from filesystem
    page = DocPage.load_from_fs(test_file)

    # Verify metadata from frontmatter
    assert page.slug == 'test-page'
    assert page.title == 'Test Page'
    assert page.category == 'Getting Started'
    assert page.order == 1
    assert len(page.content) > 0
    assert '# Test Header' in page.content

    print("✅ PASS: DocPage.load_from_fs works correctly")
    return True


def test_render():
    """Test #32: DocPage.render() converts markdown to Nitro components"""
    print("\nTest #32: DocPage.render()...")

    page = DocPage(
        id='render-test',
        slug='render-test',
        title='Render Test',
        category='test',
        content='# Hello World\n\nThis is **bold** text.',
        order=1
    )

    # Render
    html = page.render()

    # Verify output
    assert isinstance(html, str)
    assert '<h1' in html
    assert 'Hello World' in html
    assert '<strong' in html or 'bold' in html

    print("✅ PASS: DocPage.render() converts markdown to HTML")
    return True


def test_persistence():
    """Test #33: DocPage entities persist to database"""
    print("\nTest #33: DocPage persistence...")

    # Initialize database
    DocPage.repository().init_db()

    # Create and save
    page = DocPage(
        id='persist-test',
        slug='persist-test',
        title='Persist Test',
        category='test',
        content='# Persistence Test',
        order=1
    )

    result = page.save()
    assert result is True, "Save should return True"

    # Retrieve
    retrieved = DocPage.get('persist-test')
    assert retrieved is not None, "Should retrieve saved page"
    assert retrieved.slug == 'persist-test'
    assert retrieved.title == 'Persist Test'
    assert retrieved.category == 'test'
    assert retrieved.content == '# Persistence Test'
    assert retrieved.order == 1

    print("✅ PASS: DocPage persists to database")
    return True


def test_all_sorted():
    """Test #34: DocPage.all() returns pages sorted by order field"""
    print("\nTest #34: DocPage.all() sorting...")

    # Initialize database
    DocPage.repository().init_db()

    # Create multiple pages with different orders
    pages_data = [
        ('page-3', 'Page 3', 3),
        ('page-1', 'Page 1', 1),
        ('page-2', 'Page 2', 2),
    ]

    for slug, title, order in pages_data:
        page = DocPage(
            id=slug,
            slug=slug,
            title=title,
            category='test',
            content=f'# {title}',
            order=order
        )
        page.save()

    # Get all pages
    all_pages = DocPage.all()

    # Verify sorted by order (ascending)
    test_pages = [p for p in all_pages if p.category == 'test' and p.slug.startswith('page-')]
    assert len(test_pages) >= 3, f"Should have at least 3 test pages, got {len(test_pages)}"

    # Check if sorted (they should be in order 1, 2, 3)
    orders = [p.order for p in test_pages[:3]]
    assert orders == sorted(orders), f"Pages should be sorted by order, got {orders}"

    print("✅ PASS: DocPage.all() returns sorted pages")
    return True


def test_filter():
    """Test #35: DocPage.filter(category='guide') returns filtered results"""
    print("\nTest #35: DocPage.filter()...")

    # Initialize database
    DocPage.repository().init_db()

    # Create pages with different categories
    categories_data = [
        ('guide-1', 'Guide 1', 'guide'),
        ('api-1', 'API 1', 'api'),
        ('tutorial-1', 'Tutorial 1', 'tutorial'),
        ('guide-2', 'Guide 2', 'guide'),
    ]

    for slug, title, category in categories_data:
        page = DocPage(
            id=slug,
            slug=slug,
            title=title,
            category=category,
            content=f'# {title}',
            order=1
        )
        page.save()

    # Filter by category
    guide_pages = DocPage.filter(category='guide')

    # Verify only guide pages returned
    assert len(guide_pages) >= 2, f"Should have at least 2 guide pages, got {len(guide_pages)}"
    for page in guide_pages:
        if page.slug.startswith('guide-') or page.slug.startswith('api-') or page.slug.startswith('tutorial-'):
            assert page.category == 'guide', f"Page {page.slug} should be in guide category"

    print("✅ PASS: DocPage.filter() works correctly")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("DocPage Entity Tests")
    print("=" * 60)

    tests = [
        test_entity_initialization,
        test_load_from_fs,
        test_render,
        test_persistence,
        test_all_sorted,
        test_filter,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ FAIL: {test_func.__name__} - {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
