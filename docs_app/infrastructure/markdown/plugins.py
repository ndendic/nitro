"""
Custom Mistletoe tokens for extended markdown syntax.

Implements:
- Alert blocks with ::: syntax (e.g., ::: warning)
- Demo component blocks with ::demo: syntax (e.g., ::demo:button)
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

    def __init__(self, result):
        """
        Initialize AlertBlock.

        Args:
            result: Tuple of (variant, children_list) from read() method
        """
        if isinstance(result, tuple) and len(result) == 2:
            # Called from read() method
            variant, children = result
            self._alert_type = variant
            self.children = children
        else:
            # Fallback - shouldn't happen but just in case
            self._alert_type = 'info'
            self.children = []

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
            Tuple of (variant, children_list) that will be passed to __init__
        """
        # Get the opening line
        line = next(lines)
        match_obj = cls.start(line)

        if not match_obj:
            return None

        # Extract variant from the opening line
        variant_str = match_obj.group(1).lower()

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

        # Return a tuple that will be passed to __init__
        children_list = list(doc.children) if doc.children else []

        return (variant_str, children_list)


class DemoBlock(BlockToken):
    """
    Custom token for demo component blocks with syntax:

    ::demo:button

    Renders interactive component demos.
    """

    pattern = re.compile(r'^::demo:(\w+)[ ]*$')

    def __init__(self, result):
        """
        Initialize DemoBlock.

        Args:
            result: Component name string from read() method
        """
        if isinstance(result, str):
            self._component_name = result
            self.children = []
        else:
            # Fallback
            self._component_name = 'unknown'
            self.children = []

    @classmethod
    def start(cls, line):
        """
        Check if line starts a demo block.

        Args:
            line: Line to check

        Returns:
            Match object if line starts with ::demo:, None otherwise
        """
        match_obj = cls.pattern.match(line)
        if match_obj:
            return match_obj
        return None

    @classmethod
    def read(cls, lines):
        """
        Read the demo block (single line).

        Args:
            lines: Iterator of remaining lines

        Returns:
            Component name string that will be passed to __init__
        """
        # Get the line
        line = next(lines)
        match_obj = cls.start(line)

        if not match_obj:
            return None

        # Extract component name from the line
        component_name = match_obj.group(1).lower()

        # Return the component name
        return component_name
