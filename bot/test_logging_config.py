#!/usr/bin/env python3
"""
Tests for logging configuration.

Tests cover:
- Logging setup
- Log file creation
- Context logger
- Access logging
"""

import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from logging_config import setup_logging, log_access, ContextLogger, LOG_DIR


class TestLoggingSetup(unittest.TestCase):
    """Test logging configuration."""

    def setUp(self):
        """Set up test environment."""
        # Clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates console handler."""
        setup_logging(level=logging.INFO, log_to_file=False)

        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0)

    def test_setup_logging_with_files(self):
        """Test that log files are created."""
        setup_logging(level=logging.INFO, log_to_file=True)

        # Log directory should exist
        self.assertTrue(LOG_DIR.exists())

    def test_logging_levels(self):
        """Test different logging levels work."""
        setup_logging(level=logging.DEBUG, log_to_file=False)

        logger = logging.getLogger('test')

        # Should not raise
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")


class TestContextLogger(unittest.TestCase):
    """Test ContextLogger class."""

    def setUp(self):
        """Set up test logger."""
        setup_logging(level=logging.DEBUG, log_to_file=False)

    def test_context_logger_creation(self):
        """Test creating logger with context."""
        logger = ContextLogger('test', user_id=123, handler='text')

        self.assertIsNotNone(logger)
        self.assertEqual(logger.context['user_id'], 123)
        self.assertEqual(logger.context['handler'], 'text')

    def test_context_logger_formats_messages(self):
        """Test that context is added to messages."""
        logger = ContextLogger('test', user_id=456)

        # Format a message
        formatted = logger._format_message("Test message")

        self.assertIn("user_id=456", formatted)
        self.assertIn("Test message", formatted)

    def test_context_logger_no_context(self):
        """Test logger without context."""
        logger = ContextLogger('test')

        formatted = logger._format_message("Test message")
        self.assertEqual(formatted, "Test message")

    def test_context_logger_methods(self):
        """Test all logging methods work."""
        logger = ContextLogger('test', user_id=789)

        # Should not raise
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")


class TestAccessLogging(unittest.TestCase):
    """Test access logging functionality."""

    def setUp(self):
        """Set up test environment."""
        setup_logging(level=logging.INFO, log_to_file=True)

    def test_log_access_creates_entry(self):
        """Test that log_access creates log entry."""
        # Should not raise
        log_access(user_id=123, action='voice_message', details='duration=5s')

    def test_log_access_without_details(self):
        """Test log_access with no details."""
        log_access(user_id=456, action='text_message')

    def test_log_access_multiple_calls(self):
        """Test multiple access log calls."""
        log_access(user_id=111, action='start')
        log_access(user_id=222, action='status')
        log_access(user_id=333, action='help')


class TestLogRotation(unittest.TestCase):
    """Test log file rotation."""

    def test_log_directory_created(self):
        """Test that log directory is created."""
        setup_logging(level=logging.INFO, log_to_file=True)

        self.assertTrue(LOG_DIR.exists())
        self.assertTrue(LOG_DIR.is_dir())


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLoggingSetup))
    suite.addTests(loader.loadTestsFromTestCase(TestContextLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestAccessLogging))
    suite.addTests(loader.loadTestsFromTestCase(TestLogRotation))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
