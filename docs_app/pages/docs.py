"""Documentation page routes"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

# Add docs_app to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.page_model import DocPage
from rusty_tags import Div, H1, P, Article, Nav, A
from nitro.infrastructure.html import Page

router = APIRouter()


@router.get("/documentation/{slug}", response_class=HTMLResponse)
async def view_doc(slug: str):
    """Display a documentation page by slug"""

    # Try to load the markdown file
    content_path = Path(__file__).parent.parent / "content" / f"{slug}.md"

    # Also check in subdirectories
    if not content_path.exists():
        # Search for the file in content directory
        content_dir = Path(__file__).parent.parent / "content"
        found_files = list(content_dir.rglob(f"{slug}.md"))

        if found_files:
            content_path = found_files[0]
        else:
            raise HTTPException(status_code=404, detail=f"Documentation page '{slug}' not found")

    # Load and render the page
    try:
        doc_page = DocPage.load_from_fs(content_path)
        rendered_html = doc_page.render()

        # Create the page with the docs layout
        page = Page(
            Article(
                rendered_html,
                cls="prose prose-slate dark:prose-invert max-w-none"
            ),
            title=doc_page.title,
            datastar=True,
            highlightjs=True,
            tailwind4=True
        )

        return str(page)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering page: {str(e)}")


@router.get("/documentation", response_class=HTMLResponse)
async def docs_index():
    """Display documentation index page"""

    # List all available documentation pages
    content_dir = Path(__file__).parent.parent / "content"
    md_files = list(content_dir.rglob("*.md"))

    # Group by category
    pages_by_category = {}
    for md_file in md_files:
        try:
            doc_page = DocPage.load_from_fs(md_file)
            if doc_page.category not in pages_by_category:
                pages_by_category[doc_page.category] = []
            pages_by_category[doc_page.category].append(doc_page)
        except Exception as e:
            print(f"Error loading {md_file}: {e}")
            continue

    # Sort pages within each category by order
    for category in pages_by_category:
        pages_by_category[category].sort(key=lambda p: p.order)

    # Build the index page
    sections = []
    for category, pages in sorted(pages_by_category.items()):
        section_items = []

        for page in pages:
            section_items.append(
                Div(
                    A(
                        page.title,
                        href=f"/documentation/{page.slug}",
                        cls="text-lg font-medium text-primary hover:underline"
                    ),
                    cls="mb-2"
                )
            )

        sections.append(
            Div(
                H1(category, cls="text-2xl font-bold mb-4"),
                Div(*section_items),
                cls="mb-8"
            )
        )

    page = Page(
        Article(
            H1("Documentation", cls="text-4xl font-bold mb-8"),
            *sections,
            cls="max-w-4xl mx-auto py-8"
        ),
        title="Nitro Documentation",
        datastar=True,
        tailwind4=True
    )

    return str(page)
