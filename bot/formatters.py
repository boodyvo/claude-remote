#!/usr/bin/env python3
"""
Response formatting utilities for Telegram bot.
Handles message splitting, code highlighting, and Markdown escaping.
"""

import re
from typing import List, Optional
from dataclasses import dataclass

# Telegram limits
MAX_MESSAGE_LENGTH = 4096
MAX_SAFE_LENGTH = 3900  # Leave room for formatting


@dataclass
class FormattedMessage:
    """A formatted message ready to send."""
    text: str
    parse_mode: str = 'Markdown'
    has_code: bool = False


class ResponseFormatter:
    """Format Claude responses for Telegram."""

    def __init__(self, max_length: int = MAX_SAFE_LENGTH):
        self.max_length = max_length

    def format_response(
        self,
        text: str,
        add_header: bool = False,
        header_text: str = "🤖 **Claude:**\n\n"
    ) -> List[FormattedMessage]:
        """
        Format a response for Telegram, splitting if necessary.

        Args:
            text: Raw response text from Claude
            add_header: Whether to add header to first message
            header_text: Header text to use

        Returns:
            List of FormattedMessage objects
        """
        if not text or not text.strip():
            return [FormattedMessage(
                text="(Empty response)",
                parse_mode='Markdown',
                has_code=False
            )]

        # Add header if requested
        if add_header:
            text = header_text + text

        # Check if response needs splitting
        if len(text) <= self.max_length:
            return [FormattedMessage(
                text=text,
                parse_mode='Markdown',
                has_code='```' in text
            )]

        # Split long response
        return self._split_message(text)

    def _split_message(self, text: str) -> List[FormattedMessage]:
        """
        Split a long message into multiple messages.

        Tries to split at paragraph boundaries, then sentence boundaries,
        then word boundaries. Preserves code blocks.
        """
        messages = []
        remaining = text

        while len(remaining) > self.max_length:
            # Try to find a good split point
            split_point = self._find_split_point(remaining)

            # Extract chunk
            chunk = remaining[:split_point].strip()
            remaining = remaining[split_point:].strip()

            # Add continuation indicator if there's more
            if remaining:
                chunk += "\n\n_(...continued)_"

            messages.append(FormattedMessage(
                text=chunk,
                parse_mode='Markdown',
                has_code='```' in chunk
            ))

        # Add final chunk
        if remaining:
            # Add continuation indicator at start if not first message
            if messages:
                remaining = "_(...continued)_\n\n" + remaining

            messages.append(FormattedMessage(
                text=remaining,
                parse_mode='Markdown',
                has_code='```' in remaining
            ))

        return messages

    def _find_split_point(self, text: str) -> int:
        """
        Find the best point to split a message.

        Priority:
        1. End of code block (after ```)
        2. Double newline (paragraph boundary)
        3. Single newline (line boundary)
        4. Period + space (sentence boundary)
        5. Space (word boundary)
        6. Force split at max_length
        """
        max_search = min(self.max_length, len(text))

        # Check for code blocks - don't split inside them
        code_blocks = list(re.finditer(r'```[\s\S]*?```', text[:max_search + 500]))
        if code_blocks:
            last_block = code_blocks[-1]
            if last_block.end() <= self.max_length:
                # Code block ends before limit, split after it
                return last_block.end()

        # Try paragraph boundary (double newline)
        search_text = text[:max_search]
        para_splits = [m.start() for m in re.finditer(r'\n\n', search_text)]
        if para_splits:
            return para_splits[-1] + 2  # After the double newline

        # Try line boundary (single newline)
        line_splits = [m.start() for m in re.finditer(r'\n', search_text)]
        if line_splits:
            return line_splits[-1] + 1

        # Try sentence boundary
        sentence_splits = [m.start() for m in re.finditer(r'\. ', search_text)]
        if sentence_splits:
            return sentence_splits[-1] + 2  # After period and space

        # Try word boundary
        word_splits = [m.start() for m in re.finditer(r' ', search_text)]
        if word_splits:
            return word_splits[-1] + 1

        # Force split at max_length
        return self.max_length

    def format_code_block(
        self,
        code: str,
        language: str = '',
        max_lines: Optional[int] = None
    ) -> str:
        """
        Format a code block for Telegram.

        Args:
            code: Code content
            language: Programming language for syntax highlighting
            max_lines: Maximum lines to include (rest will be truncated)

        Returns:
            Formatted code block
        """
        if max_lines:
            lines = code.split('\n')
            if len(lines) > max_lines:
                code = '\n'.join(lines[:max_lines])
                code += f"\n... ({len(lines) - max_lines} more lines)"

        return f"```{language}\n{code}\n```"

    def escape_markdown(self, text: str) -> str:
        """
        Escape special Markdown characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        # Characters that need escaping in Markdown
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

        for char in special_chars:
            text = text.replace(char, '\\' + char)

        return text

    def format_file_list(self, files: List[str]) -> str:
        """
        Format a list of files for display.

        Args:
            files: List of file paths

        Returns:
            Formatted file list
        """
        if not files:
            return "_No files modified_"

        if len(files) == 1:
            return f"📝 Modified: `{files[0]}`"

        formatted = "📝 **Modified files:**\n"
        for file in files[:10]:  # Limit to 10 files
            formatted += f"  • `{file}`\n"

        if len(files) > 10:
            formatted += f"  _...and {len(files) - 10} more files_\n"

        return formatted

    def format_tool_list(self, tools: List[str]) -> str:
        """
        Format a list of tools used.

        Args:
            tools: List of tool names

        Returns:
            Formatted tool list
        """
        if not tools:
            return ""

        # Tool emoji mapping
        tool_emojis = {
            'Read': '📖',
            'Write': '✍️',
            'Edit': '✏️',
            'Bash': '🖥️',
            'Glob': '🔍',
            'Grep': '🔎',
            'WebFetch': '🌐',
            'WebSearch': '🔍',
        }

        formatted_tools = []
        for tool in tools:
            emoji = tool_emojis.get(tool, '🔧')
            formatted_tools.append(f"{emoji} {tool}")

        return "  • Tools: " + ", ".join(formatted_tools)

    def format_error(self, error: str, max_length: int = 500) -> str:
        """
        Format an error message.

        Args:
            error: Error message
            max_length: Maximum length for error

        Returns:
            Formatted error message
        """
        if len(error) > max_length:
            error = error[:max_length] + "..."

        return f"❌ **Error:**\n```\n{error}\n```"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
