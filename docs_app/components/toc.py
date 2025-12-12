"""Table of Contents component"""

from rusty_tags import Nav, Div, Span, Ul, Li, A
from typing import List, Tuple


def TableOfContents(headers: List[Tuple[str, str, int]]):
    """
    Generate table of contents from page headers.

    Args:
        headers: List of (title, anchor_id, level) tuples
                 level: 2 for H2, 3 for H3, etc.

    Returns:
        Table of contents navigation component with scroll spy

    Example:
        TableOfContents([
            ("Introduction", "introduction", 2),
            ("Getting Started", "getting-started", 3),
            ("Advanced Usage", "advanced-usage", 2)
        ])
    """

    if not headers:
        return Div()  # Empty if no headers

    items = []

    for title, anchor_id, level in headers:
        # Calculate indentation based on level (H2 = 0, H3 = 1)
        indent_class = ""
        if level == 3:
            indent_class = "pl-4"
        elif level > 3:
            indent_class = f"pl-{(level - 2) * 4}"

        items.append(
            Li(
                A(
                    title,
                    href=f"#{anchor_id}",
                    cls=f"block py-1 text-sm text-muted-foreground hover:text-foreground transition-colors {indent_class}",
                    data_toc_link=anchor_id
                ),
                cls="toc-item"
            )
        )

    # Add smooth scroll CSS and scroll spy script
    scroll_behavior_styles = """
    <style>
    html {
        scroll-behavior: smooth;
    }
    </style>
    """

    scroll_spy_script = """
    <script>
    (function() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const id = entry.target.getAttribute('id');
                const tocLink = document.querySelector(`[data-toc-link="${id}"]`);

                if (tocLink) {
                    if (entry.isIntersecting) {
                        // Remove active class from all links
                        document.querySelectorAll('[data-toc-link]').forEach(link => {
                            link.classList.remove('text-primary', 'font-medium');
                            link.classList.add('text-muted-foreground');
                        });

                        // Add active class to current link
                        tocLink.classList.remove('text-muted-foreground');
                        tocLink.classList.add('text-primary', 'font-medium');
                    }
                }
            });
        }, {
            rootMargin: '-100px 0px -66%',
            threshold: 0
        });

        // Observe all headers with IDs
        document.querySelectorAll('h2[id], h3[id]').forEach(header => {
            observer.observe(header);
        });

        // Update URL hash on TOC link click
        document.querySelectorAll('[data-toc-link]').forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('#')) {
                    // Update URL hash
                    history.pushState(null, null, href);
                }
            });
        });
    })();
    </script>
    """

    return Div(
        Nav(
            Div(
                Span("On this page", cls="text-sm font-semibold mb-2 block"),
                Ul(*items, cls="space-y-1"),
            ),
            aria_label="Table of contents",
            cls="toc-nav sticky top-22 space-y-2 [&_ul]:m-0 [&_ul]:list-none [&_ul_ul]:pl-4 [&_li]:mt-0 [&_li]:pt-2 [&_a]:inline-block [&_a]:no-underline [&_a]:transition-colors [&_a]:hover:text-foreground [&_a]:text-muted-foreground"
        ),
        Div(scroll_behavior_styles),  # Include smooth scroll CSS
        Div(scroll_spy_script),  # Include scroll spy script
        cls="hidden sticky top-6 xl:block w-64 shrink-0"
    )
