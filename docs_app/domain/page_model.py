"""DocPage entity for documentation pages"""

from pathlib import Path
from typing import Optional, List
import mistletoe

from nitro.domain.entities.base_entity import Entity
from infrastructure.markdown.renderer import NitroRenderer
from infrastructure.markdown.plugins import AlertBlock, DemoBlock


class DocPage(Entity, table=True):
    """
    Represents a documentation page with markdown content.

    This entity handles loading markdown files from the filesystem,
    parsing frontmatter, and rendering markdown to Nitro components.
    """

    slug: str  # URL-friendly identifier (primary key)
    title: str  # Page title
    category: str  # Category/section for navigation
    content: str  # Raw markdown content
    order: int = 0  # Order within category for navigation

    @classmethod
    def load_from_fs(cls, path: Path) -> 'DocPage':
        """
        Load a documentation page from a markdown file.

        Args:
            path: Path to the markdown file

        Returns:
            DocPage instance with content loaded

        The slug is derived from the filename.
        Frontmatter is parsed for title, category, and order.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = path.read_text(encoding='utf-8')

        # Parse frontmatter (simple implementation)
        # Format:
        # ---
        # title: Page Title
        # category: Category Name
        # order: 1
        # ---
        # Content here...

        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Parse frontmatter
                fm_lines = parts[1].strip().split('\n')
                for line in fm_lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
                # Get actual content
                content = parts[2].strip()

        # Generate slug from filename
        slug = path.stem  # filename without extension

        # Create instance
        page = cls(
            id=slug,  # Use slug as ID for Entity
            slug=slug,
            title=frontmatter.get('title', slug.replace('-', ' ').title()),
            category=frontmatter.get('category', 'General'),
            content=content,
            order=int(frontmatter.get('order', 0))
        )

        return page

    @classmethod
    def all(cls) -> List['DocPage']:
        """
        Get all documentation pages sorted by order field.

        Returns:
            List of DocPage entities sorted by order (ascending)
        """
        # Use where() with order_by to sort by order field
        from sqlmodel import col
        return cls.where(order_by=col(cls.order))

    def render(self) -> str:
        """
        Render the markdown content to Nitro HTML components.

        Returns:
            Rendered HTML as string
        """
        import mistletoe.block_token as block_token

        # Add custom tokens to _token_types (before Paragraph so they have priority)
        original_token_types = list(block_token._token_types)

        if AlertBlock not in block_token._token_types:
            # Insert before Paragraph (which is last)
            block_token._token_types.insert(-1, AlertBlock)

        if DemoBlock not in block_token._token_types:
            # Insert before Paragraph (which is last)
            block_token._token_types.insert(-1, DemoBlock)

        try:
            with NitroRenderer() as renderer:
                doc = mistletoe.Document(self.content)
                result = renderer.render(doc)
            return str(result)
        finally:
            # Restore original token types
            block_token._token_types[:] = original_token_types
