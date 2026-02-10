#!/usr/bin/env python3
"""
Tests for error handling functionality.

Tests cover:
- Error categorization
- User-friendly error messages
- Error logging
- Error code assignment
"""

import unittest
from error_handlers import (
    BotError, APIError, ExecutionError, InputError,
    ErrorCode, handle_error, safe_execute
)


class TestErrorClasses(unittest.TestCase):
    """Test custom error classes."""

    def test_bot_error_creation(self):
        """Test BotError with all parameters."""
        error = BotError(
            message="Internal error",
            error_code=ErrorCode.UNKNOWN_ERROR,
            user_message="Something went wrong",
            details={'context': 'test'}
        )

        self.assertEqual(str(error), "Internal error")
        self.assertEqual(error.error_code, ErrorCode.UNKNOWN_ERROR)
        self.assertEqual(error.user_message, "Something went wrong")
        self.assertEqual(error.details['context'], 'test')

    def test_bot_error_to_dict(self):
        """Test BotError serialization."""
        error = BotError(
            message="Test error",
            error_code=ErrorCode.TIMEOUT,
            user_message="Operation timed out"
        )

        error_dict = error.to_dict()

        self.assertEqual(error_dict['error_code'], 'timeout')
        self.assertEqual(error_dict['error_message'], 'Test error')
        self.assertEqual(error_dict['user_facing_message'], 'Operation timed out')
        self.assertIn('error_details', error_dict)

    def test_api_error(self):
        """Test APIError subclass."""
        error = APIError(
            message="API failed",
            error_code=ErrorCode.DEEPGRAM_API_ERROR
        )

        self.assertIsInstance(error, BotError)
        self.assertEqual(error.error_code, ErrorCode.DEEPGRAM_API_ERROR)

    def test_execution_error(self):
        """Test ExecutionError subclass."""
        error = ExecutionError(
            message="Execution failed",
            error_code=ErrorCode.CLAUDE_EXECUTION_ERROR
        )

        self.assertIsInstance(error, BotError)
        self.assertEqual(error.error_code, ErrorCode.CLAUDE_EXECUTION_ERROR)


class TestHandleError(unittest.TestCase):
    """Test error handling function."""

    def test_handle_timeout_error(self):
        """Test timeout error handling."""
        error = TimeoutError("Operation timed out")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("timed out", message.lower())
        self.assertIn("⏱️", message)

    def test_handle_permission_error(self):
        """Test permission error handling."""
        error = PermissionError("Access denied")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("permission", message.lower())
        self.assertIn("🔒", message)

    def test_handle_file_not_found_error(self):
        """Test file not found error handling."""
        error = FileNotFoundError("File missing")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("file", message.lower())
        self.assertIn("📁", message)

    def test_handle_rate_limit_error(self):
        """Test rate limit error handling."""
        error = Exception("Rate limit exceeded")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("rate limit", message.lower())
        self.assertIn("⏱️", message)

    def test_handle_auth_error(self):
        """Test authentication error handling."""
        error = Exception("API key invalid")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("authentication", message.lower())
        self.assertIn("🔑", message)

    def test_handle_network_error(self):
        """Test network error handling."""
        error = Exception("Connection failed")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("network", message.lower())
        self.assertIn("🌐", message)

    def test_handle_unknown_error(self):
        """Test unknown error handling."""
        error = Exception("Random unknown error")
        message = handle_error(error, "test_context", user_id=123)

        self.assertIn("unexpected", message.lower())
        self.assertIn("💥", message)

    def test_handle_bot_error(self):
        """Test BotError handling."""
        error = BotError(
            message="Internal error",
            error_code=ErrorCode.TIMEOUT,
            user_message="Custom user message"
        )
        message = handle_error(error, "test_context", user_id=123)

        self.assertEqual(message, "Custom user message")


class TestSafeExecute(unittest.TestCase):
    """Test safe_execute wrapper."""

    def test_safe_execute_success(self):
        """Test successful function execution."""
        def test_func(x, y):
            return x + y

        success, result, error = safe_execute(test_func, 2, 3)

        self.assertTrue(success)
        self.assertEqual(result, 5)
        self.assertIsNone(error)

    def test_safe_execute_failure(self):
        """Test failed function execution."""
        def test_func():
            raise ValueError("Test error")

        success, result, error = safe_execute(test_func)

        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIsNotNone(error)
        self.assertIsInstance(error, str)


class TestErrorCodes(unittest.TestCase):
    """Test error code enumeration."""

    def test_error_codes_exist(self):
        """Test that all expected error codes exist."""
        expected_codes = [
            'TELEGRAM_API_ERROR',
            'DEEPGRAM_API_ERROR',
            'CLAUDE_API_ERROR',
            'UNAUTHORIZED',
            'INVALID_API_KEY',
            'CLAUDE_EXECUTION_ERROR',
            'TIMEOUT',
            'SUBPROCESS_ERROR',
            'FILE_NOT_FOUND',
            'PERMISSION_DENIED',
            'INVALID_INPUT',
            'RATE_LIMITED',
            'UNKNOWN_ERROR'
        ]

        for code in expected_codes:
            self.assertTrue(hasattr(ErrorCode, code), f"Missing error code: {code}")

    def test_error_code_values(self):
        """Test error code string values."""
        self.assertEqual(ErrorCode.TIMEOUT.value, 'timeout')
        self.assertEqual(ErrorCode.UNAUTHORIZED.value, 'unauthorized')
        self.assertEqual(ErrorCode.FILE_NOT_FOUND.value, 'file_not_found')


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestErrorClasses))
    suite.addTests(loader.loadTestsFromTestCase(TestHandleError))
    suite.addTests(loader.loadTestsFromTestCase(TestSafeExecute))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorCodes))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
