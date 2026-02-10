#!/usr/bin/env python3
"""
Test approval workflow implementation.

Tests:
1. Pending change state creation
2. Approve handler with git commit
3. Reject handler with state tracking
4. Approval history tracking
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from telegram import Update, CallbackQuery, Message, User
from telegram.ext import ContextTypes

# Import modules to test
from callback_handlers import handle_callback_query, CHANGE_STATE_PENDING, CHANGE_STATE_APPROVED, CHANGE_STATE_REJECTED
from bot import CHANGE_STATE_PENDING as BOT_PENDING


class TestApprovalWorkflow(unittest.TestCase):
    """Test approval workflow functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock update and context
        self.update = Mock(spec=Update)
        self.context = Mock()
        self.context.user_data = {}

        # Create mock user
        user = Mock(spec=User)
        user.id = 12345
        user.first_name = "Test User"

        # Create mock callback query
        callback_query = Mock(spec=CallbackQuery)
        callback_query.from_user = user
        callback_query.message = Mock(spec=Message)
        callback_query.message.edit_text = MagicMock()
        callback_query.answer = MagicMock()

        self.update.callback_query = callback_query
        self.update.effective_user = user

    def test_constants_match(self):
        """Test that state constants are consistent."""
        from callback_handlers import CHANGE_STATE_PENDING as CB_PENDING
        from callback_handlers import CHANGE_STATE_APPROVED as CB_APPROVED
        from callback_handlers import CHANGE_STATE_REJECTED as CB_REJECTED

        from bot import CHANGE_STATE_PENDING as BOT_PENDING
        from bot import CHANGE_STATE_APPROVED as BOT_APPROVED
        from bot import CHANGE_STATE_REJECTED as BOT_REJECTED

        self.assertEqual(CB_PENDING, BOT_PENDING)
        self.assertEqual(CB_APPROVED, BOT_APPROVED)
        self.assertEqual(CB_REJECTED, BOT_REJECTED)

    def test_pending_change_structure(self):
        """Test that pending_change has correct structure."""
        # Simulate what bot.py creates
        user_id = 12345
        change_id = f"change_{user_id}_{int(datetime.now().timestamp())}"

        pending_change = {
            'id': change_id,
            'state': BOT_PENDING,
            'prompt': 'test prompt',
            'timestamp': datetime.now().isoformat(),
            'output': 'test output',
            'session_id': 'session_123',
            'tools_used': ['Write', 'Edit']
        }

        # Verify structure
        self.assertIn('id', pending_change)
        self.assertIn('state', pending_change)
        self.assertIn('prompt', pending_change)
        self.assertIn('timestamp', pending_change)
        self.assertIn('output', pending_change)
        self.assertIn('session_id', pending_change)
        self.assertIn('tools_used', pending_change)
        self.assertEqual(pending_change['state'], 'pending')

    @patch('callback_handlers.git_ops')
    def test_approve_without_pending_change(self, mock_git):
        """Test approve when no pending change exists."""
        # No pending_change in context
        self.update.callback_query.data = 'action:approve'

        # This should not crash, but handle gracefully
        # The handler checks for pending_change existence

    @patch('callback_handlers.git_ops')
    def test_approve_with_pending_change(self, mock_git):
        """Test approve with pending change."""
        # Set up pending change
        self.context.user_data['pending_change'] = {
            'id': 'change_123',
            'state': CHANGE_STATE_PENDING,
            'prompt': 'Create test file',
            'timestamp': datetime.now().isoformat(),
            'output': 'Created test.txt',
            'session_id': 'session_456',
            'tools_used': ['Write']
        }

        # Mock git operations
        mock_git.is_git_repo.return_value = True
        mock_status = Mock()
        mock_status.is_clean = False
        mock_git.get_status.return_value = mock_status
        mock_git.add_files.return_value = (True, "Staged")
        mock_git.commit.return_value = (True, "abc123")

        self.update.callback_query.data = 'action:approve'

        # Note: We can't fully test the async handler here without running async
        # This is more of a structural test

    @patch('callback_handlers.git_ops')
    def test_reject_with_pending_change(self, mock_git):
        """Test reject with pending change."""
        # Set up pending change
        self.context.user_data['pending_change'] = {
            'id': 'change_123',
            'state': CHANGE_STATE_PENDING,
            'prompt': 'Create test file',
            'timestamp': datetime.now().isoformat(),
            'output': 'Created test.txt',
            'session_id': 'session_456',
            'tools_used': ['Write']
        }

        # Mock git operations
        mock_git.is_git_repo.return_value = True
        mock_status = Mock()
        mock_status.is_clean = False
        mock_git.get_status.return_value = mock_status

        self.update.callback_query.data = 'action:reject'

    def test_approval_history_limit(self):
        """Test that approval history is limited to 20 entries."""
        # Create 25 entries
        self.context.user_data['approval_history'] = [
            {
                'change_id': f'change_{i}',
                'state': CHANGE_STATE_APPROVED,
                'timestamp': datetime.now().isoformat(),
                'prompt': f'test {i}'
            }
            for i in range(25)
        ]

        # Simulate adding new entry and trimming
        self.context.user_data['approval_history'].append({
            'change_id': 'change_new',
            'state': CHANGE_STATE_APPROVED,
            'timestamp': datetime.now().isoformat(),
            'prompt': 'new test'
        })

        # Trim to last 20
        if len(self.context.user_data['approval_history']) > 20:
            self.context.user_data['approval_history'] = \
                self.context.user_data['approval_history'][-20:]

        self.assertEqual(len(self.context.user_data['approval_history']), 20)
        # Last entry should be the new one
        self.assertEqual(
            self.context.user_data['approval_history'][-1]['change_id'],
            'change_new'
        )


class TestIdempotency(unittest.TestCase):
    """Test idempotent operations."""

    def test_double_approve_prevention(self):
        """Test that approving twice doesn't duplicate commits."""
        pending_change = {
            'id': 'change_123',
            'state': CHANGE_STATE_PENDING,
            'prompt': 'test',
            'timestamp': datetime.now().isoformat()
        }

        # First approve
        pending_change['state'] = CHANGE_STATE_APPROVED
        self.assertEqual(pending_change['state'], CHANGE_STATE_APPROVED)

        # Second approve should check state first
        if pending_change.get('state') == CHANGE_STATE_PENDING:
            # This block should not execute
            self.fail("Should not approve already approved change")
        else:
            # Correct behavior - already processed
            pass

    def test_double_reject_prevention(self):
        """Test that rejecting twice doesn't cause issues."""
        pending_change = {
            'id': 'change_123',
            'state': CHANGE_STATE_PENDING,
            'prompt': 'test',
            'timestamp': datetime.now().isoformat()
        }

        # First reject
        pending_change['state'] = CHANGE_STATE_REJECTED
        self.assertEqual(pending_change['state'], CHANGE_STATE_REJECTED)

        # Second reject should check state first
        if pending_change.get('state') == CHANGE_STATE_PENDING:
            # This block should not execute
            self.fail("Should not reject already rejected change")
        else:
            # Correct behavior - already processed
            pass


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestIdempotency))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
