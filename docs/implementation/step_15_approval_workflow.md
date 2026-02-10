# Step 15: Approval Workflow Implementation

**Estimated Time:** 30 minutes
**Phase:** Phase 4 - Interactive UI & Approvals
**Prerequisites:** Step 14 (Git Integration) completed successfully
**Status:** Not Started

---

## Overview

This step implements the complete approval workflow that allows users to approve or reject changes made by Claude Code before they are applied to the workspace. This provides a critical safety mechanism for reviewing AI-generated changes before committing them.

### Context

After Claude Code generates changes (file edits, new files, deletions), users need the ability to:
1. Review what changes were made
2. Approve changes to apply them permanently
3. Reject changes to discard them
4. Track the state of pending/approved/rejected changes

This step builds on the inline keyboard UI (Step 13) and git integration (Step 14) to create a complete workflow that maintains state consistency and provides clear user feedback.

### Goals

- ✅ Implement state tracking for pending changes
- ✅ Create approve/reject callback handlers
- ✅ Add confirmation messages for user actions
- ✅ Ensure idempotent approval operations
- ✅ Implement rollback for rejected changes
- ✅ Verify state consistency across bot restarts

---

## Implementation Details

### 1. Update Bot State Management

**File:** `bot/bot.py`

Add state tracking constants at the top of the file:

```python
# Change state constants
CHANGE_STATE_PENDING = 'pending'
CHANGE_STATE_APPROVED = 'approved'
CHANGE_STATE_REJECTED = 'rejected'
```

### 2. Implement Change State Tracking

Add to the `execute_claude_command` function after Claude execution:

```python
async def execute_claude_command(update: Update, context, prompt: str):
    """Execute Claude Code command and handle response."""
    user_id = update.effective_user.id

    # ... existing code ...

    # After successful Claude execution
    if result.returncode == 0:
        # Store pending changes state
        change_id = f"change_{user_id}_{datetime.now().timestamp()}"
        context.user_data['pending_change'] = {
            'id': change_id,
            'state': CHANGE_STATE_PENDING,
            'prompt': prompt,
            'timestamp': datetime.now().isoformat(),
            'output': output,
            'session_id': context.user_data.get('claude_session_id')
        }

        logger.info(f"Created pending change: {change_id}")
```

### 3. Update Inline Keyboard

Modify the keyboard creation to include change state:

```python
# Create response with approval keyboard
keyboard = [
    [
        InlineKeyboardButton("✅ Approve", callback_data=f'approve_{change_id}'),
        InlineKeyboardButton("❌ Reject", callback_data=f'reject_{change_id}')
    ],
    [
        InlineKeyboardButton("📝 Show Diff", callback_data=f'diff_{change_id}'),
        InlineKeyboardButton("📊 Git Status", callback_data=f'status_{change_id}')
    ]
]
reply_markup = InlineKeyboardMarkup(keyboard)
```

### 4. Implement Approve Handler

Replace the simple approve callback with comprehensive approval logic:

```python
async def handle_approve(update: Update, context, change_id: str):
    """Handle change approval."""
    query = update.callback_query
    await query.answer()

    # Retrieve pending change
    pending_change = context.user_data.get('pending_change')

    if not pending_change:
        await query.edit_message_text(
            "❌ No pending changes found. They may have already been processed."
        )
        return

    if pending_change['id'] != change_id:
        await query.edit_message_text(
            "❌ Change ID mismatch. This change may have been superseded."
        )
        return

    if pending_change['state'] != CHANGE_STATE_PENDING:
        await query.edit_message_text(
            f"ℹ️ This change was already {pending_change['state']}."
        )
        return

    # Mark as approved
    pending_change['state'] = CHANGE_STATE_APPROVED
    pending_change['approved_at'] = datetime.now().isoformat()

    # Store in approval history
    if 'approval_history' not in context.user_data:
        context.user_data['approval_history'] = []

    context.user_data['approval_history'].append({
        'change_id': change_id,
        'state': CHANGE_STATE_APPROVED,
        'timestamp': datetime.now().isoformat()
    })

    # Limit history to last 20 changes
    if len(context.user_data['approval_history']) > 20:
        context.user_data['approval_history'] = context.user_data['approval_history'][-20:]

    logger.info(f"Approved change: {change_id}")

    # Check if there are git changes to commit
    git_status = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_DIR)
    )

    if git_status.stdout.strip():
        commit_message = f"Apply changes from Claude\n\nPrompt: {pending_change['prompt'][:100]}"

        # Stage and commit changes
        subprocess.run(['git', 'add', '.'], cwd=str(WORKSPACE_DIR))
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR)
        )

        if commit_result.returncode == 0:
            await query.edit_message_text(
                f"✅ Changes approved and committed!\n\n"
                f"📝 Commit: {commit_message}\n"
                f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await query.edit_message_text(
                f"⚠️ Changes approved but commit failed:\n"
                f"```\n{commit_result.stderr[:500]}\n```",
                parse_mode='Markdown'
            )
    else:
        await query.edit_message_text(
            "✅ Changes approved!\n\n"
            "ℹ️ No git changes detected (may have been informational output)"
        )

    # Clear pending change
    context.user_data['pending_change'] = None
```

### 5. Implement Reject Handler

Add comprehensive rejection logic with rollback:

```python
async def handle_reject(update: Update, context, change_id: str):
    """Handle change rejection with rollback."""
    query = update.callback_query
    await query.answer()

    # Retrieve pending change
    pending_change = context.user_data.get('pending_change')

    if not pending_change:
        await query.edit_message_text(
            "❌ No pending changes found. They may have already been processed."
        )
        return

    if pending_change['id'] != change_id:
        await query.edit_message_text(
            "❌ Change ID mismatch. This change may have been superseded."
        )
        return

    if pending_change['state'] != CHANGE_STATE_PENDING:
        await query.edit_message_text(
            f"ℹ️ This change was already {pending_change['state']}."
        )
        return

    # Mark as rejected
    pending_change['state'] = CHANGE_STATE_REJECTED
    pending_change['rejected_at'] = datetime.now().isoformat()

    # Store in approval history
    if 'approval_history' not in context.user_data:
        context.user_data['approval_history'] = []

    context.user_data['approval_history'].append({
        'change_id': change_id,
        'state': CHANGE_STATE_REJECTED,
        'timestamp': datetime.now().isoformat()
    })

    logger.info(f"Rejected change: {change_id}")

    # Rollback git changes
    git_status = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_DIR)
    )

    if git_status.stdout.strip():
        # Reset all changes
        subprocess.run(['git', 'reset', '--hard', 'HEAD'], cwd=str(WORKSPACE_DIR))
        subprocess.run(['git', 'clean', '-fd'], cwd=str(WORKSPACE_DIR))

        await query.edit_message_text(
            f"❌ Changes rejected and rolled back!\n\n"
            f"🔄 Workspace reset to last committed state\n"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        await query.edit_message_text(
            "❌ Changes rejected!\n\n"
            "ℹ️ No git changes detected (may have been informational output)"
        )

    # Clear pending change
    context.user_data['pending_change'] = None
```

### 6. Update Callback Handler Router

Replace the existing `handle_callback` function:

```python
async def handle_callback(update: Update, context):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    action_data = query.data

    # Parse action and change_id
    parts = action_data.split('_', 1)
    action = parts[0]
    change_id = parts[1] if len(parts) > 1 else None

    logger.info(f"Callback: action={action}, change_id={change_id}")

    if action == 'approve':
        await handle_approve(update, context, change_id)

    elif action == 'reject':
        await handle_reject(update, context, change_id)

    elif action == 'diff':
        await query.answer()
        # Show git diff
        diff_result = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR)
        )
        diff_output = diff_result.stdout or "(No changes)"

        # Split if too long
        if len(diff_output) > 3800:
            chunks = [diff_output[i:i+3800] for i in range(0, len(diff_output), 3800)]
            for i, chunk in enumerate(chunks[:3]):  # Limit to 3 chunks
                await query.message.reply_text(
                    f"```diff\n{chunk}\n```",
                    parse_mode='Markdown'
                )
        else:
            await query.message.reply_text(
                f"```diff\n{diff_output}\n```",
                parse_mode='Markdown'
            )

    elif action == 'status':
        await query.answer()
        # Show git status
        status_result = subprocess.run(
            ['git', 'status'],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR)
        )
        status_output = status_result.stdout or "(No git repository)"
        await query.message.reply_text(
            f"```\n{status_output[:3800]}\n```",
            parse_mode='Markdown'
        )
```

### 7. Add Approval History Command

Add a new command to view approval history:

```python
async def handle_history(update: Update, context):
    """Handle /history command - show approval history."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    history = context.user_data.get('approval_history', [])

    if not history:
        await update.message.reply_text("📜 No approval history yet.")
        return

    # Format history
    history_text = "📜 Recent Approval History:\n\n"
    for item in reversed(history[-10:]):  # Last 10 items, newest first
        state_emoji = {
            CHANGE_STATE_APPROVED: '✅',
            CHANGE_STATE_REJECTED: '❌'
        }.get(item['state'], '❓')

        timestamp = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d %H:%M')
        history_text += f"{state_emoji} {item['change_id'][:20]}... - {timestamp}\n"

    await update.message.reply_text(history_text)

# Register in main()
app.add_handler(CommandHandler("history", handle_history))
```

---

## Testing Procedures

### Test Case 1: Basic Approval Flow

**Steps:**
1. Send text message: "Create a new file called test.txt with hello world"
2. Wait for Claude response with approval buttons
3. Tap "✅ Approve" button
4. Verify success message shows commit details

**Expected Output:**
```
✅ Changes approved and committed!

📝 Commit: Apply changes from Claude

Prompt: Create a new file called test.txt with hello world
🕐 2026-02-04 15:30:45
```

**Verification:**
```bash
# SSH to server
docker exec telegram-bot git -C /workspace log -1 --oneline
# Should show: "Apply changes from Claude"

docker exec telegram-bot cat /workspace/test.txt
# Should show: hello world content
```

### Test Case 2: Rejection with Rollback

**Steps:**
1. Send text message: "Create a file called unwanted.txt"
2. Wait for Claude response
3. Tap "❌ Reject" button
4. Verify rollback message
5. Check that file was not created

**Expected Output:**
```
❌ Changes rejected and rolled back!

🔄 Workspace reset to last committed state
🕐 2026-02-04 15:32:10
```

**Verification:**
```bash
docker exec telegram-bot ls /workspace/unwanted.txt
# Should show: No such file or directory
```

### Test Case 3: Idempotent Approval

**Steps:**
1. Create a pending change
2. Tap "✅ Approve" button
3. Wait for confirmation
4. Tap "✅ Approve" button again on the same message

**Expected Output:**
```
ℹ️ This change was already approved.
```

### Test Case 4: View Diff Before Approval

**Steps:**
1. Send text message: "Add a comment to test.txt"
2. Wait for response
3. Tap "📝 Show Diff" button
4. Review diff output
5. Tap "✅ Approve" or "❌ Reject"

**Expected Output:**
```diff
diff --git a/test.txt b/test.txt
index 123abc..456def 100644
--- a/test.txt
+++ b/test.txt
@@ -1 +1,2 @@
 hello world
+# This is a comment
```

### Test Case 5: Git Status Check

**Steps:**
1. Create pending change
2. Tap "📊 Git Status" button
3. Review status output

**Expected Output:**
```
On branch main
Changes not staged for commit:
  modified:   test.txt

no changes added to commit
```

### Test Case 6: Approval History

**Steps:**
1. Perform several approve/reject actions
2. Send `/history` command
3. Review history output

**Expected Output:**
```
📜 Recent Approval History:

✅ change_123456789_17... - 2026-02-04 15:30
❌ change_123456788_17... - 2026-02-04 15:28
✅ change_123456787_17... - 2026-02-04 15:25
```

### Test Case 7: State Persistence Across Restart

**Steps:**
1. Create pending change (do NOT approve/reject yet)
2. Restart bot container:
   ```bash
   docker restart telegram-bot
   ```
3. Wait for bot to restart
4. Try to approve the pending change

**Expected Behavior:**
- Pending change should persist (thanks to PicklePersistence)
- Approval should work normally

### Test Case 8: Multiple Concurrent Users

**Steps:**
1. Have two different users send commands simultaneously
2. Each user approves/rejects their own changes
3. Verify state isolation

**Expected Behavior:**
- Each user's pending changes tracked separately
- No cross-contamination of change states
- Approval history separate per user

---

## Screenshots Guidance

### Screenshot 1: Approval Flow
**Location:** Telegram mobile app
**Content:**
- Voice message sent
- Transcription confirmation
- Claude response with changes
- Inline keyboard showing all 4 buttons
- Approval confirmation message

**Annotations:**
- Arrow pointing to "✅ Approve" button
- Highlight the commit message in confirmation

### Screenshot 2: Rejection Flow
**Location:** Telegram mobile app
**Content:**
- Pending change with buttons
- User tapping "❌ Reject"
- Rollback confirmation message

**Annotations:**
- Highlight "Workspace reset to last committed state"

### Screenshot 3: Diff Review
**Location:** Telegram mobile app
**Content:**
- "📝 Show Diff" button tapped
- Diff output displayed with syntax highlighting
- Follow-up approval action

### Screenshot 4: Approval History
**Location:** Telegram mobile app
**Content:**
- `/history` command sent
- List of recent approvals/rejections with timestamps

---

## Acceptance Criteria

### Functional Requirements
- ✅ Approve button commits changes to git
- ✅ Reject button rolls back all changes
- ✅ Diff button shows accurate git diff
- ✅ Status button shows current git status
- ✅ Approval history tracks last 20 actions
- ✅ Change states tracked: pending, approved, rejected
- ✅ Idempotent approval (can't approve twice)
- ✅ Clear confirmation messages for all actions

### Non-Functional Requirements
- ✅ State persists across bot restarts
- ✅ Each user has isolated state
- ✅ Response time <2 seconds for approval actions
- ✅ Git operations are atomic (no partial commits)
- ✅ Error handling for git operation failures

### User Experience Requirements
- ✅ Clear visual feedback for each action
- ✅ Timestamps in user's local timezone
- ✅ Truncated change IDs for readability
- ✅ Emoji indicators for visual scanning
- ✅ Informative messages for edge cases

---

## Troubleshooting Guide

### Issue 1: Approval Not Working

**Symptoms:**
- Tap "✅ Approve" button
- No response or error message

**Diagnosis:**
```bash
# Check bot logs
docker logs telegram-bot | grep -i approve

# Check callback data format
docker logs telegram-bot | grep -i callback
```

**Solutions:**
1. Verify callback_data format includes change_id
2. Check pending_change exists in user_data
3. Verify git repository initialized in workspace:
   ```bash
   docker exec telegram-bot git -C /workspace status
   ```
4. Check file permissions on workspace:
   ```bash
   docker exec telegram-bot ls -la /workspace
   ```

### Issue 2: Rollback Fails

**Symptoms:**
- Reject button clicked
- Error message or incomplete rollback

**Diagnosis:**
```bash
# Check git status
docker exec telegram-bot git -C /workspace status

# Check for uncommitted changes
docker exec telegram-bot git -C /workspace diff
```

**Solutions:**
1. Ensure workspace is a git repository
2. Check no files are locked or in use
3. Verify git clean -fd permissions
4. Manual rollback if needed:
   ```bash
   docker exec telegram-bot bash -c "cd /workspace && git reset --hard HEAD && git clean -fd"
   ```

### Issue 3: State Not Persisting

**Symptoms:**
- Bot restart loses pending changes
- Approval history disappears

**Diagnosis:**
```bash
# Check sessions directory
docker exec telegram-bot ls -la /app/sessions/

# Check pickle file
docker exec telegram-bot ls -lh /app/sessions/bot_data.pkl
```

**Solutions:**
1. Verify sessions volume mounted correctly
2. Check PicklePersistence configured in bot.py
3. Ensure sessions directory writable:
   ```bash
   docker exec telegram-bot chmod 755 /app/sessions
   ```
4. Check disk space:
   ```bash
   docker exec telegram-bot df -h
   ```

### Issue 4: Change ID Mismatch

**Symptoms:**
- "Change ID mismatch" error when approving

**Diagnosis:**
```bash
# Check callback data in logs
docker logs telegram-bot | grep -i "change_id"
```

**Solutions:**
1. Verify callback_data parsing logic splits correctly
2. Check change_id format is consistent
3. Ensure change_id stored correctly in pending_change
4. Clear state and retry:
   - Send `/clear` command
   - Resend the request

### Issue 5: Git Commit Fails

**Symptoms:**
- Approval succeeds but commit fails
- Error message about git configuration

**Diagnosis:**
```bash
# Check git config
docker exec telegram-bot git -C /workspace config --list
```

**Solutions:**
1. Configure git user:
   ```bash
   docker exec telegram-bot git -C /workspace config user.name "Claude Bot"
   docker exec telegram-bot git -C /workspace config user.email "bot@example.com"
   ```
2. Initialize git if needed:
   ```bash
   docker exec telegram-bot git -C /workspace init
   ```
3. Check for merge conflicts
4. Verify write permissions on .git directory

### Issue 6: Approval History Not Showing

**Symptoms:**
- `/history` command shows "No approval history"
- But approvals have been made

**Diagnosis:**
```bash
# Check user_data persistence
docker logs telegram-bot | grep -i "approval_history"
```

**Solutions:**
1. Verify approval_history appended correctly in handlers
2. Check list slicing logic (-20:)
3. Ensure user_data saving between operations
4. Test with fresh session:
   - Send `/clear`
   - Make new change
   - Approve
   - Check `/history`

---

## Rollback Procedure

### If Approval Workflow Breaks

**Step 1: Identify the Issue**
```bash
# Check bot logs for errors
docker logs telegram-bot --tail 100 | grep -i error

# Check recent changes
docker exec telegram-bot git -C /workspace log -5 --oneline
```

**Step 2: Disable Approval Features**

Option A: Quick fix - remove approval requirements
```python
# In bot.py, temporarily skip approval checks
# Comment out keyboard creation and directly apply changes
```

Option B: Revert to previous code version
```bash
# SSH to server
cd /path/to/claude-remote-runner
git log --oneline  # Find commit before step 15
git checkout <commit-hash> bot/bot.py
docker restart telegram-bot
```

**Step 3: Manual Workspace Cleanup**
```bash
# Reset workspace to clean state
docker exec telegram-bot bash -c "cd /workspace && git reset --hard HEAD"
docker exec telegram-bot bash -c "cd /workspace && git clean -fd"
```

**Step 4: Clear User State**
```bash
# Remove corrupted session data
docker exec telegram-bot rm /app/sessions/bot_data.pkl
docker restart telegram-bot
```

**Step 5: Restore from Backup**

If workspace is corrupted:
```bash
# Stop bot
docker stop telegram-bot

# Restore workspace volume
docker run --rm \
  -v claude-remote-runner_workspace:/target \
  -v $(pwd)/backups:/backup \
  alpine \
  sh -c "cd /target && tar xzf /backup/workspace-backup-latest.tar.gz --strip-components=1"

# Restart bot
docker start telegram-bot
```

**Step 6: Verify Rollback**
```bash
# Test basic bot functionality
# 1. Send /start command
# 2. Send text message (not voice)
# 3. Verify response

# Check workspace state
docker exec telegram-bot ls -la /workspace
docker exec telegram-bot git -C /workspace status
```

**Step 7: Document and Fix**
1. Document the issue in GitHub issue tracker
2. Analyze root cause
3. Implement fix
4. Test thoroughly before redeploying
5. Update rollback procedure with learnings

---

## Additional Notes

### Performance Considerations

**Git Operations:**
- `git diff` can be slow on large repositories
- Consider adding `--stat` flag for summary view
- Implement timeout for git operations (5 seconds)

**State Storage:**
- Approval history limited to 20 items to prevent memory bloat
- Pickle file can grow large with many users
- Consider cleanup of old approval_history periodically

### Security Considerations

**Git Operations:**
- All git operations run with bot user permissions
- No exposure of git credentials to users
- Commits attributed to configured bot user

**State Isolation:**
- Each Telegram user has isolated user_data
- Change IDs include user_id to prevent cross-user manipulation
- Callback data validation prevents unauthorized approvals

### Future Enhancements

**Approval Workflow V2:**
- [ ] Selective file approval (approve only specific files)
- [ ] Approval comments/notes
- [ ] Multi-step approval for destructive operations
- [ ] Approval delegation (team approvals)
- [ ] Approval webhooks (notify external systems)

**Git Integration V2:**
- [ ] Branch-based workflow (create PR instead of direct commit)
- [ ] Squash multiple changes into single commit
- [ ] Custom commit message templates
- [ ] Automatic push to remote after approval
- [ ] Integration with GitHub/GitLab API

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** Begin implementation following code sections above
**Estimated Completion:** 30 minutes after start
