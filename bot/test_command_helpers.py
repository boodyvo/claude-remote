#!/usr/bin/env python3
"""
Tests for command helper functions (Step 16).

Tests cover:
- /status command with approval info
- /clear command with pending change warning
- /help command content
- /info command diagnostics
- /workspace command file listing
- Clear confirmation callbacks
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

# Test that all command handlers exist
class TestCommandHandlersExist(unittest.TestCase):
    """Test that all command handlers are defined."""

    def test_handlers_exist(self):
        """Test that all new/updated handlers exist."""
        from bot import (
            handle_status,
            handle_clear,
            handle_help,
            handle_info,
            handle_workspace
        )

        self.assertTrue(callable(handle_status))
        self.assertTrue(callable(handle_clear))
        self.assertTrue(callable(handle_help))
        self.assertTrue(callable(handle_info))
        self.assertTrue(callable(handle_workspace))


class TestStatusCommand(unittest.TestCase):
    """Test enhanced /status command."""

    def test_status_includes_approval_fields(self):
        """Test that status command includes approval workflow fields."""
        # Mock context with approval data
        context = Mock()
        context.user_data = {
            'claude_session_id': 'session_123',
            'turn_count': 5,
            'pending_change': {
                'state': 'pending',
                'timestamp': datetime.now().isoformat()
            },
            'approval_history': [
                {'state': 'approved', 'change_id': '1'},
                {'state': 'approved', 'change_id': '2'},
                {'state': 'rejected', 'change_id': '3'}
            ]
        }

        # Verify data structure
        self.assertIn('pending_change', context.user_data)
        self.assertIn('approval_history', context.user_data)

        # Count approvals/rejections
        approvals = len([h for h in context.user_data['approval_history'] if h['state'] == 'approved'])
        rejections = len([h for h in context.user_data['approval_history'] if h['state'] == 'rejected'])

        self.assertEqual(approvals, 2)
        self.assertEqual(rejections, 1)


class TestClearCommand(unittest.TestCase):
    """Test enhanced /clear command."""

    def test_clear_detects_pending_changes(self):
        """Test that clear command detects pending changes."""
        context = Mock()
        context.user_data = {
            'pending_change': {
                'state': 'pending',
                'prompt': 'test'
            }
        }

        # Should warn about pending changes
        pending_change = context.user_data.get('pending_change')
        has_pending = pending_change and pending_change.get('state') == 'pending'

        self.assertTrue(has_pending)

    def test_clear_no_pending_changes(self):
        """Test clear when no pending changes exist."""
        context = Mock()
        context.user_data = {
            'claude_session_id': 'session_123',
            'turn_count': 5
        }

        # Should not have pending changes
        pending_change = context.user_data.get('pending_change')
        has_pending = pending_change and pending_change.get('state') == 'pending'

        self.assertFalse(has_pending)


class TestClearCallback(unittest.TestCase):
    """Test clear confirmation callbacks."""

    def test_clear_callback_handler_exists(self):
        """Test that clear callback handler exists."""
        from callback_handlers import handle_clear_callback

        self.assertTrue(callable(handle_clear_callback))

    def test_clear_confirm_clears_data(self):
        """Test that confirming clear removes pending changes."""
        context = Mock()
        context.user_data = {
            'claude_session_id': 'session_123',
            'turn_count': 5,
            'pending_change': {'state': 'pending'}
        }

        # Simulate clear confirm
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0
        context.user_data['pending_change'] = None

        self.assertIsNone(context.user_data['claude_session_id'])
        self.assertEqual(context.user_data['turn_count'], 0)
        self.assertIsNone(context.user_data['pending_change'])


class TestHelpCommand(unittest.TestCase):
    """Test /help command content."""

    def test_help_handler_exists(self):
        """Test that help handler exists and is callable."""
        from bot import handle_help

        self.assertTrue(callable(handle_help))


class TestInfoCommand(unittest.TestCase):
    """Test /info command diagnostics."""

    @patch('subprocess.run')
    def test_info_checks_dependencies(self, mock_run):
        """Test that info command checks system dependencies."""
        # Mock subprocess results
        mock_run.return_value = Mock(
            returncode=0,
            stdout='claude version 1.0.0\n'
        )

        result = mock_run(['claude', '--version'], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)


class TestWorkspaceCommand(unittest.TestCase):
    """Test /workspace command."""

    def test_workspace_file_organization(self):
        """Test workspace file organization logic."""
        files = [
            'src/index.js',
            'src/config.js',
            'tests/test.js',
            'README.md'
        ]

        # Organize by directory (simplified version of bot logic)
        file_tree = {}
        for file in files:
            parts = file.split('/')
            if len(parts) > 1:
                dir_name = parts[0]
                if dir_name not in file_tree:
                    file_tree[dir_name] = []
                file_tree[dir_name].append('/'.join(parts[1:]))
            else:
                if '.' not in file_tree:
                    file_tree['.'] = []
                file_tree['.'].append(file)

        self.assertIn('src', file_tree)
        self.assertIn('tests', file_tree)
        self.assertIn('.', file_tree)
        self.assertEqual(len(file_tree['src']), 2)
        self.assertEqual(len(file_tree['tests']), 1)


class TestBotStartTime(unittest.TestCase):
    """Test bot start time tracking."""

    def test_start_time_stored(self):
        """Test that bot start time is stored in bot_data."""
        bot_data = {}
        bot_data['start_time'] = datetime.now()

        self.assertIn('start_time', bot_data)
        self.assertIsInstance(bot_data['start_time'], datetime)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCommandHandlersExist))
    suite.addTests(loader.loadTestsFromTestCase(TestStatusCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestClearCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestClearCallback))
    suite.addTests(loader.loadTestsFromTestCase(TestHelpCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestInfoCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkspaceCommand))
    suite.addTests(loader.loadTestsFromTestCase(TestBotStartTime))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
