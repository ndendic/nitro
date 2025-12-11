
import mistletoe
from mistletoe.span_token import SpanToken, RawText, Emphasis, Strong, InlineCode, Link, Image, EscapeSequence, LineBreak
from mistletoe.block_token import Document, BlockToken, Heading, Quote, CodeFence, ThematicBreak, Paragraph, List, ListItem, Table, TableRow, TableCell
from rusty_tags import (
    Div, H1, H2, H3, H4, H5, H6, P, Ul, Ol, Li, A, Img, Pre, Code as HtmlCode,
    Blockquote, Hr, Table as HtmlTable, Thead, Tbody, Tr, Th, Td, Span, Strong as HtmlStrong, Em as HtmlEm, Br
)
from nitro.infrastructure.html.components.codeblock import CodeBlock
from components.alert import Alert
from infrastructure.markdown.plugins import AlertBlock
from typing import Any, List as TyList

class NitroRenderer(mistletoe.BaseRenderer):
    def __init__(self):
        super().__init__()
        # Mapping for headings
        self._headings = {
            1: H1, 2: H2, 3: H3, 4: H4, 5: H5, 6: H6
        }
        # Override CodeFence to use our custom render_code_fence method
        self.render_map['CodeFence'] = self.render_code_fence
        # Register AlertBlock custom token
        self.render_map['AlertBlock'] = self.render_alert_block

    def render_document(self, token: Document) -> Any:
        return Div(*[self.render(child) for child in token.children], cls="markdown-content space-y-4")

    def render_heading(self, token: Heading) -> Any:
        tag = self._headings.get(token.level, H6)
        # Add anchors for all heading levels (H1-H6)
        attrs = {}

        # Generate ID from content (slugify)
        text_content = "".join([c.content for c in token.children if isinstance(c, RawText)])
        # Simple slugification: lowercase, replace spaces with hyphens, remove special chars
        slug = text_content.lower()
        slug = slug.replace(" ", "-")
        # Remove special characters but keep hyphens
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        # Remove multiple consecutive hyphens
        while "--" in slug:
            slug = slug.replace("--", "-")
        slug = slug.strip("-")

        attrs["id"] = slug

        # Add styling for H2/H3 for table of contents
        if token.level in [2, 3]:
            attrs["cls"] = "scroll-mt-16 group flex items-center gap-2"

        return tag(*[self.render(child) for child in token.children], **attrs)

    def render_paragraph(self, token: Paragraph) -> Any:
        return P(*[self.render(child) for child in token.children], cls="leading-7")

    def render_list(self, token: List) -> Any:
        # token.start is None for unordered lists, a number for ordered lists
        tag = Ol if token.start is not None else Ul
        cls = "list-decimal" if token.start is not None else "list-disc"
        return tag(*[self.render(child) for child in token.children], cls=f"{cls} pl-6 space-y-2")

    def render_list_item(self, token: ListItem) -> Any:
        return Li(*[self.render(child) for child in token.children])

    def render_quote(self, token: Quote) -> Any:
        return Blockquote(
            *[self.render(child) for child in token.children], 
            cls="border-l-4 border-gray-300 pl-4 italic text-gray-700 dark:border-gray-600 dark:text-gray-300"
        )

    def render_code_fence(self, token: CodeFence) -> Any:
        lang = token.language if token.language else ""
        content = token.children[0].content
        return CodeBlock(content, code_cls=f"language-{lang}")

    def render_thematic_break(self, token: ThematicBreak) -> Any:
        return Hr(cls="my-8 border-gray-200 dark:border-gray-800")

    def render_table(self, token: Table) -> Any:
        """
        Render markdown tables with proper Thead/Tbody structure.
        - token.header contains the header row (TableRow)
        - token.children contains the data rows (list of TableRow)
        - token.column_align contains alignment for each column [None, 'left', 'center', 'right']
        """
        # Store column alignment for use in cell rendering
        self._table_column_align = getattr(token, 'column_align', [])
        self._is_header_row = False

        # Render header row if present
        header_content = []
        if hasattr(token, 'header') and token.header:
            self._is_header_row = True
            header_row = self.render(token.header)
            header_content = [Thead(header_row)]
            self._is_header_row = False

        # Render body rows
        body_rows = [self.render(child) for child in token.children]
        body_content = [Tbody(*body_rows)] if body_rows else []

        # Clear alignment info
        self._table_column_align = []

        return Div(
            HtmlTable(*header_content, *body_content, cls="w-full caption-bottom text-sm"),
            cls="my-6 w-full overflow-y-auto"
        )

    def render_table_row(self, token: TableRow) -> Any:
        """Render table row with appropriate class based on whether it's a header or data row."""
        cls = "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted"

        # Track current cell index for alignment
        self._current_cell_index = 0

        result = Tr(*[self.render(child) for child in token.children], cls=cls)

        # Reset cell index
        self._current_cell_index = 0

        return result

    def render_table_cell(self, token: TableCell) -> Any:
        """Render table cell as Th (header) or Td (data) with alignment."""
        # Determine if this is a header cell
        is_header = getattr(self, '_is_header_row', False)
        tag = Th if is_header else Td

        # Get alignment for this column
        cell_index = getattr(self, '_current_cell_index', 0)
        column_align = getattr(self, '_table_column_align', [])
        alignment = column_align[cell_index] if cell_index < len(column_align) else None

        # Increment cell index
        self._current_cell_index = cell_index + 1

        # Build cell classes
        base_cls = "p-4 align-middle [&:has([role=checkbox])]:pr-0"

        # Add alignment class (mistletoe uses: None=left/default, 0=center, 1=right)
        if alignment == 0:  # center
            cls = f"{base_cls} text-center"
        elif alignment == 1:  # right
            cls = f"{base_cls} text-right"
        else:  # None or anything else = left (default)
            cls = f"{base_cls} text-left"

        # Add header-specific styling
        if is_header:
            cls = f"{cls} font-medium"

        return tag(*[self.render(child) for child in token.children], cls=cls)

    def render_strong(self, token: Strong) -> Any:
        return HtmlStrong(*[self.render(child) for child in token.children], cls="font-semibold")

    def render_emphasis(self, token: Emphasis) -> Any:
        return HtmlEm(*[self.render(child) for child in token.children])

    def render_inline_code(self, token: InlineCode) -> Any:
        # Inline code
        content = "".join([self.render(child) for child in token.children]) if hasattr(token, 'children') else token.content
        return HtmlCode(content, cls="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold")

    def render_link(self, token: Link) -> Any:
        """
        Render links with smart routing:
        - Internal links (starting with /) use Datastar navigation
        - External links (http://, https://) open in new tab with security attributes
        - Anchor links (#section) work as regular anchor links
        """
        href = token.target
        attrs = {
            "href": href,
            "cls": "font-medium text-primary underline underline-offset-4 hover:no-underline"
        }

        # Check if it's an external link
        if href.startswith("http://") or href.startswith("https://"):
            # External link - open in new tab with security
            attrs["target"] = "_blank"
            attrs["rel"] = "noopener noreferrer"
        # Check if it's an anchor link (same page)
        elif href.startswith("#"):
            # Anchor link - just use regular href (browser handles smooth scroll)
            pass
        # Otherwise, it's an internal link - use Datastar navigation
        elif href.startswith("/"):
            # Internal link - use Datastar for SPA navigation
            attrs["data-on-click"] = f"$$get('{href}')"

        return A(*[self.render(child) for child in token.children], **attrs)

    def render_image(self, token: Image) -> Any:
        """
        Render images with proper alt text and optional title attribute.
        - Alt text comes from the token's children (the text in brackets)
        - Title attribute comes from token.title (the text in quotes after URL)
        """
        # Extract alt text from children
        alt_text = "".join([self.render(child) for child in token.children]) if token.children else ""

        # Build attributes
        attrs = {
            "src": token.src,
            "alt": alt_text,
            "cls": "rounded-md border"
        }

        # Add title attribute if present (for tooltip)
        if token.title:
            attrs["title"] = token.title

        return Img(**attrs)

    def render_raw_text(self, token: RawText) -> Any:
        return token.content

    def render_line_break(self, token: LineBreak) -> Any:
        return Br()

    def render_escape_sequence(self, token: EscapeSequence) -> Any:
        return token.children[0].content

    def render_alert_block(self, token: AlertBlock) -> Any:
        """
        Render AlertBlock custom token to Alert component.

        Args:
            token: AlertBlock token with variant and content

        Returns:
            Alert component with rendered children
        """
        # Render all children (markdown content inside the alert)
        rendered_children = [self.render(child) for child in token.children]

        # Create Alert component with the appropriate variant
        variant_value = getattr(token, 'alert_type', 'info')
        return Alert(*rendered_children, variant=variant_value)


