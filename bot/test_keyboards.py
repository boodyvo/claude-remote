#!/usr/bin/env python3
"""
Tests for keyboard layouts.

Tests cover:
- Keyboard creation
- Button configurations
- Callback data format
"""

import unittest
from keyboards import KeyboardBuilder


class TestKeyboardBuilder(unittest.TestCase):
    """Test keyboard builder functionality."""

    def setUp(self):
        """Set up keyboard builder."""
        self.kb = KeyboardBuilder()

    def test_main_actions_with_changes(self):
        """Test main actions keyboard with changes."""
        keyboard = self.kb.main_actions(has_changes=True, session_active=True)

        self.assertIsNotNone(keyboard)
        self.assertIsNotNone(keyboard.inline_keyboard)

        # Should have 3 rows
        self.assertEqual(len(keyboard.inline_keyboard), 3)

        # First row should have Approve/Reject
        first_row = keyboard.inline_keyboard[0]
        self.assertEqual(len(first_row), 2)
        self.assertIn("Approve", first_row[0].text)
        self.assertIn("Reject", first_row[1].text)
        self.assertEqual(first_row[0].callback_data, 'action:approve')
        self.assertEqual(first_row[1].callback_data, 'action:reject')

    def test_main_actions_without_changes(self):
        """Test main actions keyboard without changes."""
        keyboard = self.kb.main_actions(has_changes=False, session_active=True)

        self.assertIsNotNone(keyboard)

        # Should have 2 rows (no approve/reject)
        self.assertEqual(len(keyboard.inline_keyboard), 2)

        # First row should be git buttons
        first_row = keyboard.inline_keyboard[0]
        self.assertIn("Diff", first_row[0].text)
        self.assertIn("Status", first_row[1].text)

    def test_confirmation_keyboard(self):
        """Test confirmation keyboard."""
        keyboard = self.kb.confirmation('test_action')

        self.assertIsNotNone(keyboard)
        self.assertEqual(len(keyboard.inline_keyboard), 1)

        # Should have Confirm and Cancel
        buttons = keyboard.inline_keyboard[0]
        self.assertEqual(len(buttons), 2)
        self.assertIn("Confirm", buttons[0].text)
        self.assertIn("Cancel", buttons[1].text)
        self.assertEqual(buttons[0].callback_data, 'confirm:test_action')
        self.assertEqual(buttons[1].callback_data, 'cancel:test_action')

    def test_session_management_keyboard(self):
        """Test session management keyboard."""
        keyboard = self.kb.session_management()

        self.assertIsNotNone(keyboard)
        self.assertEqual(len(keyboard.inline_keyboard), 2)

        # First row: New Session, List Sessions
        first_row = keyboard.inline_keyboard[0]
        self.assertEqual(len(first_row), 2)
        self.assertIn("New Session", first_row[0].text)
        self.assertEqual(first_row[0].callback_data, 'session:new')

        # Second row: Clean, Info
        second_row = keyboard.inline_keyboard[1]
        self.assertEqual(len(second_row), 2)
        self.assertIn("Clean", second_row[0].text)
        self.assertEqual(second_row[0].callback_data, 'session:clean')

    def test_git_actions_keyboard(self):
        """Test git actions keyboard."""
        keyboard = self.kb.git_actions()

        self.assertIsNotNone(keyboard)
        self.assertEqual(len(keyboard.inline_keyboard), 3)

        # First row: Diff, Status
        first_row = keyboard.inline_keyboard[0]
        self.assertEqual(len(first_row), 2)
        self.assertEqual(first_row[0].callback_data, 'git:diff')
        self.assertEqual(first_row[1].callback_data, 'git:status')

        # Second row: Log, Branches
        second_row = keyboard.inline_keyboard[1]
        self.assertEqual(len(second_row), 2)
        self.assertEqual(second_row[0].callback_data, 'git:log')
        self.assertEqual(second_row[1].callback_data, 'git:branches')

        # Third row: Back
        third_row = keyboard.inline_keyboard[2]
        self.assertEqual(len(third_row), 1)
        self.assertEqual(third_row[0].callback_data, 'action:back')

    def test_close_button(self):
        """Test close button keyboard."""
        keyboard = self.kb.close_button()

        self.assertIsNotNone(keyboard)
        self.assertEqual(len(keyboard.inline_keyboard), 1)

        button = keyboard.inline_keyboard[0][0]
        self.assertIn("Dismiss", button.text)
        self.assertEqual(button.callback_data, 'action:dismiss')

    def test_pagination_first_page(self):
        """Test pagination on first page."""
        keyboard = self.kb.pagination(0, 5, 'sessions')

        self.assertIsNotNone(keyboard)

        # Navigation row
        nav_row = keyboard.inline_keyboard[0]

        # First page: should have page indicator and Next button
        self.assertGreaterEqual(len(nav_row), 2)

        # Check for page indicator
        page_indicator = next((btn for btn in nav_row if '1/5' in btn.text), None)
        self.assertIsNotNone(page_indicator)

        # Check for Next button
        next_button = next((btn for btn in nav_row if 'Next' in btn.text), None)
        self.assertIsNotNone(next_button)
        self.assertEqual(next_button.callback_data, 'page:sessions:1')

    def test_pagination_middle_page(self):
        """Test pagination on middle page."""
        keyboard = self.kb.pagination(2, 5, 'sessions')

        nav_row = keyboard.inline_keyboard[0]

        # Middle page: should have Previous, page indicator, and Next
        self.assertEqual(len(nav_row), 3)

        # Check for Previous button
        prev_button = next((btn for btn in nav_row if 'Previous' in btn.text), None)
        self.assertIsNotNone(prev_button)
        self.assertEqual(prev_button.callback_data, 'page:sessions:1')

        # Check for page indicator
        page_indicator = next((btn for btn in nav_row if '3/5' in btn.text), None)
        self.assertIsNotNone(page_indicator)

        # Check for Next button
        next_button = next((btn for btn in nav_row if 'Next' in btn.text), None)
        self.assertIsNotNone(next_button)
        self.assertEqual(next_button.callback_data, 'page:sessions:3')

    def test_pagination_last_page(self):
        """Test pagination on last page."""
        keyboard = self.kb.pagination(4, 5, 'sessions')

        nav_row = keyboard.inline_keyboard[0]

        # Last page: should have Previous and page indicator only
        self.assertGreaterEqual(len(nav_row), 2)

        # Check for Previous button
        prev_button = next((btn for btn in nav_row if 'Previous' in btn.text), None)
        self.assertIsNotNone(prev_button)

        # Check for page indicator
        page_indicator = next((btn for btn in nav_row if '5/5' in btn.text), None)
        self.assertIsNotNone(page_indicator)

        # No Next button on last page
        next_button = next((btn for btn in nav_row if 'Next' in btn.text), None)
        self.assertIsNone(next_button)


class TestCallbackDataFormat(unittest.TestCase):
    """Test callback data format consistency."""

    def setUp(self):
        """Set up keyboard builder."""
        self.kb = KeyboardBuilder()

    def test_action_callbacks_format(self):
        """Test that action callbacks follow 'action:name' format."""
        keyboard = self.kb.main_actions()

        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data.startswith('action:'):
                    # Should have category and action
                    parts = button.callback_data.split(':')
                    self.assertGreaterEqual(len(parts), 2)
                    self.assertEqual(parts[0], 'action')

    def test_git_callbacks_format(self):
        """Test that git callbacks follow 'git:action' format."""
        keyboard = self.kb.git_actions()

        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data.startswith('git:'):
                    parts = button.callback_data.split(':')
                    self.assertEqual(len(parts), 2)
                    self.assertEqual(parts[0], 'git')

    def test_session_callbacks_format(self):
        """Test that session callbacks follow 'session:action' format."""
        keyboard = self.kb.session_management()

        for row in keyboard.inline_keyboard:
            for button in row:
                if button.callback_data.startswith('session:'):
                    parts = button.callback_data.split(':')
                    self.assertEqual(len(parts), 2)
                    self.assertEqual(parts[0], 'session')


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKeyboardBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestCallbackDataFormat))

    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)
