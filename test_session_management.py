#!/usr/bin/env python3
"""
Automated tests for session management functionality.
Tests session helper functions without requiring manual Telegram interaction.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

# Mock context object that simulates telegram context
class MockContext:
    """Mock Telegram context for testing."""
    def __init__(self):
        self.user_data = {}

def test_session_management():
    """Test all session management functions."""
    print("=" * 70)
    print("Automated Session Management Tests")
    print("=" * 70)

    # Import after path setup
    from bot import (
        initialize_user_data,
        get_or_create_session_id,
        increment_turn_count,
        reset_session,
        get_session_info,
        USER_DATA_SCHEMA
    )

    passed = 0
    failed = 0

    # Test 1: Initialize user data
    print("\nTest 1: Initialize user data with defaults")
    context = MockContext()
    initialize_user_data(context)

    if 'claude_session_id' in context.user_data:
        print("  ✓ PASS: claude_session_id initialized")
        passed += 1
    else:
        print("  ✗ FAIL: claude_session_id not initialized")
        failed += 1

    if context.user_data.get('turn_count') == 0:
        print("  ✓ PASS: turn_count initialized to 0")
        passed += 1
    else:
        print(f"  ✗ FAIL: turn_count is {context.user_data.get('turn_count')}, expected 0")
        failed += 1

    if context.user_data.get('last_active'):
        print(f"  ✓ PASS: last_active timestamp set: {context.user_data.get('last_active')}")
        passed += 1
    else:
        print("  ✗ FAIL: last_active not set")
        failed += 1

    if context.user_data.get('workspace_path') == '/workspace':
        print("  ✓ PASS: workspace_path set to /workspace")
        passed += 1
    else:
        print(f"  ✗ FAIL: workspace_path is {context.user_data.get('workspace_path')}")
        failed += 1

    if 'preferences' in context.user_data:
        print(f"  ✓ PASS: preferences initialized: {context.user_data['preferences']}")
        passed += 1
    else:
        print("  ✗ FAIL: preferences not initialized")
        failed += 1

    # Test 2: Get or create session ID
    print("\nTest 2: Get or create session ID")
    context = MockContext()
    user_id = 123456789

    session_id = get_or_create_session_id(context, user_id)

    if session_id and session_id.startswith(f'user_{user_id}_'):
        print(f"  ✓ PASS: Session ID created with correct format: {session_id}")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session ID format incorrect: {session_id}")
        failed += 1

    if len(session_id.split('_')[-1]) == 8:
        print("  ✓ PASS: UUID portion is 8 characters")
        passed += 1
    else:
        print(f"  ✗ FAIL: UUID portion length is {len(session_id.split('_')[-1])}, expected 8")
        failed += 1

    # Test that session ID is reused
    session_id2 = get_or_create_session_id(context, user_id)
    if session_id == session_id2:
        print("  ✓ PASS: Session ID is reused (not regenerated)")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session ID changed: {session_id} -> {session_id2}")
        failed += 1

    # Test 3: Increment turn count
    print("\nTest 3: Increment turn count")
    context = MockContext()
    initialize_user_data(context)

    turn1 = increment_turn_count(context)
    if turn1 == 1:
        print(f"  ✓ PASS: First increment returns 1")
        passed += 1
    else:
        print(f"  ✗ FAIL: First increment returns {turn1}, expected 1")
        failed += 1

    turn2 = increment_turn_count(context)
    if turn2 == 2:
        print(f"  ✓ PASS: Second increment returns 2")
        passed += 1
    else:
        print(f"  ✗ FAIL: Second increment returns {turn2}, expected 2")
        failed += 1

    turn3 = increment_turn_count(context)
    if turn3 == 3:
        print(f"  ✓ PASS: Third increment returns 3")
        passed += 1
    else:
        print(f"  ✗ FAIL: Third increment returns {turn3}, expected 3")
        failed += 1

    # Test 4: Reset session
    print("\nTest 4: Reset session")
    context = MockContext()
    context.user_data['claude_session_id'] = 'user_123_abc123de'
    context.user_data['turn_count'] = 15

    reset_session(context)

    if context.user_data.get('claude_session_id') is None:
        print("  ✓ PASS: Session ID reset to None")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session ID is {context.user_data.get('claude_session_id')}, expected None")
        failed += 1

    if context.user_data.get('turn_count') == 0:
        print("  ✓ PASS: Turn count reset to 0")
        passed += 1
    else:
        print(f"  ✗ FAIL: Turn count is {context.user_data.get('turn_count')}, expected 0")
        failed += 1

    # Test 5: Get session info
    print("\nTest 5: Get session info")
    context = MockContext()
    context.user_data['claude_session_id'] = 'user_999_xyz789ab'
    context.user_data['turn_count'] = 5
    context.user_data['last_active'] = '2026-02-06T10:30:00'
    context.user_data['workspace_path'] = '/workspace'
    context.user_data['preferences'] = {'auto_compact': True}

    info = get_session_info(context)

    if info['session_id'] == 'user_999_xyz789ab':
        print(f"  ✓ PASS: Session ID retrieved correctly")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session ID is {info['session_id']}")
        failed += 1

    if info['turn_count'] == 5:
        print(f"  ✓ PASS: Turn count retrieved correctly")
        passed += 1
    else:
        print(f"  ✗ FAIL: Turn count is {info['turn_count']}, expected 5")
        failed += 1

    if info['workspace_path'] == '/workspace':
        print(f"  ✓ PASS: Workspace path retrieved correctly")
        passed += 1
    else:
        print(f"  ✗ FAIL: Workspace path is {info['workspace_path']}")
        failed += 1

    if info['preferences'] == {'auto_compact': True}:
        print(f"  ✓ PASS: Preferences retrieved correctly")
        passed += 1
    else:
        print(f"  ✗ FAIL: Preferences are {info['preferences']}")
        failed += 1

    # Test 6: Session info with no session
    print("\nTest 6: Get session info when no active session")
    context = MockContext()
    initialize_user_data(context)
    reset_session(context)

    info = get_session_info(context)

    if info['session_id'] == 'No active session':
        print(f"  ✓ PASS: Returns 'No active session' when session_id is None")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session ID is {info['session_id']}, expected 'No active session'")
        failed += 1

    # Test 7: USER_DATA_SCHEMA structure
    print("\nTest 7: USER_DATA_SCHEMA has required fields")
    required_fields = ['claude_session_id', 'turn_count', 'last_active',
                       'workspace_path', 'preferences']

    for field in required_fields:
        if field in USER_DATA_SCHEMA:
            print(f"  ✓ PASS: Schema contains '{field}'")
            passed += 1
        else:
            print(f"  ✗ FAIL: Schema missing '{field}'")
            failed += 1

    # Test 8: Preferences structure
    print("\nTest 8: Preferences have required fields")
    if 'preferences' in USER_DATA_SCHEMA:
        prefs = USER_DATA_SCHEMA['preferences']
        if 'auto_compact' in prefs:
            print(f"  ✓ PASS: Preferences contain 'auto_compact'")
            passed += 1
        else:
            print(f"  ✗ FAIL: Preferences missing 'auto_compact'")
            failed += 1

        if 'max_turns_before_compact' in prefs:
            print(f"  ✓ PASS: Preferences contain 'max_turns_before_compact'")
            passed += 1
        else:
            print(f"  ✗ FAIL: Preferences missing 'max_turns_before_compact'")
            failed += 1

    # Test 9: Multiple users don't share sessions
    print("\nTest 9: Multiple users have isolated sessions")
    context1 = MockContext()
    context2 = MockContext()

    user1_id = 111111111
    user2_id = 222222222

    session1 = get_or_create_session_id(context1, user1_id)
    session2 = get_or_create_session_id(context2, user2_id)

    if session1 != session2:
        print(f"  ✓ PASS: Different users get different session IDs")
        print(f"    User {user1_id}: {session1}")
        print(f"    User {user2_id}: {session2}")
        passed += 1
    else:
        print(f"  ✗ FAIL: Users share session ID: {session1}")
        failed += 1

    if f'user_{user1_id}_' in session1 and f'user_{user2_id}_' in session2:
        print(f"  ✓ PASS: Session IDs contain correct user IDs")
        passed += 1
    else:
        print(f"  ✗ FAIL: Session IDs don't contain correct user IDs")
        failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")

    if failed == 0:
        print("\n✅ All session management tests passed!")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed!")
        return False


if __name__ == '__main__':
    try:
        success = test_session_management()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
