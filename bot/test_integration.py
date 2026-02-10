#!/usr/bin/env python3
"""
Integration tests for Claude Code execution.

Tests the actual workflow:
1. First execution (no session) -> should create new session
2. Second execution (with session) -> should resume session
3. Invalid session ID -> should handle gracefully
"""

import unittest
import re
from claude_executor import ClaudeExecutor


class TestClaudeIntegration(unittest.TestCase):
    """Integration tests with real Claude CLI."""

    def setUp(self):
        """Set up executor."""
        self.executor = ClaudeExecutor()

    def test_first_execution_creates_session(self):
        """Test that first execution creates a new session with UUID."""
        # First execution WITHOUT session_id
        response = self.executor.execute("What is 2+2?", session_id=None)

        # Should succeed
        self.assertTrue(response.success, f"Execution failed: {response.error}")

        # Should return a session_id
        self.assertIsNotNone(response.session_id, "No session_id returned")

        # Session ID should be a UUID format (8-4-4-4-12 hex digits)
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        self.assertIsNotNone(
            re.match(uuid_pattern, response.session_id),
            f"Session ID '{response.session_id}' is not a valid UUID"
        )

        # Should have output
        self.assertIn("4", response.output)

        print(f"✓ First execution created session: {response.session_id}")

    def test_second_execution_resumes_session(self):
        """Test that second execution can resume the session."""
        # First execution
        response1 = self.executor.execute("Remember the number 42", session_id=None)
        self.assertTrue(response1.success, f"First execution failed: {response1.error}")

        session_id = response1.session_id
        self.assertIsNotNone(session_id, "No session_id from first execution")

        print(f"✓ First execution session: {session_id}")

        # Second execution WITH session_id
        response2 = self.executor.execute(
            "What number did I tell you to remember?",
            session_id=session_id
        )

        # Should succeed
        self.assertTrue(response2.success, f"Second execution failed: {response2.error}")

        # Should remember the number
        self.assertIn("42", response2.output.lower(), "Claude didn't remember the number")

        # Session ID should be the same
        self.assertEqual(response2.session_id, session_id, "Session ID changed unexpectedly")

        print(f"✓ Second execution resumed session: {response2.session_id}")
        print(f"✓ Claude remembered: {response2.output[:100]}")

    def test_invalid_session_id_handled_gracefully(self):
        """Test that invalid session ID is handled gracefully."""
        # Try with a non-UUID session ID (like our old format)
        invalid_session_id = "user_123_abc123"

        response = self.executor.execute("Hello", session_id=invalid_session_id)

        # Should fail gracefully with clear error
        self.assertFalse(response.success, "Should have failed with invalid session ID")
        self.assertIsNotNone(response.error, "Should have error message")
        self.assertIn("session", response.error.lower(), "Error should mention session")

        print(f"✓ Invalid session ID handled: {response.error[:100]}")

    def test_nonexistent_uuid_session_handled(self):
        """Test that non-existent UUID session is handled."""
        # Use a valid UUID format but session doesn't exist
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = self.executor.execute("Hello", session_id=fake_uuid)

        # Should either fail gracefully OR create new session
        # (Claude CLI behavior may vary)
        if not response.success:
            self.assertIsNotNone(response.error)
            print(f"✓ Nonexistent UUID rejected: {response.error[:100]}")
        else:
            print(f"✓ Nonexistent UUID created new session: {response.session_id}")

    def test_session_persistence_across_multiple_turns(self):
        """Test that session persists across multiple turns."""
        # Turn 1
        r1 = self.executor.execute("My name is Alice", session_id=None)
        self.assertTrue(r1.success)
        session_id = r1.session_id

        # Turn 2
        r2 = self.executor.execute("What's my name?", session_id=session_id)
        self.assertTrue(r2.success)
        self.assertIn("alice", r2.output.lower())

        # Turn 3
        r3 = self.executor.execute("What did I tell you in the first message?", session_id=session_id)
        self.assertTrue(r3.success)
        self.assertIn("alice", r3.output.lower())

        print(f"✓ Session persisted across 3 turns")


def run_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestClaudeIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("\n" + "="*60)
    print("INTEGRATION TESTS - Real Claude CLI Execution")
    print("="*60 + "\n")

    result = run_tests()

    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ ALL INTEGRATION TESTS PASSED")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
    print("="*60)

    exit(0 if result.wasSuccessful() else 1)
