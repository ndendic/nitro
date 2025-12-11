"""
Custom Mistletoe tokens for extended markdown syntax.

Implements:
- Alert blocks with ::: syntax (e.g., ::: warning)
"""

import re
from mistletoe.block_token import BlockToken


class AlertBlock(BlockToken):
    """
    Custom token for alert blocks with syntax:

    ::: warning
    This is a warning message
    :::

    Supports variants: info, warning, danger, tip
    """

    pattern = re.compile(r'^:::[ ]*(\w+)[ ]*$')

    def __init__(self, tokenize_func=None):
        """
        Initialize AlertBlock. This is called by mistletoe's tokenizer.
        The actual initialization is done in read().
        """
        # Don't call super().__init__() - we handle everything in read()
        pass

    @classmethod
    def start(cls, line):
        """
        Check if line starts an alert block.

        Args:
            line: Line to check

        Returns:
            Match object if line starts with :::, None otherwise
        """
        match_obj = cls.pattern.match(line)
        if match_obj:
            return match_obj
        return None

    @classmethod
    def read(cls, lines):
        """
        Read the alert block content until closing :::.

        Args:
            lines: Iterator of remaining lines

        Returns:
            AlertBlock instance
        """
        # Get the opening line
        line = next(lines)
        match_obj = cls.start(line)

        if not match_obj:
            return None

        # Extract variant from the opening line
        variant_str = match_obj.group(1).lower()
        print(f"DEBUG: Extracted variant: {variant_str!r} (type: {type(variant_str)})")

        # Read content lines until we hit the closing :::
        content_lines = []
        for line in lines:
            # Check if this is the closing marker
            if line.strip() == ':::':
                break
            content_lines.append(line)

        # Parse the content as markdown to get children
        from mistletoe import Document
        content_text = ''.join(content_lines)  # Preserve line endings for proper parsing
        doc = Document(content_text)

        # Create the token using object.__new__ to bypass __init__
        token = object.__new__(cls)
        token.alert_type = variant_str  # Use alert_type instead of variant to avoid conflicts
        token.children = doc.children if doc.children else []
        token.line_number = 1

        return token
