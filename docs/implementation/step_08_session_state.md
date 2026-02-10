# Step 8: Session State Management

**Phase:** 2 - Voice Processing Pipeline
**Estimated Time:** 1 hour
**Prerequisites:** Steps 1-7 completed
**Dependencies:** Python telegram bot, PicklePersistence

---

## Overview

This step implements persistent session state management for the Telegram bot using `PicklePersistence`. This ensures that user data, conversation history, and Claude session IDs persist across bot restarts, providing a seamless user experience.

### Context

Without persistence, each bot restart would lose:
- User session data
- Conversation context
- Claude session IDs
- Turn counts for auto-compact

PicklePersistence stores this data in a pickle file on disk, automatically saving and loading state.

### Goals

1. Implement PicklePersistence for the Telegram bot
2. Store user-specific session data (Claude session IDs, turn counts)
3. Test persistence across bot restarts
4. Verify data isolation between users
5. Implement proper cleanup of stale sessions

---

## Implementation Details

### 8.1 Directory Structure

Create the sessions directory for storing persistence files:

```bash
mkdir -p sessions
chmod 700 sessions  # Restrict permissions to owner only
```

### 8.2 PicklePersistence Integration

**File: `bot/bot.py`**

Add the PicklePersistence import and initialization:

```python
#!/usr/bin/env python3
"""
Telegram bot for Claude Code voice control with persistent state.
"""

import os
import logging
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    PicklePersistence,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.environ.get('ALLOWED_USER_IDS', '').split(',')
    if uid.strip()
]

# Session persistence directory
SESSIONS_DIR = Path('sessions')
SESSIONS_DIR.mkdir(exist_ok=True)

# Initialize persistence
persistence = PicklePersistence(filepath=str(SESSIONS_DIR / 'bot_data.pkl'))

# Build application with persistence
def build_application():
    """Build the Telegram bot application with persistence."""
    return Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .persistence(persistence) \
        .build()

app = build_application()
```

### 8.3 User Data Schema

Define the user data structure that will be persisted:

```python
# User data schema (stored per user in context.user_data)
USER_DATA_SCHEMA = {
    'claude_session_id': None,      # str or None
    'turn_count': 0,                # int
    'last_active': None,            # datetime or None
    'workspace_path': '/workspace', # str
    'preferences': {                # dict
        'auto_compact': True,
        'show_transcription': True,
        'max_turns_before_compact': 20
    }
}

def initialize_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Initialize user data with default values if not present."""
    if 'claude_session_id' not in context.user_data:
        context.user_data.update(USER_DATA_SCHEMA.copy())

    # Update last active timestamp
    from datetime import datetime
    context.user_data['last_active'] = datetime.now().isoformat()
```

### 8.4 Session Management Functions

Add helper functions for session management:

```python
from datetime import datetime
import uuid

def get_or_create_session_id(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    """Get existing session ID or create a new one."""
    initialize_user_data(context)

    session_id = context.user_data.get('claude_session_id')

    if not session_id:
        # Generate new session ID
        session_id = f"user_{user_id}_{uuid.uuid4().hex[:8]}"
        context.user_data['claude_session_id'] = session_id
        context.user_data['turn_count'] = 0
        logger.info(f"Created new session for user {user_id}: {session_id}")

    return session_id

def increment_turn_count(context: ContextTypes.DEFAULT_TYPE) -> int:
    """Increment and return the current turn count."""
    initialize_user_data(context)
    context.user_data['turn_count'] = context.user_data.get('turn_count', 0) + 1
    return context.user_data['turn_count']

def reset_session(context: ContextTypes.DEFAULT_TYPE):
    """Reset the session to default state."""
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0
    logger.info("Session reset to default state")

def get_session_info(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get current session information."""
    initialize_user_data(context)
    return {
        'session_id': context.user_data.get('claude_session_id', 'No active session'),
        'turn_count': context.user_data.get('turn_count', 0),
        'last_active': context.user_data.get('last_active', 'Never'),
        'preferences': context.user_data.get('preferences', {})
    }
```

### 8.5 Updated Command Handlers

Update the /start, /status, and /clear handlers to use persistence:

```python
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with session initialization."""
    user = update.effective_user

    if not check_authorization(user.id):
        await update.message.reply_text("⛔ You are not authorized to use this bot.")
        return

    # Initialize user data
    initialize_user_data(context)

    session_info = get_session_info(context)
    session_status = "active" if session_info['session_id'] != 'No active session' else "new"

    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        f"I'm your Claude Code voice assistant.\n\n"
        f"📱 Send me a voice message with your coding task\n"
        f"💬 Or send a text message with your request\n"
        f"📝 I'll execute it and show you the results\n\n"
        f"📊 Session Status: {session_status}\n"
        f"🔄 Turn Count: {session_info['turn_count']}\n\n"
        f"Commands:\n"
        f"/start - Show this message\n"
        f"/status - Check current session\n"
        f"/clear - Clear conversation history\n"
        f"/compact - Manually compact session"
    )

async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_info = get_session_info(context)

    status_message = (
        f"📊 Current Status\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 User ID: {user_id}\n"
        f"🆔 Session ID: {session_info['session_id']}\n"
        f"🔄 Turn Count: {session_info['turn_count']}\n"
        f"📁 Workspace: {session_info.get('workspace_path', '/workspace')}\n"
        f"⏰ Last Active: {session_info['last_active']}\n\n"
        f"⚙️ Preferences:\n"
    )

    prefs = session_info.get('preferences', {})
    for key, value in prefs.items():
        status_message += f"  • {key}: {value}\n"

    await update.message.reply_text(status_message)

async def handle_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    old_session = context.user_data.get('claude_session_id', 'None')

    # Reset session
    reset_session(context)

    await update.message.reply_text(
        f"🗑️ Conversation history cleared!\n\n"
        f"Previous session: {old_session}\n"
        f"Starting fresh on next message."
    )

async def handle_compact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compact command for manual session compacting."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_id = context.user_data.get('claude_session_id')

    if not session_id:
        await update.message.reply_text("❌ No active session to compact")
        return

    await update.message.reply_text("⏳ Compacting session...")

    # This will be implemented in Step 9
    # For now, just reset turn count
    context.user_data['turn_count'] = 0

    await update.message.reply_text("✅ Session compacted! Turn count reset.")
```

### 8.6 Authorization Helper

```python
def check_authorization(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    if not ALLOWED_USER_IDS:
        logger.warning("No ALLOWED_USER_IDS configured - allowing all users")
        return True  # No restrictions if not configured
    return user_id in ALLOWED_USER_IDS
```

### 8.7 Main Function with Persistence

```python
def main():
    """Start the bot with persistence enabled."""
    # Create sessions directory
    SESSIONS_DIR.mkdir(exist_ok=True)

    # Register handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("clear", handle_clear))
    app.add_handler(CommandHandler("compact", handle_compact))

    logger.info(f"Starting bot with persistence at {SESSIONS_DIR / 'bot_data.pkl'}")
    logger.info(f"Allowed user IDs: {ALLOWED_USER_IDS if ALLOWED_USER_IDS else 'All users'}")

    # Run with webhook (for production on Coolify)
    WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # Fall back to polling for local development
        logger.info("No WEBHOOK_URL configured, using polling mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
```

### 8.8 Update requirements.txt

Ensure the correct version of python-telegram-bot is specified:

**File: `bot/requirements.txt`**

```txt
python-telegram-bot[webhooks]==21.9
openai==1.59.5
anthropic==0.41.0
```

---

## Testing Procedures

### Test 1: Session Creation

**Objective:** Verify that a new session is created for first-time users.

**Steps:**
1. Start the bot: `python bot/bot.py`
2. Send `/start` command in Telegram
3. Send `/status` command

**Expected Output:**
```
📊 Current Status
━━━━━━━━━━━━━━━━
👤 User ID: 123456789
🆔 Session ID: user_123456789_a1b2c3d4
🔄 Turn Count: 0
📁 Workspace: /workspace
⏰ Last Active: 2026-02-04T10:30:45.123456
```

**Verification:**
- Session ID should be generated in format `user_{id}_{hash}`
- Turn count should be 0
- Workspace path should be set

### Test 2: Session Persistence Across Restarts

**Objective:** Verify that session data persists when bot restarts.

**Steps:**
1. Send `/start` command
2. Note the session ID from `/status`
3. Stop the bot (Ctrl+C)
4. Verify pickle file exists: `ls -la sessions/bot_data.pkl`
5. Restart the bot: `python bot/bot.py`
6. Send `/status` command again

**Expected Output:**
- Session ID should be the same as before restart
- Turn count should be preserved
- Last active timestamp should be preserved

**Verification Command:**
```bash
# Check pickle file was created
stat sessions/bot_data.pkl

# Should show file with recent modification time
```

### Test 3: Multi-User Isolation

**Objective:** Verify that different users have isolated session data.

**Steps:**
1. Add two user IDs to `ALLOWED_USER_IDS`
2. Send `/start` from User A's Telegram
3. Send `/status` from User A - note session ID
4. Send `/start` from User B's Telegram
5. Send `/status` from User B - note session ID
6. Verify session IDs are different

**Expected Output:**
- User A: `Session ID: user_111111111_abc123de`
- User B: `Session ID: user_222222222_xyz789pq`

**Verification:**
- Session IDs must be different
- No data leakage between users

### Test 4: Session Clear

**Objective:** Verify that `/clear` properly resets session state.

**Steps:**
1. Send `/start` command
2. Send `/status` - note session ID and turn count
3. Send `/clear` command
4. Send `/status` again

**Expected Output (after clear):**
```
🗑️ Conversation history cleared!

Previous session: user_123456789_a1b2c3d4
Starting fresh on next message.
```

**Verification:**
- After `/clear`, session ID should be reset to None
- Turn count should be 0
- Previous session ID should be shown in clear confirmation

### Test 5: Turn Count Increment

**Objective:** Verify turn counting works correctly (preparation for auto-compact).

**Steps:**
1. Modify code temporarily to increment turn count on each `/status` call:
   ```python
   async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
       increment_turn_count(context)
       # ... rest of handler
   ```
2. Send `/status` multiple times
3. Verify turn count increments: 0 → 1 → 2 → 3...

**Expected Output:**
```
Turn Count: 3  # After third /status call
```

**Verification:**
- Turn count should increment consistently
- Count should persist across bot restarts

### Test 6: Pickle File Integrity

**Objective:** Verify pickle file is not corrupted and can be read.

**Steps:**
1. Run bot and create session
2. Stop bot gracefully (Ctrl+C)
3. Test pickle file can be loaded:

```python
# test_persistence.py
import pickle
from pathlib import Path

pickle_file = Path('sessions/bot_data.pkl')

try:
    with open(pickle_file, 'rb') as f:
        data = pickle.load(f)
    print("✅ Pickle file is valid")
    print(f"Data keys: {data.keys()}")
    print(f"User data: {data.get('user_data', {})}")
except Exception as e:
    print(f"❌ Pickle file corrupted: {e}")
```

**Expected Output:**
```
✅ Pickle file is valid
Data keys: dict_keys(['user_data', 'chat_data', 'bot_data', 'callback_data'])
User data: {123456789: {'claude_session_id': 'user_123456789_a1b2c3d4', ...}}
```

### Test 7: Cleanup Old Sessions

**Objective:** Test session cleanup functionality (future enhancement).

**Steps:**
1. Create a cleanup function:

```python
from datetime import datetime, timedelta

def cleanup_old_sessions(max_age_days: int = 7):
    """Remove sessions inactive for more than max_age_days."""
    try:
        with open(SESSIONS_DIR / 'bot_data.pkl', 'rb') as f:
            data = pickle.load(f)

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        user_data = data.get('user_data', {})

        removed_count = 0
        for user_id, udata in list(user_data.items()):
            last_active_str = udata.get('last_active')
            if last_active_str:
                last_active = datetime.fromisoformat(last_active_str)
                if last_active < cutoff_date:
                    del user_data[user_id]
                    removed_count += 1

        with open(SESSIONS_DIR / 'bot_data.pkl', 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Cleaned up {removed_count} old sessions")
        return removed_count
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 0
```

2. Test with artificially old session:
   - Manually edit pickle file to set old `last_active` date
   - Run cleanup function
   - Verify old session was removed

---

## Acceptance Criteria

### Functional Requirements

- [ ] PicklePersistence is properly initialized with `sessions/bot_data.pkl`
- [ ] User data schema includes: `claude_session_id`, `turn_count`, `last_active`, `preferences`
- [ ] New users get initialized with default user data
- [ ] Session IDs are generated in format `user_{id}_{hash}`
- [ ] `/status` command shows current session information
- [ ] `/clear` command resets session to default state
- [ ] Turn count increments correctly (tested via temporary code)
- [ ] Bot restart preserves all user session data

### Data Integrity

- [ ] Pickle file is created in `sessions/` directory
- [ ] Pickle file is readable and not corrupted after bot restart
- [ ] Multiple users have isolated session data (no leakage)
- [ ] Concurrent users don't interfere with each other's sessions
- [ ] File permissions on `sessions/` are restrictive (700)

### Error Handling

- [ ] Bot handles missing pickle file gracefully (creates new one)
- [ ] Bot handles corrupted pickle file (logs error, starts fresh)
- [ ] Missing user data fields are initialized with defaults
- [ ] Invalid session IDs are handled gracefully

### Performance

- [ ] Pickle load time is < 100ms for typical session sizes
- [ ] Pickle save time is < 100ms
- [ ] Session data size is reasonable (< 10KB per user)

---

## Troubleshooting Guide

### Issue 1: Pickle file not created

**Symptoms:**
- `sessions/bot_data.pkl` doesn't exist after running bot
- `/status` command doesn't show persistent session

**Diagnosis:**
```bash
# Check directory exists
ls -la sessions/

# Check permissions
stat sessions/

# Check bot logs
docker logs telegram-bot | grep -i persistence
```

**Solutions:**
- Ensure `sessions/` directory exists: `mkdir -p sessions`
- Check write permissions: `chmod 700 sessions`
- Verify `persistence` is passed to Application builder
- Check for errors in bot logs

### Issue 2: Session data not persisting across restarts

**Symptoms:**
- Session ID changes after bot restart
- Turn count resets to 0 after restart

**Diagnosis:**
```bash
# Check if pickle file was modified during bot run
ls -l sessions/bot_data.pkl

# Test loading pickle manually
python3 -c "import pickle; print(pickle.load(open('sessions/bot_data.pkl', 'rb')))"
```

**Solutions:**
- Verify bot is shutting down gracefully (not killed forcefully)
- Check that `PicklePersistence` is configured correctly
- Ensure `update_persistence` is not set to False
- Add explicit flush in shutdown handler if needed

### Issue 3: Corrupted pickle file

**Symptoms:**
- Bot crashes on startup with pickle-related error
- `pickle.UnpicklingError` in logs

**Diagnosis:**
```bash
# Try to load pickle file
python3 << EOF
import pickle
try:
    with open('sessions/bot_data.pkl', 'rb') as f:
        pickle.load(f)
    print("✅ File is valid")
except Exception as e:
    print(f"❌ Corrupted: {e}")
EOF
```

**Solutions:**
- Backup corrupted file: `mv sessions/bot_data.pkl sessions/bot_data.pkl.bak`
- Remove corrupted file: `rm sessions/bot_data.pkl`
- Restart bot (will create fresh pickle file)
- Investigate root cause (disk full, abrupt shutdown, etc.)

### Issue 4: Permission denied errors

**Symptoms:**
- `PermissionError: [Errno 13] Permission denied: 'sessions/bot_data.pkl'`

**Diagnosis:**
```bash
# Check file ownership and permissions
ls -la sessions/
stat sessions/bot_data.pkl

# Check process user
ps aux | grep bot.py
```

**Solutions:**
- Fix ownership: `chown $USER:$USER sessions/bot_data.pkl`
- Fix permissions: `chmod 600 sessions/bot_data.pkl`
- Ensure sessions directory is writable: `chmod 700 sessions/`

### Issue 5: Data leakage between users

**Symptoms:**
- User A sees User B's session ID or data
- Session data mixed between users

**Diagnosis:**
- Add debug logging:
  ```python
  logger.info(f"User {user_id} data: {context.user_data}")
  ```
- Check if user_id is being used correctly as key

**Solutions:**
- Verify `context.user_data` is used (not `context.bot_data`)
- Ensure user_id is correct in all handlers
- Check for global variable pollution
- Review handler code for proper context usage

### Issue 6: Session data grows too large

**Symptoms:**
- Pickle file is very large (> 10MB)
- Bot becomes slow over time
- Disk space issues

**Diagnosis:**
```bash
# Check pickle file size
ls -lh sessions/bot_data.pkl

# Analyze pickle contents
python3 << EOF
import pickle
import sys
data = pickle.load(open('sessions/bot_data.pkl', 'rb'))
print(f"Total size: {sys.getsizeof(data)} bytes")
print(f"User count: {len(data.get('user_data', {}))}")
for uid, udata in data.get('user_data', {}).items():
    print(f"User {uid}: {sys.getsizeof(udata)} bytes")
EOF
```

**Solutions:**
- Implement session cleanup for inactive users
- Limit data stored per user
- Remove old session IDs that are no longer valid
- Consider using database instead of pickle for large deployments

---

## Rollback Procedure

### Quick Rollback (5 minutes)

If Step 8 implementation causes issues:

1. **Revert code changes:**
   ```bash
   git checkout HEAD~1 bot/bot.py
   ```

2. **Remove persistence files:**
   ```bash
   rm -rf sessions/
   ```

3. **Restart bot:**
   ```bash
   # If running locally
   pkill -f bot.py
   python bot/bot.py

   # If running in Docker
   docker-compose restart telegram-bot
   ```

4. **Verify bot works without persistence:**
   - Send `/start` command
   - Verify bot responds (even if session doesn't persist)

### Full Rollback (10 minutes)

If you need to completely remove persistence functionality:

1. **Backup current state (optional):**
   ```bash
   cp -r sessions/ sessions_backup/
   git stash
   ```

2. **Revert to pre-Step 8 commit:**
   ```bash
   git log --oneline  # Find commit hash before Step 8
   git checkout <commit-hash>
   ```

3. **Clean up:**
   ```bash
   rm -rf sessions/
   docker-compose down
   docker-compose up -d
   ```

4. **Verify:**
   - Bot should work without persistence
   - Sessions won't persist across restarts (acceptable for rollback)

### Data Recovery

If you need to recover data from backup:

```bash
# Stop bot
docker-compose stop telegram-bot

# Restore from backup
cp sessions_backup/bot_data.pkl sessions/

# Restart bot
docker-compose start telegram-bot

# Verify data was restored
# Send /status in Telegram - should show previous session
```

---

## Next Steps

After completing Step 8:

1. **Proceed to Step 9:** Claude Code Headless Execution
   - Will use `claude_session_id` from persisted user data
   - Will increment `turn_count` for each interaction
   - Will implement auto-compact based on turn count

2. **Testing integration:**
   - Step 9 will test that session IDs persist correctly
   - Step 10 will test session resumption with `--resume` flag

3. **Optional enhancements:**
   - Add session cleanup cron job
   - Implement session backup mechanism
   - Add session export/import functionality

---

## Additional Notes

### Performance Considerations

- **Pickle file size:** Should be < 1MB for 100 users
- **Save frequency:** Automatic after each update (python-telegram-bot handles this)
- **Load time:** Should be negligible (< 100ms)

### Security Considerations

- **File permissions:** `sessions/` directory should be 700 (owner only)
- **Sensitive data:** Don't store API keys or passwords in user_data
- **User isolation:** Verified by using `context.user_data` (per-user storage)

### Alternatives to PicklePersistence

If pickle doesn't meet your needs, consider:

1. **DictPersistence:** In-memory only (good for testing)
2. **Custom persistence:** Implement `BasePersistence` with database backend
3. **Redis:** For distributed deployments
4. **PostgreSQL:** For structured data and queries

Example custom persistence stub:

```python
from telegram.ext.basepersistence import BasePersistence

class PostgresPersistence(BasePersistence):
    async def get_user_data(self):
        # Query from database
        pass

    async def update_user_data(self, user_id, data):
        # Save to database
        pass
```

---

**Step Status:** Ready for Implementation
**Next Step:** Step 9 - Claude Code Headless Execution
**Estimated Completion:** 1 hour
