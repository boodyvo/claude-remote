# Step 10: Session ID Management

**Phase:** 3 - Claude Code Integration
**Estimated Time:** 1 hour
**Prerequisites:** Steps 1-9 completed
**Dependencies:** Claude Code CLI session system, filesystem access

---

## Overview

This step implements comprehensive session ID management for Claude Code conversations. It includes proper session ID extraction from Claude's output, session persistence, session listing, and cleanup of stale sessions.

### Context

Claude Code stores conversation sessions in `~/.claude/projects/`. Each session has:
- Unique session ID
- Conversation history
- Context and state
- Metadata (creation time, last accessed, etc.)

Proper session management ensures:
- Conversations persist across bot restarts
- Multiple users have isolated sessions
- Stale sessions don't consume disk space
- Users can manage their sessions

### Goals

1. Extract session IDs from Claude Code output
2. Store session IDs persistently per user
3. Implement session listing functionality
4. Add session cleanup for inactive sessions
5. Provide commands for session management (/sessions, /newsession)
6. Test session isolation between users

---

## Implementation Details

### 10.1 Session ID Extraction

Claude Code returns session information in different formats depending on the output format used. We need to extract and store the session ID reliably.

**File: `bot/claude_executor.py`** (update)

Add improved session ID extraction:

```python
import re
from typing import Optional, Dict, List, Any
from pathlib import Path
import os

# Claude session directory
CLAUDE_SESSIONS_DIR = Path.home() / '.claude' / 'projects'

class ClaudeExecutor:
    """Execute Claude Code commands and parse output."""

    # ... existing code ...

    def _extract_session_id_from_events(self, events: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract session ID from streaming JSON events.

        Args:
            events: List of parsed JSON event objects

        Returns:
            Session ID string or None if not found
        """
        # Method 1: Look for explicit session_id in events
        for event in events:
            if 'session_id' in event:
                return event['session_id']

            # Check nested structures
            if 'message' in event and isinstance(event['message'], dict):
                if 'session_id' in event['message']:
                    return event['message']['session_id']

        # Method 2: Look in metadata
        for event in events:
            metadata = event.get('metadata', {})
            if 'session_id' in metadata:
                return metadata['session_id']

        return None

    def _extract_session_id_from_filesystem(self) -> Optional[str]:
        """
        Extract the most recently created/modified session ID from filesystem.

        Returns:
            Most recent session ID or None
        """
        try:
            if not CLAUDE_SESSIONS_DIR.exists():
                return None

            # Find all session directories
            session_dirs = [
                d for d in CLAUDE_SESSIONS_DIR.iterdir()
                if d.is_dir()
            ]

            if not session_dirs:
                return None

            # Get most recently modified
            latest_session = max(session_dirs, key=lambda d: d.stat().st_mtime)
            return latest_session.name

        except Exception as e:
            logger.error(f"Failed to extract session from filesystem: {e}")
            return None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific session.

        Args:
            session_id: The session ID to query

        Returns:
            Dictionary with session info or None if not found
        """
        session_dir = CLAUDE_SESSIONS_DIR / session_id

        if not session_dir.exists():
            return None

        try:
            stat = session_dir.stat()

            # Count conversation turns (if history file exists)
            history_file = session_dir / 'history.json'
            turn_count = 0
            if history_file.exists():
                import json
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    turn_count = len(history.get('turns', []))

            return {
                'session_id': session_id,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'size_bytes': sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file()),
                'turn_count': turn_count,
                'exists': True
            }

        except Exception as e:
            logger.error(f"Failed to get session info for {session_id}: {e}")
            return None

    def list_sessions(self, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available Claude sessions.

        Args:
            user_filter: Optional filter to match session IDs (e.g., "user_123")

        Returns:
            List of session info dictionaries
        """
        try:
            if not CLAUDE_SESSIONS_DIR.exists():
                return []

            sessions = []

            for session_dir in CLAUDE_SESSIONS_DIR.iterdir():
                if not session_dir.is_dir():
                    continue

                session_id = session_dir.name

                # Apply filter if provided
                if user_filter and not session_id.startswith(user_filter):
                    continue

                info = self.get_session_info(session_id)
                if info:
                    sessions.append(info)

            # Sort by most recently modified
            sessions.sort(key=lambda s: s['modified'], reverse=True)

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a Claude session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if successful, False otherwise
        """
        session_dir = CLAUDE_SESSIONS_DIR / session_id

        if not session_dir.exists():
            logger.warning(f"Session {session_id} not found")
            return False

        try:
            import shutil
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_old_sessions(
        self,
        user_filter: Optional[str] = None,
        max_age_days: int = 30
    ) -> int:
        """
        Delete sessions older than max_age_days.

        Args:
            user_filter: Optional filter for session IDs
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of sessions deleted
        """
        from datetime import datetime, timedelta
        import time

        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0

        sessions = self.list_sessions(user_filter=user_filter)

        for session in sessions:
            if session['modified'] < cutoff_time:
                if self.delete_session(session['session_id']):
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old sessions")
        return deleted_count

    def _parse_stream_json(self, result: subprocess.CompletedProcess) -> ClaudeResponse:
        """Parse streaming JSON output from Claude Code."""
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"Claude returned error: {error_msg}")
            return ClaudeResponse(
                success=False,
                output="",
                error=error_msg
            )

        # Parse events
        events = []
        output_parts = []
        files_modified = []
        tools_used = set()

        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                events.append(event)

                event_type = event.get('type')

                if event_type == 'content_block_delta':
                    delta = event.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        output_parts.append(text)

                elif event_type == 'content_block_start':
                    content_block = event.get('content_block', {})
                    if content_block.get('type') == 'tool_use':
                        tool_name = content_block.get('name', 'unknown')
                        tools_used.add(tool_name)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON line: {line[:100]}")
                continue

        output = ''.join(output_parts).strip()

        # Extract session ID - try multiple methods
        session_id = self._extract_session_id_from_events(events)

        # Fallback: get from filesystem
        if not session_id:
            session_id = self._extract_session_id_from_filesystem()

        return ClaudeResponse(
            success=True,
            output=output if output else "(Claude completed task with no text output)",
            session_id=session_id,
            files_modified=files_modified,
            tools_used=list(tools_used),
            raw_events=events
        )
```

### 10.2 Bot Integration

**File: `bot/bot.py`** (update)

Add session management commands:

```python
from datetime import datetime
import time

# ... existing imports and code ...

async def handle_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sessions command - list user's sessions."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Get user's sessions
    user_filter = f"user_{user_id}"
    sessions = claude_executor.list_sessions(user_filter=user_filter)

    if not sessions:
        await update.message.reply_text(
            "📭 No sessions found.\n\n"
            "Send a message to start a new session!"
        )
        return

    # Format session list
    current_session_id = context.user_data.get('claude_session_id')

    message_parts = ["📚 Your Claude Sessions\n" + "=" * 30 + "\n"]

    for i, session in enumerate(sessions[:10], 1):  # Limit to 10 most recent
        session_id = session['session_id']
        is_current = session_id == current_session_id

        # Format timestamps
        modified_time = datetime.fromtimestamp(session['modified'])
        modified_str = modified_time.strftime('%Y-%m-%d %H:%M')

        # Format size
        size_kb = session['size_bytes'] / 1024
        size_str = f"{size_kb:.1f}KB" if size_kb < 1024 else f"{size_kb/1024:.1f}MB"

        # Build line
        prefix = "👉 " if is_current else f"{i}. "
        message_parts.append(
            f"{prefix}{session_id[:20]}...\n"
            f"   📅 {modified_str} | 💾 {size_str} | 🔄 {session['turn_count']} turns\n"
        )

    message_parts.append(
        f"\n💡 Use /newsession to start fresh\n"
        f"💡 Use /cleansessions to delete old sessions"
    )

    await update.message.reply_text(''.join(message_parts))


async def handle_newsession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newsession command - start a new session."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    old_session = context.user_data.get('claude_session_id', 'None')

    # Clear current session
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0

    await update.message.reply_text(
        f"🆕 New session started!\n\n"
        f"Previous session: `{old_session}`\n\n"
        f"Send a message to begin.",
        parse_mode='Markdown'
    )


async def handle_cleansessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cleansessions command - delete old sessions."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Delete sessions older than 30 days
    user_filter = f"user_{user_id}"
    deleted_count = claude_executor.cleanup_old_sessions(
        user_filter=user_filter,
        max_age_days=30
    )

    if deleted_count > 0:
        await update.message.reply_text(
            f"🗑️ Cleaned up {deleted_count} old session(s)\n"
            f"(older than 30 days)"
        )
    else:
        await update.message.reply_text(
            "✨ No old sessions to clean up!\n"
            "All your sessions are recent."
        )


async def handle_sessioninfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sessioninfo command - show detailed session info."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_id = context.user_data.get('claude_session_id')

    if not session_id:
        await update.message.reply_text("❌ No active session")
        return

    # Get session info
    info = claude_executor.get_session_info(session_id)

    if not info:
        await update.message.reply_text(
            f"⚠️ Session `{session_id}` not found on disk.\n"
            f"It may have been deleted or not created yet.",
            parse_mode='Markdown'
        )
        return

    # Format info
    created_time = datetime.fromtimestamp(info['created'])
    modified_time = datetime.fromtimestamp(info['modified'])

    message = (
        f"📊 Session Information\n"
        f"{'=' * 30}\n\n"
        f"🆔 ID: `{info['session_id']}`\n\n"
        f"📅 Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📅 Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💾 Size: {info['size_bytes'] / 1024:.2f} KB\n"
        f"🔄 Turns: {info['turn_count']}\n\n"
        f"📁 Location: `~/.claude/projects/{info['session_id']}/`"
    )

    await update.message.reply_text(message, parse_mode='Markdown')


# Update execute_claude_command to save session ID properly
async def execute_claude_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str
):
    """Execute a Claude Code command and send response to user."""
    user_id = update.effective_user.id
    initialize_user_data(context)

    # Get or create session ID
    session_id = context.user_data.get('claude_session_id')

    # Send "working" message
    status_msg = await update.message.reply_text(
        "⏳ Claude is working on this...\n"
        f"{'📝 Resuming session' if session_id else '🆕 Starting new session'}"
    )

    try:
        # Execute Claude command
        response: ClaudeResponse = claude_executor.execute(
            prompt=prompt,
            session_id=session_id
        )

        if not response.success:
            await status_msg.edit_text(
                f"❌ Claude encountered an error:\n\n"
                f"```\n{response.error[:3000]}\n```",
                parse_mode='Markdown'
            )
            return

        # Update session ID if returned
        if response.session_id:
            # If this is a new session, generate a user-specific ID
            if not session_id:
                # Claude may have created a session - use it or create our own
                import uuid
                user_session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"

                # Rename Claude's session to our format (if possible)
                # For now, just store whatever Claude returns
                context.user_data['claude_session_id'] = response.session_id
                logger.info(f"Created new session: {response.session_id}")
            else:
                # Update existing session ID (in case Claude changed it)
                context.user_data['claude_session_id'] = response.session_id

        # Increment turn count
        context.user_data['turn_count'] = context.user_data.get('turn_count', 0) + 1
        turn_count = context.user_data['turn_count']

        # Auto-compact every 20 turns
        if turn_count >= 20:
            logger.info(f"Auto-compacting session after {turn_count} turns")
            if claude_executor.compact_session(context.user_data['claude_session_id']):
                context.user_data['turn_count'] = 0
                await update.message.reply_text("🗜️ Session auto-compacted")

        # Format and send response
        # ... (rest of the function remains the same)

    except Exception as e:
        logger.error(f"Unexpected error executing Claude: {e}", exc_info=True)
        await status_msg.edit_text(
            f"💥 Unexpected error:\n```\n{str(e)[:3000]}\n```",
            parse_mode='Markdown'
        )


def build_application():
    """Build the Telegram bot application."""
    app = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .persistence(persistence) \
        .build()

    # Register handlers
    app.add_handler(CommandHandler("sessions", handle_sessions))
    app.add_handler(CommandHandler("newsession", handle_newsession))
    app.add_handler(CommandHandler("cleansessions", handle_cleansessions))
    app.add_handler(CommandHandler("sessioninfo", handle_sessioninfo))
    app.add_handler(CommandHandler("compact", handle_compact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app
```

---

## Testing Procedures

### Test 1: Session Creation and Storage

**Objective:** Verify session ID is created and stored correctly.

**Steps:**
1. Send `/start` command
2. Send message: "Hello Claude"
3. Check logs for session ID
4. Send `/sessioninfo` command

**Expected Output:**
```
📊 Session Information
==============================

🆔 ID: `claude_abc123def456`

📅 Created: 2026-02-04 10:30:45
📅 Modified: 2026-02-04 10:30:47

💾 Size: 12.34 KB
🔄 Turns: 1

📁 Location: `~/.claude/projects/claude_abc123def456/`
```

**Verification:**
- Session ID is extracted and stored
- Session file exists on disk
- Turn count is 1

### Test 2: Session Listing

**Objective:** Verify `/sessions` command lists user's sessions.

**Steps:**
1. Create 3 sessions by sending `/newsession` between messages
2. Send messages in each session
3. Send `/sessions` command

**Expected Output:**
```
📚 Your Claude Sessions
==============================
👉 user_123_abc12345...
   📅 2026-02-04 10:35 | 💾 15.2KB | 🔄 3 turns

2. user_123_def67890...
   📅 2026-02-04 10:30 | 💾 8.5KB | 🔄 1 turns

3. user_123_ghi24680...
   📅 2026-02-04 10:25 | 💾 5.1KB | 🔄 2 turns

💡 Use /newsession to start fresh
💡 Use /cleansessions to delete old sessions
```

**Verification:**
- Current session is marked with 👉
- Sessions are sorted by most recent first
- Metadata (size, turns, date) is accurate

### Test 3: Session Isolation

**Objective:** Verify users don't see each other's sessions.

**Steps:**
1. User A creates session and sends message
2. User B creates session and sends message
3. User A sends `/sessions` - should only see User A's sessions
4. User B sends `/sessions` - should only see User B's sessions

**Expected Result:**
- User A sees only sessions starting with `user_A_ID_`
- User B sees only sessions starting with `user_B_ID_`
- No cross-contamination

### Test 4: New Session Creation

**Objective:** Verify `/newsession` creates a fresh session.

**Steps:**
1. Send message: "Remember the number 42"
2. Claude responds, confirming
3. Send `/newsession`
4. Send message: "What number did I tell you?"
5. Claude should not remember 42

**Expected Output:**
```
🆕 New session started!

Previous session: `claude_abc123`

Send a message to begin.
```

Then:
```
🤖 Claude:

I don't recall you mentioning any specific number. This appears to be the start of our conversation.
```

**Verification:**
- Session ID changes
- Context is not carried over
- Turn count resets to 0

### Test 5: Session Cleanup

**Objective:** Verify `/cleansessions` deletes old sessions.

**Steps:**
1. Create test session directory:
   ```bash
   mkdir -p ~/.claude/projects/user_123_oldtest
   touch ~/.claude/projects/user_123_oldtest/history.json
   # Set modification time to 31 days ago
   touch -t 202501010000 ~/.claude/projects/user_123_oldtest
   ```
2. Send `/cleansessions` command
3. Verify old session is deleted

**Expected Output:**
```
🗑️ Cleaned up 1 old session(s)
(older than 30 days)
```

**Verification:**
```bash
ls ~/.claude/projects/user_123_oldtest
# Should return: No such file or directory
```

### Test 6: Session Persistence Across Restarts

**Objective:** Verify session ID survives bot restart.

**Steps:**
1. Send message, note session ID from `/sessioninfo`
2. Restart bot: `docker-compose restart telegram-bot`
3. Send another message
4. Check `/sessioninfo` - session ID should be same

**Expected Result:**
- Session ID unchanged after restart
- Conversation context continues
- Turn count increments correctly

### Test 7: Missing Session Handling

**Objective:** Verify graceful handling when session file is deleted.

**Steps:**
1. Create session, send message
2. Note session ID
3. Manually delete session:
   ```bash
   rm -rf ~/.claude/projects/<session_id>
   ```
4. Send another message

**Expected Behavior:**
- Bot creates new session automatically
- No crash or error
- User is informed old session was lost

---

## Acceptance Criteria

### Functional Requirements

- [ ] Session IDs are extracted from Claude output correctly
- [ ] Session IDs are stored per user in persistence
- [ ] `/sessions` command lists all user sessions
- [ ] `/newsession` command creates fresh session
- [ ] `/cleansessions` deletes sessions older than 30 days
- [ ] `/sessioninfo` shows detailed session information
- [ ] Sessions persist across bot restarts
- [ ] Users only see their own sessions (isolation)

### Data Management

- [ ] Session files are stored in `~/.claude/projects/`
- [ ] Session metadata (size, turns, dates) is accurate
- [ ] Old sessions are cleaned up automatically
- [ ] Missing sessions are handled gracefully
- [ ] Session listing is sorted by most recent

### Performance

- [ ] Session listing is fast (< 500ms for 100 sessions)
- [ ] Session cleanup doesn't block bot operation
- [ ] File operations don't cause timeout

### Error Handling

- [ ] Missing session directory handled gracefully
- [ ] Corrupted session files don't crash bot
- [ ] Permission errors are logged and reported
- [ ] Invalid session IDs handled properly

---

## Troubleshooting Guide

### Issue 1: Session directory not found

**Symptoms:**
- `/sessions` returns empty list
- `/sessioninfo` says session not found

**Diagnosis:**
```bash
ls -la ~/.claude/projects/
```

**Solutions:**
- Create directory: `mkdir -p ~/.claude/projects/`
- Check Claude Code creates sessions properly
- Verify permissions: `chmod 755 ~/.claude/projects/`

### Issue 2: Sessions not isolated between users

**Symptoms:**
- User A sees User B's sessions

**Diagnosis:**
- Check session ID format
- Verify user_filter logic in `list_sessions()`

**Solutions:**
- Ensure session IDs include user ID: `user_{user_id}_`
- Fix filter logic in code
- Clean up incorrectly named sessions

### Issue 3: Cleanup deletes active session

**Symptoms:**
- Current session deleted by cleanup

**Diagnosis:**
- Check if session was recently modified
- Verify max_age_days calculation

**Solutions:**
- Exclude current session from cleanup
- Update session modification time on each use
- Reduce max_age_days value

---

## Rollback Procedure

### Quick Rollback

Remove session management commands:

```bash
git checkout HEAD~1 bot/bot.py
docker-compose restart telegram-bot
```

Bot will still work but without session management features.

---

## Next Steps

After completing Step 10:

1. **Proceed to Step 11:** Response Formatting
2. **Test full workflow:** Voice → Transcription → Claude → Response
3. **Optimize:** Session cleanup scheduling, disk usage monitoring

---

**Step Status:** Ready for Implementation
**Next Step:** Step 11 - Response Formatting
**Estimated Completion:** 1 hour
