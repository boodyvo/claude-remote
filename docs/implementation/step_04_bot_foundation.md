# Step 4: Telegram Bot Foundation

**Estimated Time:** 1 hour
**Prerequisites:**
- Steps 1-3 completed (project setup, credentials, Docker running)
- Telegram bot token from Step 2
- Docker Compose services running
- bot/requirements.txt with dependencies installed

**Deliverable:** Minimal working Telegram bot that responds to /start command and implements user authorization

## Overview

This step implements the foundational structure of the Telegram bot. We'll create a minimal but production-ready bot that:
- Responds to the /start command with a welcome message
- Implements user authentication (only allowed users can interact)
- Uses proper logging
- Runs in polling mode locally (webhook mode for production later)
- Has clean error handling

This foundation will be extended in subsequent steps to add voice processing and Claude Code integration. Getting the basics right now ensures a stable platform for adding features later.

## Implementation Details

### What to Build

1. **Bot Configuration:** Load environment variables and configure bot
2. **/start Command Handler:** Welcome message and bot introduction
3. **User Authorization:** Check user IDs against allowlist
4. **Logging:** Structured logging for debugging
5. **Main Loop:** Bot startup and polling mechanism
6. **Error Handling:** Graceful error handling and recovery

### How to Implement

#### Step 4.1: Create bot/config.py for Configuration Management

```python
# bot/config.py
"""
Configuration management for Telegram bot.
Loads and validates environment variables.
"""

import os
import sys
from typing import List

def get_required_env(var_name: str) -> str:
    """Get required environment variable or exit."""
    value = os.getenv(var_name)
    if not value:
        print(f"ERROR: {var_name} environment variable is required but not set")
        sys.exit(1)
    return value

def get_optional_env(var_name: str, default: str = "") -> str:
    """Get optional environment variable with default."""
    return os.getenv(var_name, default)

# Required API keys
TELEGRAM_TOKEN = get_required_env('TELEGRAM_TOKEN')
DEEPGRAM_API_KEY = get_required_env('DEEPGRAM_API_KEY')
ANTHROPIC_API_KEY = get_required_env('ANTHROPIC_API_KEY')

# Optional configuration
WEBHOOK_URL = get_optional_env('WEBHOOK_URL')
BOT_MODE = get_optional_env('BOT_MODE', 'polling')  # polling or webhook

# User authorization
ALLOWED_USER_IDS_STR = get_optional_env('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS: List[int] = []
if ALLOWED_USER_IDS_STR:
    try:
        ALLOWED_USER_IDS = [
            int(uid.strip())
            for uid in ALLOWED_USER_IDS_STR.split(',')
            if uid.strip()
        ]
    except ValueError as e:
        print(f"ERROR: Invalid ALLOWED_USER_IDS format: {e}")
        sys.exit(1)

# Paths
WORKSPACE_DIR = '/workspace'
SESSIONS_DIR = './sessions'

# Bot settings
MAX_MESSAGE_LENGTH = 4000  # Telegram limit is 4096, leave buffer
LOG_LEVEL = get_optional_env('LOG_LEVEL', 'INFO')

# Validate configuration
def validate_config():
    """Validate configuration and print summary."""
    print("=" * 50)
    print("Bot Configuration:")
    print("=" * 50)
    print(f"Telegram Token: {'✓ Set' if TELEGRAM_TOKEN else '✗ Missing'}")
    print(f"OpenAI API Key: {'✓ Set' if DEEPGRAM_API_KEY else '✗ Missing'}")
    print(f"Anthropic API Key: {'✓ Set' if ANTHROPIC_API_KEY else '✗ Missing'}")
    print(f"Bot Mode: {BOT_MODE}")
    print(f"Webhook URL: {WEBHOOK_URL if WEBHOOK_URL else 'Not set (using polling)'}")
    print(f"Allowed User IDs: {ALLOWED_USER_IDS if ALLOWED_USER_IDS else 'All users allowed (NOT RECOMMENDED)'}")
    print(f"Workspace Directory: {WORKSPACE_DIR}")
    print(f"Sessions Directory: {SESSIONS_DIR}")
    print(f"Log Level: {LOG_LEVEL}")
    print("=" * 50)

if __name__ == '__main__':
    validate_config()
```

#### Step 4.2: Update bot/bot.py with Complete Implementation

```python
#!/usr/bin/env python3
"""
Telegram bot for Claude Code voice control.
This is the foundation implementation (Step 4).
Voice and Claude integration will be added in Steps 5-10.
"""

import os
import sys
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    filters
)

# Import configuration
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, config.LOG_LEVEL)
)
logger = logging.getLogger(__name__)


def check_authorization(user_id: int) -> bool:
    """
    Check if user is authorized to use the bot.

    Args:
        user_id: Telegram user ID

    Returns:
        True if authorized, False otherwise
    """
    # If no restrictions configured, allow all users
    if not config.ALLOWED_USER_IDS:
        logger.warning("No ALLOWED_USER_IDS configured - all users can access bot")
        return True

    # Check if user is in allowlist
    return user_id in config.ALLOWED_USER_IDS


async def handle_start(update: Update, context) -> None:
    """
    Handle /start command.

    Sends welcome message and bot introduction.
    """
    user = update.effective_user
    user_id = user.id

    logger.info(f"/start command from user {user_id} ({user.first_name})")

    # Check authorization
    if not check_authorization(user_id):
        logger.warning(f"Unauthorized access attempt by user {user_id}")
        await update.message.reply_text(
            "⛔ You are not authorized to use this bot.\n\n"
            f"Your User ID: {user_id}\n\n"
            "Contact the bot administrator to request access."
        )
        return

    # Send welcome message
    welcome_message = (
        f"👋 Hello {user.first_name}!\n\n"
        "I'm your **Claude Code Remote Assistant**.\n\n"
        "🎤 **Voice Control**: Send me a voice message with your coding task\n"
        "💬 **Text Control**: Or send a text message with your request\n"
        "📝 **Interactive**: I'll execute tasks and show you the results\n\n"
        "**Available Commands:**\n"
        "/start - Show this message\n"
        "/status - Check current session info\n"
        "/clear - Clear conversation history\n"
        "/help - Detailed usage guide\n\n"
        "**Current Status:**\n"
        f"✓ Bot is running\n"
        f"✓ Your User ID: {user_id}\n"
        "⏳ Voice processing: Coming in Step 5\n"
        "⏳ Claude integration: Coming in Step 9\n\n"
        "Send me a text message to test basic functionality!"
    )

    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )


async def handle_help(update: Update, context) -> None:
    """Handle /help command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    help_message = (
        "**Claude Code Remote Assistant - Help**\n\n"
        "**How to Use:**\n\n"
        "1️⃣ **Voice Messages**\n"
        "   - Tap microphone icon in Telegram\n"
        "   - Speak your coding task clearly\n"
        "   - Bot will transcribe and execute\n\n"
        "2️⃣ **Text Messages**\n"
        "   - Type your request directly\n"
        "   - Bot will process immediately\n\n"
        "**Commands:**\n"
        "/start - Initialize bot\n"
        "/status - Check session info\n"
        "/clear - Reset conversation\n"
        "/help - Show this help\n\n"
        "**Tips:**\n"
        "• Speak clearly for best transcription\n"
        "• Be specific in your requests\n"
        "• Review changes before approving\n"
        "• Use /clear if Claude seems confused\n\n"
        "**Support:**\n"
        "Check the documentation for detailed guides."
    )

    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )


async def handle_status(update: Update, context) -> None:
    """Handle /status command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Get session info (placeholder for now)
    session_id = context.user_data.get('claude_session_id', 'No active session')
    turn_count = context.user_data.get('turn_count', 0)

    status_message = (
        "📊 **Bot Status**\n\n"
        f"**User:** {update.effective_user.first_name}\n"
        f"**User ID:** {user_id}\n"
        f"**Session ID:** {session_id}\n"
        f"**Turn Count:** {turn_count}\n"
        f"**Workspace:** {config.WORKSPACE_DIR}\n\n"
        "**Services:**\n"
        "✓ Bot running\n"
        "✓ User authorized\n"
        "⏳ Voice processing: Coming soon\n"
        "⏳ Claude Code: Coming soon"
    )

    await update.message.reply_text(
        status_message,
        parse_mode='Markdown'
    )


async def handle_clear(update: Update, context) -> None:
    """Handle /clear command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Clear user session data
    context.user_data.clear()
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0

    logger.info(f"Cleared session for user {user_id}")

    await update.message.reply_text(
        "🗑️ **Session Cleared**\n\n"
        "Conversation history has been reset.\n"
        "Starting fresh with next message!"
    )


async def handle_text(update: Update, context) -> None:
    """
    Handle text messages (placeholder for now).

    In future steps, this will process text commands via Claude.
    """
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    text = update.message.text
    logger.info(f"Text message from user {user_id}: {text}")

    # Echo response for now (will be replaced with Claude integration)
    response = (
        "📝 **Message Received**\n\n"
        f"You said: {text}\n\n"
        "⏳ Text processing will be implemented in Step 9 (Claude Integration)\n\n"
        "For now, I'm just echoing your message back."
    )

    await update.message.reply_text(
        response,
        parse_mode='Markdown'
    )


async def handle_voice(update: Update, context) -> None:
    """
    Handle voice messages (placeholder for now).

    In Step 5, this will download and convert voice.
    In Step 6, this will transcribe via Deepgram API.
    """
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    logger.info(f"Voice message from user {user_id}")

    await update.message.reply_text(
        "🎤 **Voice Message Received**\n\n"
        "⏳ Voice processing will be implemented in Steps 5-6:\n"
        "  - Step 5: Download & Convert\n"
        "  - Step 6: Whisper Transcription\n\n"
        "For now, send text messages to test the bot."
    )


async def error_handler(update: Update, context) -> None:
    """
    Handle errors in the bot.

    Logs errors and sends user-friendly message.
    """
    logger.error(f"Exception while handling an update: {context.error}", exc_info=True)

    # Try to notify user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ **An error occurred**\n\n"
            "The bot encountered an unexpected error.\n"
            "Please try again or contact support if the issue persists.\n\n"
            f"Error: {str(context.error)[:100]}"
        )


def main():
    """Start the bot."""
    # Validate configuration
    config.validate_config()

    # Create sessions directory if it doesn't exist
    Path(config.SESSIONS_DIR).mkdir(exist_ok=True)

    # Set up persistence
    persistence = PicklePersistence(
        filepath=f'{config.SESSIONS_DIR}/bot_data.pkl'
    )

    # Create application
    app = Application.builder() \
        .token(config.TELEGRAM_TOKEN) \
        .persistence(persistence) \
        .build()

    # Register command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("clear", handle_clear))

    # Register message handlers
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text
    ))
    app.add_handler(MessageHandler(
        filters.VOICE,
        handle_voice
    ))

    # Register error handler
    app.add_error_handler(error_handler)

    logger.info("=" * 50)
    logger.info("Bot starting...")
    logger.info(f"Mode: {config.BOT_MODE}")
    logger.info("=" * 50)

    # Start bot
    if config.BOT_MODE == 'webhook' and config.WEBHOOK_URL:
        # Webhook mode (for production)
        logger.info(f"Starting in webhook mode: {config.WEBHOOK_URL}")
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv('BOT_PORT', 8443)),
            webhook_url=config.WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        # Polling mode (for local development)
        logger.info("Starting in polling mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
```

#### Step 4.3: Update Docker Compose for Bot

Update the bot service in `docker-compose.yml`:

```yaml
  telegram-bot:
    image: python:3.11-slim
    container_name: telegram-bot
    working_dir: /app
    volumes:
      - ./bot:/app
      - ./sessions:/app/sessions
      - workspace:/workspace
      - claude-config:/root/.claude
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN:?}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:?}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?}
      - WEBHOOK_URL=${WEBHOOK_URL:-}
      - ALLOWED_USER_IDS=${ALLOWED_USER_IDS:-}
      - BOT_MODE=polling
      - LOG_LEVEL=INFO
    command: >
      bash -c "
        apt-get update &&
        apt-get install -y ffmpeg curl git &&
        pip install --no-cache-dir -r requirements.txt &&
        python bot.py
      "
    restart: unless-stopped
    networks:
      - claude-network
    depends_on:
      claudebox-web:
        condition: service_healthy
```

#### Step 4.4: Restart Services

```bash
# Rebuild and restart
docker-compose down
docker-compose up -d

# Watch logs
docker-compose logs -f telegram-bot
```

Expected logs:
```
Bot Configuration:
==================================================
Telegram Token: ✓ Set
OpenAI API Key: ✓ Set
Anthropic API Key: ✓ Set
Bot Mode: polling
Allowed User IDs: [123456789]
...
==================================================
Bot starting...
Mode: polling
==================================================
```

#### Step 4.5: Test the Bot

1. **Open Telegram** on your phone or desktop
2. **Find your bot** (search for the username you created in Step 2)
3. **Send /start command**

Expected response:
```
👋 Hello [Your Name]!

I'm your Claude Code Remote Assistant.

🎤 Voice Control: Send me a voice message with your coding task
💬 Text Control: Or send a text message with your request
📝 Interactive: I'll execute tasks and show you the results

Available Commands:
/start - Show this message
/status - Check current session info
/clear - Clear conversation history
/help - Detailed usage guide

Current Status:
✓ Bot is running
✓ Your User ID: 123456789
⏳ Voice processing: Coming in Step 5
⏳ Claude integration: Coming in Step 9

Send me a text message to test basic functionality!
```

4. **Send a text message**: "Hello bot"

Expected response:
```
📝 Message Received

You said: Hello bot

⏳ Text processing will be implemented in Step 9 (Claude Integration)

For now, I'm just echoing your message back.
```

5. **Test /status command**

Expected response showing your user ID, session info, etc.

6. **Test /help command**

Expected response with detailed help text.

### Code Examples

**Test Script to Validate Bot:**

```bash
cat > test_bot.sh << 'EOF'
#!/bin/bash
# Test bot is responding correctly

source .env

echo "Testing Telegram Bot..."
echo "========================"

# Function to send message to bot
send_message() {
    local chat_id=$1
    local text=$2

    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
        -d "chat_id=${chat_id}" \
        -d "text=${text}"
}

# Get bot info
echo "1. Testing bot token..."
response=$(curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe")
if echo "$response" | grep -q '"ok":true'; then
    echo "✓ Bot token is valid"
    bot_name=$(echo "$response" | grep -o '"first_name":"[^"]*"' | cut -d'"' -f4)
    echo "  Bot name: $bot_name"
else
    echo "✗ Bot token is invalid"
    exit 1
fi

# Check bot is running
echo ""
echo "2. Testing bot container..."
if docker ps | grep -q telegram-bot; then
    echo "✓ Bot container is running"
else
    echo "✗ Bot container is not running"
    exit 1
fi

# Check logs for startup message
echo ""
echo "3. Checking bot logs..."
if docker logs telegram-bot 2>&1 | grep -q "Bot starting"; then
    echo "✓ Bot started successfully"
else
    echo "⚠ Bot may not have started properly"
    echo "Check logs with: docker logs telegram-bot"
fi

# Check for errors in logs
echo ""
echo "4. Checking for errors..."
error_count=$(docker logs telegram-bot 2>&1 | grep -i error | wc -l)
if [ "$error_count" -eq 0 ]; then
    echo "✓ No errors in logs"
else
    echo "⚠ Found $error_count errors in logs"
    docker logs telegram-bot 2>&1 | grep -i error | tail -5
fi

echo ""
echo "========================"
echo "Bot validation complete!"
echo ""
echo "Next steps:"
echo "1. Open Telegram and find your bot"
echo "2. Send /start command"
echo "3. Test with text messages"
echo "4. Verify responses are working"
EOF

chmod +x test_bot.sh
./test_bot.sh
```

### Project Structure

After this step:

```
claude-remote-runner/
├── docker-compose.yml          # Updated bot service
├── bot/
│   ├── bot.py                  # ← UPDATED: Full bot implementation
│   ├── config.py               # ← NEW: Configuration management
│   └── requirements.txt
├── sessions/                   # Bot session data (created at runtime)
│   └── bot_data.pkl           # Persistence file
├── test_bot.sh                 # ← NEW: Bot validation script
└── ...
```

## Testing & Validation

### Test Cases

**Test 1: Bot Configuration Loads**
```bash
docker exec telegram-bot python config.py
# Expected: Configuration summary with all values
```

**Test 2: Bot Container Running**
```bash
docker ps | grep telegram-bot
# Expected: Container shows "Up" status
```

**Test 3: Bot Logs Show Startup**
```bash
docker logs telegram-bot | grep "Bot starting"
# Expected: Startup message present
```

**Test 4: /start Command Works**
- Send `/start` in Telegram
- Expected: Welcome message with formatted text

**Test 5: /help Command Works**
- Send `/help` in Telegram
- Expected: Help text with all commands listed

**Test 6: /status Command Works**
- Send `/status` in Telegram
- Expected: Status info with user ID and session details

**Test 7: /clear Command Works**
- Send `/clear` in Telegram
- Expected: Confirmation message

**Test 8: Text Messages Handled**
- Send "Test message" in Telegram
- Expected: Echo response

**Test 9: Voice Messages Handled (Placeholder)**
- Send voice message in Telegram
- Expected: "Coming soon" message

**Test 10: Authorization Works**
If you have ALLOWED_USER_IDS set, test with unauthorized user ID:
- Expected: "Not authorized" message

### Acceptance Criteria

- [ ] bot/config.py created with configuration management
- [ ] bot/bot.py updated with full bot implementation
- [ ] Docker Compose updated with new bot command
- [ ] Bot container starts without errors
- [ ] Bot logs show successful startup and configuration
- [ ] /start command returns welcome message
- [ ] /help command returns help text
- [ ] /status command returns status info
- [ ] /clear command clears session data
- [ ] Text messages receive echo response
- [ ] Voice messages receive placeholder response
- [ ] User authorization works (if configured)
- [ ] Unauthorized users are rejected (if allowlist configured)
- [ ] Error handling works (no crashes on invalid input)
- [ ] Session persistence works (bot_data.pkl created)
- [ ] Logs show INFO level messages
- [ ] No critical errors in logs

### How to Test

**Manual Test Procedure:**

```bash
# 1. Check configuration
docker exec telegram-bot python config.py

# 2. Check logs
docker logs telegram-bot --tail 50

# 3. Test all commands in Telegram:
#    /start
#    /help
#    /status
#    /clear

# 4. Send text message: "Hello"
# 5. Send voice message (if available)

# 6. Check session file created
docker exec telegram-bot ls -la sessions/
# Expected: bot_data.pkl exists

# 7. Test persistence across restarts
docker-compose restart telegram-bot
# Wait 30 seconds
# Send /status again
# Expected: Bot remembers previous state
```

## Troubleshooting

### Issue 1: Bot Not Responding in Telegram

**Symptoms:**
- Send /start command, no response
- Bot shows as offline

**Solutions:**

1. **Check bot is running:**
   ```bash
   docker logs telegram-bot --tail 50
   ```

2. **Check for errors:**
   ```bash
   docker logs telegram-bot | grep -i error
   ```

3. **Test token:**
   ```bash
   curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe"
   ```

4. **Check polling is working:**
   ```bash
   docker logs telegram-bot | grep -i polling
   # Should see: "Starting in polling mode"
   ```

5. **Restart bot:**
   ```bash
   docker-compose restart telegram-bot
   ```

### Issue 2: Import Error for config.py

**Symptoms:**
```
ModuleNotFoundError: No module named 'config'
```

**Solutions:**

1. **Check file exists:**
   ```bash
   docker exec telegram-bot ls -la /app/config.py
   ```

2. **Check Python path:**
   ```bash
   docker exec telegram-bot python -c "import sys; print(sys.path)"
   # /app should be in path
   ```

3. **Verify working directory:**
   ```yaml
   # In docker-compose.yml:
   working_dir: /app  # Must be set
   ```

### Issue 3: User Authorization Not Working

**Symptoms:**
- Authorized user sees "not authorized" message
- Or unauthorized user can access bot

**Solutions:**

1. **Check user ID is correct:**
   - Send message from @userinfobot to verify your ID
   - Compare with ALLOWED_USER_IDS in .env

2. **Check configuration loaded:**
   ```bash
   docker exec telegram-bot python config.py | grep "Allowed User"
   ```

3. **Check format:**
   ```bash
   # In .env, should be:
   ALLOWED_USER_IDS=123456789,987654321
   # NOT: ALLOWED_USER_IDS=[123456789,987654321]
   ```

4. **Restart after .env changes:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Issue 4: Session Persistence Not Working

**Symptoms:**
- Bot forgets data after restart
- bot_data.pkl not created

**Solutions:**

1. **Check sessions directory mounted:**
   ```bash
   docker inspect telegram-bot | grep -A 5 Mounts
   # Should show ./sessions:/app/sessions
   ```

2. **Check directory exists:**
   ```bash
   ls -la sessions/
   ```

3. **Check permissions:**
   ```bash
   chmod 755 sessions/
   ```

4. **Check PicklePersistence:**
   ```bash
   docker exec telegram-bot python -c "from telegram.ext import PicklePersistence; print('OK')"
   ```

### Issue 5: Markdown Formatting Not Working

**Symptoms:**
- Bot messages show raw markdown like **bold** instead of formatted text

**Solutions:**

**In bot.py, ensure:**
```python
await update.message.reply_text(
    message,
    parse_mode='Markdown'  # ← This is required
)
```

**Alternative: Use HTML:**
```python
parse_mode='HTML'
# Then use <b>bold</b> instead of **bold**
```

### Issue 6: Bot Crashes on Startup

**Symptoms:**
- Container keeps restarting
- Logs show Python traceback

**Solutions:**

1. **Check syntax:**
   ```bash
   docker exec telegram-bot python -m py_compile bot.py
   ```

2. **Check imports:**
   ```bash
   docker exec telegram-bot python -c "from telegram import Update; print('OK')"
   ```

3. **Run bot directly:**
   ```bash
   docker-compose run --rm telegram-bot python bot.py
   # See full error output
   ```

4. **Check environment variables:**
   ```bash
   docker exec telegram-bot env | grep -E "TELEGRAM|OPENAI|ANTHROPIC"
   ```

## Rollback Procedure

### Restore Previous bot.py

```bash
# If using Git
git checkout HEAD~1 bot/bot.py

# Restart bot
docker-compose restart telegram-bot
```

### Remove config.py (Use Inline Config)

```bash
# Remove config.py
rm bot/config.py

# Update bot.py to load config inline
# (Replace import config with inline os.getenv() calls)

# Restart
docker-compose restart telegram-bot
```

### Revert to Placeholder Bot

```bash
cat > bot/bot.py << 'EOF'
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Placeholder bot running")
while True:
    time.sleep(60)
EOF

docker-compose restart telegram-bot
```

## Next Step

Once all acceptance criteria are met, proceed to:

**Step 5: Voice Message Download & Conversion**
- File: `docs/implementation/step_05_voice_download.md`
- Duration: 1 hour
- Goal: Implement voice message download from Telegram and conversion to WAV format using ffmpeg

Before proceeding, ensure:
1. Bot responds to /start command
2. All commands work (/help, /status, /clear)
3. Text messages are handled
4. User authorization works
5. No errors in bot logs
6. Session persistence works
7. test_bot.sh passes all checks

**Checkpoint:** You now have a working Telegram bot with proper structure, authorization, and command handling. The next steps will add voice processing and Claude Code integration.

**Save Your Work:**
```bash
git add bot/bot.py bot/config.py docker-compose.yml test_bot.sh
git commit -m "Implement Telegram bot foundation (Step 4)

- Add bot/config.py for configuration management
- Implement complete bot.py with all command handlers
- Add /start, /help, /status, /clear commands
- Implement user authorization system
- Add error handling and logging
- Update Docker Compose for bot service
- Add test_bot.sh validation script
- Bot runs in polling mode for local development
- All tests passing"
```
