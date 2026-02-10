# Step 16: Command Helpers Implementation

**Estimated Time:** 30 minutes
**Phase:** Phase 4 - Interactive UI & Approvals
**Prerequisites:** Step 15 (Approval Workflow) completed successfully
**Status:** Not Started

---

## Overview

This step implements a comprehensive set of helper commands that improve bot usability and provide essential functionality for session management, status checking, and troubleshooting. These commands transform the bot from a simple voice interface into a fully-featured assistant.

### Context

Users need convenient commands to:
- Check the current session status and configuration
- Clear conversation history when starting a new task
- Get help on available commands and features
- View system information and diagnostics
- Reset bot state when encountering issues

This step creates a complete command suite that enhances user experience and provides self-service troubleshooting capabilities.

### Goals

- ✅ Implement /status command for session information
- ✅ Implement /clear command for session reset
- ✅ Implement /help command with comprehensive documentation
- ✅ Implement /info command for system diagnostics
- ✅ Implement /compact command for context compression
- ✅ Add command aliases for convenience
- ✅ Create user-friendly, informative responses

---

## Implementation Details

### 1. Update Existing /status Command

**File:** `bot/bot.py`

Replace the basic /status handler with enhanced version:

```python
async def handle_status(update: Update, context):
    """Handle /status command - show comprehensive session status."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Gather session information
    session_id = context.user_data.get('claude_session_id', 'None')
    turn_count = context.user_data.get('turn_count', 0)
    pending_change = context.user_data.get('pending_change')
    approval_history = context.user_data.get('approval_history', [])

    # Git repository status
    try:
        git_result = subprocess.run(
            ['git', '-C', str(WORKSPACE_DIR), 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        git_branch = git_result.stdout.strip() if git_result.returncode == 0 else 'Not initialized'

        commit_result = subprocess.run(
            ['git', '-C', str(WORKSPACE_DIR), 'rev-parse', '--short', 'HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        git_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else 'None'
    except Exception as e:
        git_branch = 'Error'
        git_commit = 'Error'
        logger.error(f"Git status check failed: {e}")

    # Workspace files count
    try:
        file_count_result = subprocess.run(
            ['find', str(WORKSPACE_DIR), '-type', 'f', '!', '-path', '*/.git/*'],
            capture_output=True,
            text=True,
            timeout=5
        )
        file_count = len(file_count_result.stdout.strip().split('\n')) if file_count_result.stdout else 0
    except Exception:
        file_count = 'Unknown'

    # Format pending change info
    pending_status = "None"
    if pending_change:
        state = pending_change.get('state', 'unknown')
        timestamp = pending_change.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%H:%M:%S')
            except:
                time_str = timestamp
        pending_status = f"{state.title()} (created at {time_str})"

    # Recent approvals
    recent_approvals = len([h for h in approval_history if h['state'] == CHANGE_STATE_APPROVED])
    recent_rejections = len([h for h in approval_history if h['state'] == CHANGE_STATE_REJECTED])

    # Build status message
    status_text = f"""📊 **Session Status**

**Claude Session:**
└─ ID: `{session_id}`
└─ Turn Count: {turn_count}/20 (auto-compact at 20)

**Pending Changes:**
└─ {pending_status}

**Approval History:**
└─ Approved: {recent_approvals}
└─ Rejected: {recent_rejections}
└─ Total: {len(approval_history)}

**Git Repository:**
└─ Branch: {git_branch}
└─ Latest Commit: {git_commit}

**Workspace:**
└─ Path: `/workspace`
└─ Files: {file_count}

**User Info:**
└─ Telegram ID: `{user_id}`
└─ Name: {update.effective_user.first_name}

Use /clear to reset session
Use /help for available commands
"""

    await update.message.reply_text(status_text, parse_mode='Markdown')
```

### 2. Update Existing /clear Command

Replace the basic /clear handler:

```python
async def handle_clear(update: Update, context):
    """Handle /clear command - reset session with confirmation."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Store old session ID for reference
    old_session_id = context.user_data.get('claude_session_id', 'None')
    old_turn_count = context.user_data.get('turn_count', 0)
    pending_change = context.user_data.get('pending_change')

    # Warn if there are pending changes
    if pending_change and pending_change.get('state') == CHANGE_STATE_PENDING:
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, clear everything", callback_data='clear_confirm'),
                InlineKeyboardButton("❌ Cancel", callback_data='clear_cancel')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ **Warning: Pending Changes Detected**\n\n"
            "You have unapproved changes that will be lost.\n"
            "Are you sure you want to clear the session?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return

    # Clear session data
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0
    context.user_data['pending_change'] = None
    # Keep approval_history for reference

    await update.message.reply_text(
        f"🗑️ **Session Cleared!**\n\n"
        f"Previous session: `{old_session_id}`\n"
        f"Previous turns: {old_turn_count}\n\n"
        f"Starting fresh session on next command.\n"
        f"Approval history preserved.",
        parse_mode='Markdown'
    )

    logger.info(f"Session cleared for user {user_id}: {old_session_id}")


async def handle_clear_callback(update: Update, context):
    """Handle clear confirmation callbacks."""
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == 'clear_confirm':
        # Clear all session data
        old_session_id = context.user_data.get('claude_session_id', 'None')
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0
        context.user_data['pending_change'] = None

        await query.edit_message_text(
            f"🗑️ **Session Cleared!**\n\n"
            f"Previous session: `{old_session_id}`\n"
            f"Pending changes discarded.\n\n"
            f"Starting fresh session on next command.",
            parse_mode='Markdown'
        )
    elif action == 'clear_cancel':
        await query.edit_message_text(
            "✅ Clear operation cancelled.\n\n"
            "Session remains active."
        )
```

### 3. Implement /help Command

Add comprehensive help documentation:

```python
async def handle_help(update: Update, context):
    """Handle /help command - show comprehensive help."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    help_text = """🤖 **Claude Code Voice Assistant - Help**

**Getting Started:**
Send me a voice message or text with your coding task, and I'll execute it using Claude Code.

**📱 Voice Commands:**
1️⃣ Tap the microphone icon
2️⃣ Speak your request clearly
3️⃣ Release to send
4️⃣ Review the transcription
5️⃣ Approve or reject changes

**💬 Text Commands:**
You can also send text messages instead of voice for any task.

**🎯 Available Commands:**

`/start` - Show welcome message
`/help` - Show this help message
`/status` - Show current session status
`/clear` - Clear conversation history
`/history` - View approval history
`/info` - Show system information
`/compact` - Compress session context
`/workspace` - Show workspace contents

**🔘 Inline Buttons:**

✅ **Approve** - Apply changes and commit to git
❌ **Reject** - Discard changes and rollback
📝 **Show Diff** - View git diff of changes
📊 **Git Status** - Check working tree status

**💡 Tips for Best Results:**

• Speak clearly at moderate pace
• Be specific in your requests
• Review transcription before approving
• Use /clear if Claude seems confused
• Check /status regularly
• Use /compact every 20 turns to save tokens

**📝 Example Requests:**

Voice: "Create a Python script that reads a CSV file"
Voice: "Add unit tests for the auth module"
Voice: "Refactor the database connection"
Text: `Fix the bug in login.py`

**🔒 Privacy:**
• Voice files deleted after transcription
• Sessions persist across bot restarts
• Only you can access your session

**❓ Need Help?**
If you encounter issues:
1. Check /status for session info
2. Try /clear to reset
3. Review /info for diagnostics

**🔗 Resources:**
• Claude Code: https://code.claude.com/docs
• Telegram Bot: @YourBotUsername

Last updated: February 4, 2026
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')
```

### 4. Implement /info Command

Add system diagnostics command:

```python
async def handle_info(update: Update, context):
    """Handle /info command - show system diagnostics."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Check Claude Code version
    try:
        claude_version = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        claude_info = claude_version.stdout.strip() if claude_version.returncode == 0 else 'Not found'
    except Exception as e:
        claude_info = f'Error: {str(e)}'

    # Check ffmpeg
    try:
        ffmpeg_version = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        ffmpeg_info = ffmpeg_version.stdout.split('\n')[0] if ffmpeg_version.returncode == 0 else 'Not found'
    except Exception as e:
        ffmpeg_info = f'Error: {str(e)}'

    # Check git
    try:
        git_version = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        git_info = git_version.stdout.strip() if git_version.returncode == 0 else 'Not found'
    except Exception as e:
        git_info = f'Error: {str(e)}'

    # Check workspace mount
    workspace_exists = WORKSPACE_DIR.exists()
    workspace_writable = os.access(str(WORKSPACE_DIR), os.W_OK) if workspace_exists else False

    # Check disk space
    try:
        disk_usage = subprocess.run(
            ['df', '-h', str(WORKSPACE_DIR)],
            capture_output=True,
            text=True,
            timeout=5
        )
        disk_lines = disk_usage.stdout.strip().split('\n')
        disk_info = disk_lines[1] if len(disk_lines) > 1 else 'Unknown'
    except Exception:
        disk_info = 'Error'

    # Python version
    import sys
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # Bot uptime (approximate)
    uptime = datetime.now() - context.bot_data.get('start_time', datetime.now())
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds

    info_text = f"""ℹ️ **System Information**

**Bot Configuration:**
└─ Python: {python_version}
└─ Uptime: {uptime_str}
└─ Webhook: {'Enabled' if WEBHOOK_URL else 'Disabled'}

**Dependencies:**
└─ Claude Code: `{claude_info[:50]}`
└─ ffmpeg: `{ffmpeg_info[:50]}`
└─ git: `{git_info}`

**Workspace:**
└─ Path: `/workspace`
└─ Exists: {'✅' if workspace_exists else '❌'}
└─ Writable: {'✅' if workspace_writable else '❌'}
└─ Disk: `{disk_info}`

**API Keys:**
└─ Anthropic: {'✅ Configured' if ANTHROPIC_API_KEY else '❌ Missing'}
└─ OpenAI: {'✅ Configured' if DEEPGRAM_API_KEY else '❌ Missing'}
└─ Telegram: {'✅ Configured' if TELEGRAM_TOKEN else '❌ Missing'}

**Session Storage:**
└─ Path: `/app/sessions`
└─ Backend: PicklePersistence

**Allowed Users:**
└─ Count: {len(ALLOWED_USER_IDS) if ALLOWED_USER_IDS else 'Unlimited'}
└─ You: {'✅ Authorized' if check_authorization(user_id) else '❌ Not authorized'}

Use /status for session details
Use /help for available commands
"""

    await update.message.reply_text(info_text, parse_mode='Markdown')


# Initialize bot start time in main()
def main():
    # ... existing code ...

    # Store bot start time
    app.bot_data['start_time'] = datetime.now()

    # ... rest of main() ...
```

### 5. Implement /compact Command

Add manual context compression:

```python
async def handle_compact(update: Update, context):
    """Handle /compact command - manually compress session context."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_id = context.user_data.get('claude_session_id')

    if not session_id:
        await update.message.reply_text(
            "ℹ️ No active session to compact.\n\n"
            "Send a command first to create a session."
        )
        return

    # Send status message
    status_msg = await update.message.reply_text("⏳ Compacting session context...")

    try:
        # Run Claude's /compact command
        compact_result = subprocess.run(
            ['claude', '-p', '/compact', '--resume', session_id],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR),
            timeout=30
        )

        if compact_result.returncode == 0:
            # Reset turn count after successful compact
            old_turns = context.user_data.get('turn_count', 0)
            context.user_data['turn_count'] = 0

            await status_msg.edit_text(
                f"✅ **Session Compacted!**\n\n"
                f"Previous turn count: {old_turns}\n"
                f"New turn count: 0\n\n"
                f"Context history has been compressed while preserving important information.\n"
                f"This helps reduce token usage and improves performance.",
                parse_mode='Markdown'
            )

            logger.info(f"Session compacted for user {user_id}: {session_id}")
        else:
            error_msg = compact_result.stderr[:500] if compact_result.stderr else 'Unknown error'
            await status_msg.edit_text(
                f"❌ Compact failed:\n```\n{error_msg}\n```",
                parse_mode='Markdown'
            )

    except subprocess.TimeoutExpired:
        await status_msg.edit_text(
            "⏱️ Compact operation timed out (>30s).\n\n"
            "Try again or use /clear to start fresh."
        )
    except Exception as e:
        logger.error(f"Compact error: {e}", exc_info=True)
        await status_msg.edit_text(f"💥 Error: {str(e)}")
```

### 6. Implement /workspace Command

Add workspace exploration:

```python
async def handle_workspace(update: Update, context):
    """Handle /workspace command - show workspace contents."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    try:
        # Get directory tree (max 3 levels deep)
        tree_result = subprocess.run(
            ['find', str(WORKSPACE_DIR), '-maxdepth', '3', '-type', 'f', '!', '-path', '*/.git/*'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if tree_result.returncode != 0:
            await update.message.reply_text("❌ Failed to read workspace")
            return

        files = [f.replace(str(WORKSPACE_DIR) + '/', '') for f in tree_result.stdout.strip().split('\n') if f]
        files = [f for f in files if f]  # Remove empty strings

        if not files:
            await update.message.reply_text(
                "📁 **Workspace Contents**\n\n"
                "The workspace is empty.\n"
                "Send a command to create files!"
            )
            return

        # Organize by directory
        file_tree = {}
        for file in files[:50]:  # Limit to 50 files
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

        # Format output
        output = "📁 **Workspace Contents**\n\n"
        output += f"Path: `/workspace`\n"
        output += f"Total files: {len(files)}\n\n"

        for dir_name, dir_files in sorted(file_tree.items())[:10]:  # Max 10 dirs
            output += f"📂 `{dir_name}/`\n"
            for file in sorted(dir_files)[:5]:  # Max 5 files per dir
                output += f"  └─ {file}\n"
            if len(dir_files) > 5:
                output += f"  └─ ... and {len(dir_files) - 5} more\n"
            output += "\n"

        if len(files) > 50:
            output += f"_... and {len(files) - 50} more files_\n"

        output += "\nUse git commands or web UI to explore further."

        await update.message.reply_text(output, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Workspace command error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error reading workspace: {str(e)}")
```

### 7. Update Callback Handler

Add support for clear confirmation callbacks:

```python
async def handle_callback(update: Update, context):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    action_data = query.data

    # Handle clear confirmation callbacks
    if action_data in ['clear_confirm', 'clear_cancel']:
        await handle_clear_callback(update, context)
        return

    # ... existing approve/reject/diff/status logic ...
```

### 8. Register All Commands

Update `main()` function:

```python
def main():
    """Start the bot."""
    # Store bot start time
    app.bot_data['start_time'] = datetime.now()

    # Register command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("clear", handle_clear))
    app.add_handler(CommandHandler("history", handle_history))
    app.add_handler(CommandHandler("info", handle_info))
    app.add_handler(CommandHandler("compact", handle_compact))
    app.add_handler(CommandHandler("workspace", handle_workspace))

    # Register message handlers
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Register callback handler
    app.add_handler(CallbackQueryHandler(handle_callback))

    # ... rest of main() ...
```

---

## Testing Procedures

### Test Case 1: /status Command

**Steps:**
1. Send `/status` command
2. Review all status fields

**Expected Output:**
```
📊 Session Status

Claude Session:
└─ ID: session_123456789_1707...
└─ Turn Count: 5/20 (auto-compact at 20)

Pending Changes:
└─ None

Approval History:
└─ Approved: 3
└─ Rejected: 1
└─ Total: 4

Git Repository:
└─ Branch: main
└─ Latest Commit: abc1234

Workspace:
└─ Path: /workspace
└─ Files: 12

User Info:
└─ Telegram ID: 123456789
└─ Name: John

Use /clear to reset session
Use /help for available commands
```

**Verification:**
- All fields populated correctly
- Turn count accurate
- Git info matches actual repository state

### Test Case 2: /clear Command (No Pending Changes)

**Steps:**
1. Ensure no pending changes exist
2. Send `/clear` command
3. Send `/status` to verify reset

**Expected Output:**
```
🗑️ Session Cleared!

Previous session: session_123456789_1707...
Previous turns: 5

Starting fresh session on next command.
Approval history preserved.
```

**Verification:**
```bash
# Status should show:
# - Session ID: None
# - Turn Count: 0
# - Approval history still present
```

### Test Case 3: /clear Command (With Pending Changes)

**Steps:**
1. Create pending change (don't approve/reject)
2. Send `/clear` command
3. Tap "Yes, clear everything"

**Expected Output:**
```
⚠️ Warning: Pending Changes Detected

You have unapproved changes that will be lost.
Are you sure you want to clear the session?

[Buttons: "✅ Yes, clear everything" | "❌ Cancel"]
```

After confirmation:
```
🗑️ Session Cleared!

Previous session: session_123456789_1707...
Pending changes discarded.

Starting fresh session on next command.
```

### Test Case 4: /help Command

**Steps:**
1. Send `/help` command
2. Review all sections

**Expected Output:**
- Complete help text with all sections
- Properly formatted markdown
- All commands listed
- Example requests shown

**Verification:**
- Text not truncated
- Links work correctly
- Emoji render properly

### Test Case 5: /info Command

**Steps:**
1. Send `/info` command
2. Review system diagnostics

**Expected Output:**
```
ℹ️ System Information

Bot Configuration:
└─ Python: 3.11.6
└─ Uptime: 2:15:30
└─ Webhook: Enabled

Dependencies:
└─ Claude Code: claude version 1.5.0
└─ ffmpeg: ffmpeg version 4.4.2-0ubuntu0.22.04.1
└─ git: git version 2.34.1

Workspace:
└─ Path: /workspace
└─ Exists: ✅
└─ Writable: ✅
└─ Disk: /dev/sda1 140G 25G 108G 19% /workspace

API Keys:
└─ Anthropic: ✅ Configured
└─ OpenAI: ✅ Configured
└─ Telegram: ✅ Configured

Session Storage:
└─ Path: /app/sessions
└─ Backend: PicklePersistence

Allowed Users:
└─ Count: 2
└─ You: ✅ Authorized
```

**Verification:**
```bash
# Check versions manually
docker exec telegram-bot claude --version
docker exec telegram-bot ffmpeg -version
docker exec telegram-bot git --version
```

### Test Case 6: /compact Command

**Steps:**
1. Create a session with 15-20 turns
2. Send `/compact` command
3. Wait for confirmation
4. Check `/status` shows turn count reset

**Expected Output:**
```
✅ Session Compacted!

Previous turn count: 18
New turn count: 0

Context history has been compressed while preserving important information.
This helps reduce token usage and improves performance.
```

**Verification:**
```bash
# Check Claude session still works
# Send new command and verify context retained
```

### Test Case 7: /workspace Command

**Steps:**
1. Create some files in workspace
2. Send `/workspace` command
3. Review file tree

**Expected Output:**
```
📁 Workspace Contents

Path: /workspace
Total files: 8

📂 .
  └─ README.md
  └─ package.json

📂 src/
  └─ index.js
  └─ config.js
  └─ ... and 2 more

📂 tests/
  └─ test.spec.js

Use git commands or web UI to explore further.
```

**Verification:**
```bash
# Compare with actual files
docker exec telegram-bot find /workspace -type f ! -path '*/.git/*'
```

### Test Case 8: All Commands in Sequence

**Steps:**
1. `/start` - Welcome message
2. Send voice message
3. `/status` - Check session created
4. `/info` - Verify system health
5. `/workspace` - See created files
6. `/history` - Check approvals
7. `/compact` - Compress context
8. `/help` - Review commands
9. `/clear` - Reset session

**Expected Behavior:**
- All commands work in sequence
- State updates correctly
- No errors or crashes

---

## Screenshots Guidance

### Screenshot 1: Command Help
**Location:** Telegram mobile app
**Content:**
- `/help` command sent
- Full help text displayed
- All sections visible (may need scrolling)

**Annotations:**
- Highlight command list section
- Circle example requests

### Screenshot 2: Status Display
**Location:** Telegram mobile app
**Content:**
- `/status` command result
- All status fields populated

**Annotations:**
- Point out turn count
- Highlight git branch info

### Screenshot 3: System Info
**Location:** Telegram mobile app
**Content:**
- `/info` command output
- All checkmarks showing system health

### Screenshot 4: Workspace Explorer
**Location:** Telegram mobile app
**Content:**
- `/workspace` command showing file tree
- Multiple directories and files

---

## Acceptance Criteria

### Functional Requirements
- ✅ /status shows accurate session information
- ✅ /clear resets session and turn count
- ✅ /clear warns about pending changes
- ✅ /help displays complete documentation
- ✅ /info shows system diagnostics
- ✅ /compact compresses session context
- ✅ /workspace displays file tree
- ✅ /history shows approval history (from Step 15)

### Non-Functional Requirements
- ✅ All commands respond within 3 seconds
- ✅ Command output properly formatted (Markdown)
- ✅ Long outputs don't exceed Telegram limits (4096 chars)
- ✅ Error handling for all command failures
- ✅ Commands work for authorized users only

### User Experience Requirements
- ✅ Clear, informative output for all commands
- ✅ Consistent emoji usage across commands
- ✅ Confirmation dialogs for destructive operations
- ✅ Helpful error messages guide users to solutions
- ✅ Commands documented in /help

---

## Troubleshooting Guide

### Issue 1: /status Shows Incomplete Info

**Symptoms:**
- Some status fields show "Error" or "Unknown"

**Diagnosis:**
```bash
# Check individual components
docker exec telegram-bot git -C /workspace status
docker exec telegram-bot find /workspace -type f | wc -l
```

**Solutions:**
1. Initialize git if not present:
   ```bash
   docker exec telegram-bot git -C /workspace init
   ```
2. Check workspace mount:
   ```bash
   docker inspect telegram-bot | grep -A 10 Mounts
   ```
3. Verify permissions:
   ```bash
   docker exec telegram-bot ls -la /workspace
   ```

### Issue 2: /compact Fails

**Symptoms:**
- "Compact failed" error message

**Diagnosis:**
```bash
# Check Claude session exists
docker exec telegram-bot claude --list-sessions

# Check session file
docker exec telegram-bot ls -la /root/.claude/projects/
```

**Solutions:**
1. Verify session ID is correct in user_data
2. Check Claude config volume mounted
3. Try manual compact:
   ```bash
   docker exec telegram-bot claude -p "/compact" --resume <session_id>
   ```
4. If all fails, use `/clear` to start fresh

### Issue 3: /workspace Command Times Out

**Symptoms:**
- Command takes >10 seconds or fails with timeout

**Diagnosis:**
```bash
# Check file count
docker exec telegram-bot find /workspace -type f | wc -l

# Check disk I/O
docker exec telegram-bot iostat
```

**Solutions:**
1. Reduce maxdepth in find command (currently 3)
2. Exclude more directories (.git, node_modules, etc.)
3. Increase timeout from 10s to 30s
4. Implement pagination for large workspaces

### Issue 4: /info Shows Missing Dependencies

**Symptoms:**
- ffmpeg, git, or Claude shows "Not found"

**Diagnosis:**
```bash
# Check PATH
docker exec telegram-bot echo $PATH

# Check binary locations
docker exec telegram-bot which ffmpeg
docker exec telegram-bot which git
docker exec telegram-bot which claude
```

**Solutions:**
1. Reinstall missing packages in container
2. Update Dockerfile to include all dependencies
3. Check container build logs:
   ```bash
   docker logs telegram-bot | grep -i "install"
   ```

### Issue 5: Commands Don't Respond

**Symptoms:**
- Send command, no response from bot

**Diagnosis:**
```bash
# Check bot is running
docker ps | grep telegram-bot

# Check logs for errors
docker logs telegram-bot --tail 50

# Verify handlers registered
docker logs telegram-bot | grep -i "handler"
```

**Solutions:**
1. Restart bot container:
   ```bash
   docker restart telegram-bot
   ```
2. Verify command handlers registered in main()
3. Check for syntax errors in bot.py
4. Verify webhook is working:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

### Issue 6: /clear Doesn't Clear Session

**Symptoms:**
- After /clear, session still active

**Diagnosis:**
```bash
# Check logs
docker logs telegram-bot | grep -i "clear"

# Check persistence file
docker exec telegram-bot ls -lh /app/sessions/bot_data.pkl
```

**Solutions:**
1. Verify user_data updates are saving
2. Check PicklePersistence configuration
3. Manual clear:
   ```bash
   docker exec telegram-bot rm /app/sessions/bot_data.pkl
   docker restart telegram-bot
   ```

---

## Rollback Procedure

### If Command Helpers Break

**Step 1: Identify Broken Commands**
```bash
# Test each command
# /status
# /clear
# /help
# /info
# /compact
# /workspace

# Check logs for errors
docker logs telegram-bot | grep -i error
```

**Step 2: Disable Broken Commands**

Create a hotfix to disable problematic commands:

```python
# In bot.py, comment out broken command handler
# app.add_handler(CommandHandler("broken_command", handle_broken_command))
```

Restart bot:
```bash
docker restart telegram-bot
```

**Step 3: Revert to Previous Version**

```bash
# SSH to server
cd /path/to/claude-remote-runner
git log --oneline  # Find commit before step 16
git checkout <commit-hash> bot/bot.py
docker restart telegram-bot
```

**Step 4: Verify Core Functionality**

Test essential commands still work:
- `/start` - Welcome message
- Voice message transcription
- Basic Claude execution
- Approval buttons

**Step 5: Fix and Redeploy**

1. Fix the issue locally
2. Test thoroughly
3. Commit fix
4. Push to repository
5. Coolify auto-deploys

---

## Additional Notes

### Performance Considerations

**Command Execution Time:**
- `/status`: <1 second (multiple subprocess calls)
- `/clear`: <0.5 seconds (memory only)
- `/help`: <0.5 seconds (static text)
- `/info`: 1-2 seconds (multiple version checks)
- `/compact`: 10-30 seconds (Claude API call)
- `/workspace`: 2-5 seconds (filesystem scan)

**Optimization Tips:**
- Cache version checks in /info (refresh every 5 minutes)
- Implement command rate limiting (max 10/minute per user)
- Lazy load help text from file
- Paginate workspace results for large directories

### Security Considerations

**Command Access:**
- All commands check authorization first
- User IDs validated against ALLOWED_USER_IDS
- No command exposes sensitive credentials
- File paths sanitized in /workspace output

**Information Disclosure:**
- /info shows only non-sensitive system info
- API keys shown as "Configured/Missing" only
- User IDs logged but not shared between users
- Workspace paths never expose host filesystem

### Future Enhancements

**Command Improvements:**
- [ ] /stats - Usage statistics (messages/day, API costs)
- [ ] /settings - Configure bot preferences
- [ ] /export - Export session history
- [ ] /import - Import previous session
- [ ] /alias - Create custom command aliases
- [ ] /schedule - Schedule commands (cron-like)

**Interactive Features:**
- [ ] Inline search in /workspace
- [ ] File preview from /workspace
- [ ] Interactive session browser in /history
- [ ] Command autocomplete suggestions
- [ ] Multi-language /help support

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** Begin implementation following code sections above
**Estimated Completion:** 30 minutes after start
