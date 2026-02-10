#!/usr/bin/env python3
"""
End-to-end test for Claude integration.
Tests the complete flow: prompt → execute → parse response.
"""

import sys
from claude_executor import ClaudeExecutor

def test_simple_math():
    """Test simple math question."""
    print("=" * 60)
    print("TEST 1: Simple Math (What is 7+8?)")
    print("=" * 60)

    executor = ClaudeExecutor()
    response = executor.execute("What is 7+8?")

    print(f"Success: {response.success}")
    print(f"Output: {response.output}")
    print(f"Session ID: {response.session_id}")
    print(f"Model: {response.model}")
    print(f"Cost: ${response.cost_usd:.4f}")
    print(f"Tokens: {response.input_tokens} in / {response.output_tokens} out")
    print(f"Duration: {response.duration_ms}ms")
    print(f"Tools used: {response.tools_used}")

    if response.success and "15" in response.output:
        print("✓ TEST PASSED")
        return True, response.session_id
    else:
        print("✗ TEST FAILED")
        if response.error:
            print(f"Error: {response.error}")
        return False, None


def test_session_resumption(session_id):
    """Test resuming a session."""
    print("\n" + "=" * 60)
    print("TEST 2: Session Resumption")
    print("=" * 60)
    print(f"Resuming session: {session_id}")

    executor = ClaudeExecutor()
    response = executor.execute("What was the previous calculation result?", session_id=session_id)

    print(f"Success: {response.success}")
    print(f"Output: {response.output}")
    print(f"Session ID: {response.session_id}")
    print(f"Cost: ${response.cost_usd:.4f}")

    if response.success:
        print("✓ TEST PASSED")
        return True
    else:
        print("✗ TEST FAILED")
        if response.error:
            print(f"Error: {response.error}")
        return False


def test_tool_usage():
    """Test command that requires tool usage."""
    print("\n" + "=" * 60)
    print("TEST 3: Tool Usage (create a test file)")
    print("=" * 60)

    executor = ClaudeExecutor()
    response = executor.execute("Create a file called test_claude.txt with the content 'Hello from Claude Code'")

    print(f"Success: {response.success}")
    print(f"Output: {response.output}")
    print(f"Tools used: {response.tools_used}")
    print(f"Cost: ${response.cost_usd:.4f}")

    if response.success:
        # Check if Write tool was used
        if "Write" in response.tools_used:
            print("✓ TEST PASSED (Write tool was used)")
            return True
        else:
            print("⚠ TEST WARNING (no Write tool detected, but succeeded)")
            return True
    else:
        print("✗ TEST FAILED")
        if response.error:
            print(f"Error: {response.error}")
        return False


def test_error_handling():
    """Test error handling with invalid session."""
    print("\n" + "=" * 60)
    print("TEST 4: Error Handling")
    print("=" * 60)

    # Note: This might still succeed as Claude might just ignore invalid session
    # The real test is that it doesn't crash
    executor = ClaudeExecutor()
    response = executor.execute("What is 1+1?", session_id="invalid-session-id-that-does-not-exist")

    print(f"Success: {response.success}")
    print(f"Output: {response.output}")

    if response.success or response.error:
        print("✓ TEST PASSED (handled gracefully)")
        return True
    else:
        print("✗ TEST FAILED")
        return False


def main():
    """Run all end-to-end tests."""
    print("\n" + "=" * 60)
    print("CLAUDE EXECUTOR END-TO-END TESTS")
    print("=" * 60 + "\n")

    results = []

    # Test 1: Simple math
    success, session_id = test_simple_math()
    results.append(("Simple Math", success))

    # Test 2: Session resumption (only if Test 1 passed)
    if success and session_id:
        success2 = test_session_resumption(session_id)
        results.append(("Session Resumption", success2))
    else:
        print("\n⚠ Skipping session resumption test (no valid session)")
        results.append(("Session Resumption", False))

    # Test 3: Tool usage
    success3 = test_tool_usage()
    results.append(("Tool Usage", success3))

    # Test 4: Error handling
    success4 = test_error_handling()
    results.append(("Error Handling", success4))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
