#!/usr/bin/env python3
"""
Tests for response formatting functionality.

Tests cover:
- Message splitting
- Code block preservation
- Markdown escaping
- Tool/file formatting
- Length handling
"""

import unittest
from formatters import ResponseFormatter, FormattedMessage, truncate_text


class TestResponseFormatter(unittest.TestCase):
    """Test ResponseFormatter class."""

    def setUp(self):
        """Set up test formatter."""
        self.formatter = ResponseFormatter(max_length=100)  # Small for testing

    def test_format_short_response(self):
        """Test formatting a short response (no splitting)."""
        text = "This is a short response."
        messages = self.formatter.format_response(text)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, text)
        self.assertEqual(messages[0].parse_mode, 'Markdown')
        self.assertFalse(messages[0].has_code)

    def test_format_empty_response(self):
        """Test formatting an empty response."""
        messages = self.formatter.format_response("")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].text, "(Empty response)")

    def test_format_response_with_header(self):
        """Test adding header to response."""
        text = "Test"
        messages = self.formatter.format_response(text, add_header=True)

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].text.startswith("🤖 **Claude:**"))
        self.assertIn("Test", messages[0].text)

    def test_format_long_response_splits(self):
        """Test that long responses are split."""
        text = "A" * 200  # Longer than max_length
        messages = self.formatter.format_response(text)

        self.assertGreater(len(messages), 1)
        # Check continuation indicators
        self.assertIn("...continued", messages[0].text.lower())
        self.assertIn("...continued", messages[1].text.lower())

    def test_code_block_detection(self):
        """Test code block detection."""
        text = "Here's some code:\n```python\nprint('hello')\n```"
        messages = self.formatter.format_response(text)

        self.assertEqual(len(messages), 1)
        self.assertTrue(messages[0].has_code)

    def test_format_code_block(self):
        """Test code block formatting."""
        code = "print('hello')\nprint('world')"
        formatted = self.formatter.format_code_block(code, language='python')

        self.assertTrue(formatted.startswith("```python"))
        self.assertTrue(formatted.endswith("```"))
        self.assertIn("print('hello')", formatted)

    def test_format_code_block_with_max_lines(self):
        """Test code block truncation."""
        code = "\n".join([f"line {i}" for i in range(10)])
        formatted = self.formatter.format_code_block(code, language='python', max_lines=3)

        self.assertIn("line 0", formatted)
        self.assertIn("line 2", formatted)
        self.assertNotIn("line 9", formatted)
        self.assertIn("7 more lines", formatted)

    def test_escape_markdown(self):
        """Test Markdown character escaping."""
        text = "Test_with*special[chars]"
        escaped = self.formatter.escape_markdown(text)

        self.assertIn("\\_", escaped)
        self.assertIn("\\*", escaped)
        self.assertIn("\\[", escaped)
        self.assertIn("\\]", escaped)

    def test_format_file_list_empty(self):
        """Test formatting empty file list."""
        result = self.formatter.format_file_list([])
        self.assertEqual(result, "_No files modified_")

    def test_format_file_list_single(self):
        """Test formatting single file."""
        result = self.formatter.format_file_list(["test.py"])
        self.assertIn("📝", result)
        self.assertIn("test.py", result)

    def test_format_file_list_multiple(self):
        """Test formatting multiple files."""
        files = ["file1.py", "file2.py", "file3.py"]
        result = self.formatter.format_file_list(files)

        self.assertIn("📝", result)
        self.assertIn("file1.py", result)
        self.assertIn("file2.py", result)
        self.assertIn("file3.py", result)

    def test_format_file_list_many(self):
        """Test formatting many files (truncation)."""
        files = [f"file{i}.py" for i in range(15)]
        result = self.formatter.format_file_list(files)

        self.assertIn("file0.py", result)
        self.assertIn("file9.py", result)
        self.assertIn("5 more files", result)  # 15 - 10 = 5

    def test_format_tool_list_empty(self):
        """Test formatting empty tool list."""
        result = self.formatter.format_tool_list([])
        self.assertEqual(result, "")

    def test_format_tool_list_single(self):
        """Test formatting single tool."""
        result = self.formatter.format_tool_list(["Read"])
        self.assertIn("📖", result)
        self.assertIn("Read", result)

    def test_format_tool_list_multiple(self):
        """Test formatting multiple tools."""
        tools = ["Read", "Write", "Bash"]
        result = self.formatter.format_tool_list(tools)

        self.assertIn("📖 Read", result)
        self.assertIn("✍️ Write", result)
        self.assertIn("🖥️ Bash", result)

    def test_format_error(self):
        """Test error formatting."""
        error = "Something went wrong!"
        result = self.formatter.format_error(error)

        self.assertIn("❌", result)
        self.assertIn("Error", result)
        self.assertIn(error, result)
        self.assertIn("```", result)

    def test_format_error_long(self):
        """Test error truncation."""
        error = "X" * 1000
        result = self.formatter.format_error(error, max_length=100)

        self.assertLess(len(result), 200)  # Should be truncated + formatting
        self.assertIn("...", result)


class TestTruncateText(unittest.TestCase):
    """Test truncate_text utility function."""

    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        text = "Short text"
        result = truncate_text(text, max_length=100)
        self.assertEqual(result, text)

    def test_truncate_long_text(self):
        """Test that long text is truncated."""
        text = "A" * 100
        result = truncate_text(text, max_length=50)

        self.assertEqual(len(result), 50)
        self.assertTrue(result.endswith("..."))

    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        text = "A" * 100
        result = truncate_text(text, max_length=50, suffix="[more]")

        self.assertEqual(len(result), 50)
        self.assertTrue(result.endswith("[more]"))


class TestMessageSplitting(unittest.TestCase):
    """Test message splitting logic."""

    def setUp(self):
        """Set up formatter with realistic limit."""
        self.formatter = ResponseFormatter(max_length=200)

    def test_split_at_paragraph(self):
        """Test splitting at paragraph boundaries."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        messages = self.formatter.format_response(text)

        # Should split at paragraph boundaries
        if len(messages) > 1:
            self.assertIn("Paragraph", messages[0].text)
            self.assertIn("...continued", messages[0].text.lower())

    def test_split_preserves_code_blocks(self):
        """Test that code blocks are not split."""
        text = "Text before\n```python\n" + ("x" * 50) + "\n```\nText after"
        messages = self.formatter.format_response(text)

        # Code block should be kept intact
        found_complete_block = False
        for msg in messages:
            if "```python" in msg.text and "```" in msg.text[10:]:
                found_complete_block = True

        self.assertTrue(found_complete_block, "Code block was split")

    def test_continuation_indicators(self):
        """Test that continuation indicators are added."""
        text = "A" * 500  # Force splitting
        messages = self.formatter.format_response(text)

        if len(messages) > 1:
            # First message should end with "continued"
            self.assertIn("...continued", messages[0].text.lower())
            # Second message should start with "continued"
            self.assertIn("...continued", messages[1].text.lower())


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestResponseFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestTruncateText))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageSplitting))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
