#!/usr/bin/env python3
"""
Automated tests for claude_executor.py module.

Tests cover:
- Command building
- Stream-JSON parsing
- Error handling
- Session resumption
- Response structure
"""

import unittest
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from claude_executor import ClaudeExecutor, ClaudeResponse, CLAUDE_EXECUTABLE


class TestClaudeResponse(unittest.TestCase):
    """Test ClaudeResponse dataclass structure."""

    def test_create_success_response(self):
        """Test creating a successful response."""
        response = ClaudeResponse(
            success=True,
            output="Test output",
            session_id="test-session-123",
            cost_usd=0.029,
            input_tokens=10,
            output_tokens=20,
            duration_ms=1500,
            model="claude-opus-4-6",
            tools_used=["Read", "Write"]
        )

        self.assertTrue(response.success)
        self.assertEqual(response.output, "Test output")
        self.assertEqual(response.session_id, "test-session-123")
        self.assertEqual(response.cost_usd, 0.029)
        self.assertEqual(response.input_tokens, 10)
        self.assertEqual(response.output_tokens, 20)
        self.assertEqual(response.duration_ms, 1500)
        self.assertEqual(response.model, "claude-opus-4-6")
        self.assertEqual(response.tools_used, ["Read", "Write"])
        self.assertIsNone(response.error)

    def test_create_error_response(self):
        """Test creating an error response."""
        response = ClaudeResponse(
            success=False,
            output="",
            error="Test error message"
        )

        self.assertFalse(response.success)
        self.assertEqual(response.output, "")
        self.assertEqual(response.error, "Test error message")
        self.assertIsNone(response.session_id)
        self.assertEqual(response.cost_usd, 0.0)

    def test_default_values(self):
        """Test default values are set correctly."""
        response = ClaudeResponse(success=True, output="test")

        self.assertIsNone(response.error)
        self.assertIsNone(response.session_id)
        self.assertEqual(response.cost_usd, 0.0)
        self.assertEqual(response.input_tokens, 0)
        self.assertEqual(response.output_tokens, 0)
        self.assertEqual(response.duration_ms, 0)
        self.assertIsNone(response.model)
        self.assertEqual(response.tools_used, [])
        self.assertEqual(response.raw_events, [])


class TestClaudeExecutor(unittest.TestCase):
    """Test ClaudeExecutor class methods."""

    def setUp(self):
        """Set up test executor instance."""
        self.executor = ClaudeExecutor(
            workspace=Path("/workspace"),
            timeout=120,
            max_turns=10
        )

    def test_initialization(self):
        """Test executor initializes with correct parameters."""
        self.assertEqual(self.executor.workspace, Path("/workspace"))
        self.assertEqual(self.executor.timeout, 120)
        self.assertEqual(self.executor.max_turns, 10)

    def test_build_command_without_session(self):
        """Test command building without session ID."""
        cmd = self.executor._build_command("What is 2+2?", None)

        expected = [
            CLAUDE_EXECUTABLE,
            "-p", "What is 2+2?",
            "--output-format", "stream-json",
            "--verbose",
            "--max-turns", "10"
        ]

        self.assertEqual(cmd, expected)

    def test_build_command_with_session(self):
        """Test command building with session ID."""
        cmd = self.executor._build_command(
            "Continue the task",
            "session-123"
        )

        expected = [
            CLAUDE_EXECUTABLE,
            "-p", "Continue the task",
            "--output-format", "stream-json",
            "--verbose",
            "--max-turns", "10",
            "--resume", "session-123"
        ]

        self.assertEqual(cmd, expected)

    def test_parse_stream_json_success(self):
        """Test parsing successful stream-json output."""
        # Mock successful subprocess result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"test-123","model":"claude-opus-4-6"}
{"type":"assistant","message":{"content":[{"type":"text","text":"4"}],"usage":{"input_tokens":3,"output_tokens":1}}}
{"type":"result","subtype":"success","total_cost_usd":0.029,"duration_ms":1500,"usage":{"input_tokens":3,"output_tokens":1}}'''
        mock_result.stderr = ""

        response = self.executor._parse_stream_json(mock_result)

        self.assertTrue(response.success)
        self.assertEqual(response.output, "4")
        self.assertEqual(response.session_id, "test-123")
        self.assertEqual(response.model, "claude-opus-4-6")
        self.assertEqual(response.cost_usd, 0.029)
        self.assertEqual(response.duration_ms, 1500)
        self.assertEqual(response.input_tokens, 3)
        self.assertEqual(response.output_tokens, 1)

    def test_parse_stream_json_with_tools(self):
        """Test parsing stream-json with tool usage."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"test-456"}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read"},{"type":"text","text":"File content"},{"type":"tool_use","name":"Write"}]}}
{"type":"result","total_cost_usd":0.05,"duration_ms":2000,"usage":{"input_tokens":10,"output_tokens":20}}'''
        mock_result.stderr = ""

        response = self.executor._parse_stream_json(mock_result)

        self.assertTrue(response.success)
        self.assertEqual(response.output, "File content")
        self.assertIn("Read", response.tools_used)
        self.assertIn("Write", response.tools_used)
        self.assertEqual(len(response.tools_used), 2)

    def test_parse_stream_json_error(self):
        """Test parsing error response."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Not logged in"

        response = self.executor._parse_stream_json(mock_result)

        self.assertFalse(response.success)
        self.assertEqual(response.output, "")
        self.assertEqual(response.error, "Error: Not logged in")

    def test_parse_stream_json_no_output(self):
        """Test parsing response with tools but no text output."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"test-789"}
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash"}]}}
{"type":"result","total_cost_usd":0.01,"duration_ms":500,"usage":{"input_tokens":5,"output_tokens":2}}'''
        mock_result.stderr = ""

        response = self.executor._parse_stream_json(mock_result)

        self.assertTrue(response.success)
        self.assertEqual(response.output, "(Claude completed task with no text output)")
        self.assertIn("Bash", response.tools_used)

    def test_parse_stream_json_malformed_line(self):
        """Test parsing handles malformed JSON lines gracefully."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"test-999"}
MALFORMED JSON LINE
{"type":"assistant","message":{"content":[{"type":"text","text":"Success"}]}}
{"type":"result","total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1}}'''
        mock_result.stderr = ""

        response = self.executor._parse_stream_json(mock_result)

        # Should still succeed despite malformed line
        self.assertTrue(response.success)
        self.assertEqual(response.output, "Success")

    def test_parse_stream_json_multiple_text_blocks(self):
        """Test parsing concatenates multiple text blocks."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"test-multi"}
{"type":"assistant","message":{"content":[{"type":"text","text":"First part. "},{"type":"text","text":"Second part."}]}}
{"type":"result","total_cost_usd":0.01,"usage":{"input_tokens":2,"output_tokens":4}}'''
        mock_result.stderr = ""

        response = self.executor._parse_stream_json(mock_result)

        self.assertTrue(response.success)
        self.assertEqual(response.output, "First part. Second part.")

    @patch('subprocess.run')
    def test_execute_success(self, mock_run):
        """Test successful execution."""
        # Mock subprocess.run to return successful result
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"exec-test"}
{"type":"assistant","message":{"content":[{"type":"text","text":"Test response"}]}}
{"type":"result","total_cost_usd":0.02,"duration_ms":1000,"usage":{"input_tokens":5,"output_tokens":5}}'''
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = self.executor.execute("Test prompt")

        self.assertTrue(response.success)
        self.assertEqual(response.output, "Test response")
        self.assertEqual(response.session_id, "exec-test")

        # Verify subprocess.run was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertEqual(call_args.kwargs['cwd'], str(Path("/workspace")))
        self.assertEqual(call_args.kwargs['timeout'], 120)

    @patch('subprocess.run')
    def test_execute_timeout(self, mock_run):
        """Test execution timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=['claude'],
            timeout=120
        )

        response = self.executor.execute("Test prompt")

        self.assertFalse(response.success)
        self.assertEqual(response.output, "")
        self.assertIn("timeout", response.error.lower())

    @patch('subprocess.run')
    def test_execute_exception(self, mock_run):
        """Test execution exception handling."""
        mock_run.side_effect = Exception("Test exception")

        response = self.executor.execute("Test prompt")

        self.assertFalse(response.success)
        self.assertEqual(response.output, "")
        self.assertIn("Test exception", response.error)

    @patch('subprocess.run')
    def test_execute_with_session_resumption(self, mock_run):
        """Test execution with session resumption."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''{"type":"system","subtype":"init","session_id":"resumed-123"}
{"type":"assistant","message":{"content":[{"type":"text","text":"Resumed"}]}}
{"type":"result","total_cost_usd":0.01,"usage":{"input_tokens":1,"output_tokens":1}}'''
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = self.executor.execute("Continue", session_id="old-session-123")

        self.assertTrue(response.success)

        # Verify --resume flag was included
        call_args = mock_run.call_args[0][0]
        self.assertIn("--resume", call_args)
        self.assertIn("old-session-123", call_args)


class TestIntegration(unittest.TestCase):
    """Integration tests (require actual Claude CLI)."""

    def setUp(self):
        """Check if Claude CLI is available."""
        try:
            result = subprocess.run(
                [CLAUDE_EXECUTABLE, "--version"],
                capture_output=True,
                timeout=5
            )
            self.claude_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.claude_available = False

    def test_real_execution_simple_math(self):
        """Test real execution with simple math (requires Claude CLI)."""
        if not self.claude_available:
            self.skipTest("Claude CLI not available")

        executor = ClaudeExecutor()
        response = executor.execute("What is 3+3?")

        # Should succeed if credentials are configured
        if response.success:
            self.assertIn("6", response.output)
            self.assertIsNotNone(response.session_id)
            self.assertGreater(response.cost_usd, 0)
        else:
            # If not logged in, error should indicate that
            self.assertIn("login", response.error.lower())


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestClaudeResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestClaudeExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
