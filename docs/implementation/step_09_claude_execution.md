# Step 9: Claude Code Headless Execution

**Phase:** 3 - Claude Code Integration
**Estimated Time:** 1-2 hours
**Prerequisites:** Steps 1-8 completed
**Dependencies:** Claude Code CLI, subprocess module, JSON parsing

---

## Overview

This step implements headless execution of Claude Code commands via subprocess calls. The bot will execute Claude commands with user prompts, parse the streaming JSON output, and extract meaningful responses to send back to users via Telegram.

### Context

Claude Code CLI supports headless execution with several output formats:
- `--output-format stream-json`: Streaming JSON events (recommended)
- `--output-format json`: Single JSON response
- `--output-format text`: Plain text output

We'll use `stream-json` format for real-time progress updates and detailed event parsing.

### Goals

1. Execute Claude Code via subprocess with proper timeout handling
2. Parse streaming JSON output to extract responses
3. Handle Claude Code errors gracefully
4. Implement command timeout and cancellation
5. Capture file changes and tool usage
6. Test with various command types

---

## Implementation Details

### 9.1 Claude Code Command Structure

Claude Code accepts several important flags:

```bash
claude -p "prompt text" \
  --output-format stream-json \
  --max-turns 10 \
  --resume <session-id> \
  --workspace /workspace
```

### 9.2 Subprocess Execution Module

**File: `bot/claude_executor.py`**

Create a dedicated module for Claude execution:

```python
#!/usr/bin/env python3
"""
Claude Code execution module for headless operation.
Handles subprocess execution, output parsing, and error handling.
"""

import subprocess
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

# Claude Code executable path
CLAUDE_EXECUTABLE = "claude"

# Default workspace directory
DEFAULT_WORKSPACE = Path("/workspace")

# Command timeout in seconds
DEFAULT_TIMEOUT = 120  # 2 minutes


@dataclass
class ClaudeResponse:
    """Structured response from Claude Code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    files_modified: List[str] = None
    tools_used: List[str] = None
    turn_count: int = 0
    raw_events: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.files_modified is None:
            self.files_modified = []
        if self.tools_used is None:
            self.tools_used = []
        if self.raw_events is None:
            self.raw_events = []


class ClaudeExecutor:
    """Execute Claude Code commands and parse output."""

    def __init__(
        self,
        workspace: Path = DEFAULT_WORKSPACE,
        timeout: int = DEFAULT_TIMEOUT,
        max_turns: int = 10
    ):
        self.workspace = workspace
        self.timeout = timeout
        self.max_turns = max_turns

    def execute(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        output_format: str = "stream-json"
    ) -> ClaudeResponse:
        """
        Execute a Claude Code command.

        Args:
            prompt: The user's prompt/request
            session_id: Optional session ID to resume conversation
            output_format: Output format (stream-json, json, or text)

        Returns:
            ClaudeResponse object with execution results
        """
        # Build command
        cmd = self._build_command(prompt, session_id, output_format)

        logger.info(f"Executing Claude command: {' '.join(cmd[:3])}...")
        logger.debug(f"Full command: {cmd}")

        try:
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace),
                timeout=self.timeout,
                env=self._get_env()
            )

            # Parse output based on format
            if output_format == "stream-json":
                return self._parse_stream_json(result)
            elif output_format == "json":
                return self._parse_json(result)
            else:
                return self._parse_text(result)

        except subprocess.TimeoutExpired as e:
            logger.error(f"Claude command timeout after {self.timeout}s")
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Command timeout after {self.timeout} seconds"
            )

        except Exception as e:
            logger.error(f"Claude execution failed: {e}", exc_info=True)
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Execution error: {str(e)}"
            )

    def _build_command(
        self,
        prompt: str,
        session_id: Optional[str],
        output_format: str
    ) -> List[str]:
        """Build the Claude Code command with all arguments."""
        cmd = [
            CLAUDE_EXECUTABLE,
            "-p", prompt,
            "--output-format", output_format,
            "--max-turns", str(self.max_turns)
        ]

        # Add session resumption if provided
        if session_id:
            cmd.extend(["--resume", session_id])

        return cmd

    def _get_env(self) -> Dict[str, str]:
        """Get environment variables for Claude execution."""
        import os
        env = os.environ.copy()

        # Ensure ANTHROPIC_API_KEY is set
        if "ANTHROPIC_API_KEY" not in env:
            logger.warning("ANTHROPIC_API_KEY not in environment")

        return env

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

        # Parse line-by-line JSON events
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

                # Extract text content
                if event_type == 'content_block_delta':
                    delta = event.get('delta', {})
                    if delta.get('type') == 'text_delta':
                        text = delta.get('text', '')
                        output_parts.append(text)

                # Track tool usage
                elif event_type == 'content_block_start':
                    content_block = event.get('content_block', {})
                    if content_block.get('type') == 'tool_use':
                        tool_name = content_block.get('name', 'unknown')
                        tools_used.add(tool_name)

                # Track file modifications (if available in events)
                elif event_type == 'tool_result':
                    # Parse tool results for file operations
                    pass

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON line: {line[:100]}")
                continue

        output = ''.join(output_parts).strip()

        # Extract session ID from events if present
        session_id = None
        for event in events:
            if 'session_id' in event:
                session_id = event['session_id']
                break

        return ClaudeResponse(
            success=True,
            output=output if output else "(Claude completed task with no text output)",
            session_id=session_id,
            files_modified=files_modified,
            tools_used=list(tools_used),
            raw_events=events
        )

    def _parse_json(self, result: subprocess.CompletedProcess) -> ClaudeResponse:
        """Parse JSON output from Claude Code."""
        if result.returncode != 0:
            return ClaudeResponse(
                success=False,
                output="",
                error=result.stderr.strip()
            )

        try:
            data = json.loads(result.stdout)
            return ClaudeResponse(
                success=True,
                output=data.get('content', [{}])[0].get('text', ''),
                session_id=data.get('session_id')
            )
        except json.JSONDecodeError as e:
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Failed to parse Claude output: {e}"
            )

    def _parse_text(self, result: subprocess.CompletedProcess) -> ClaudeResponse:
        """Parse text output from Claude Code."""
        if result.returncode != 0:
            return ClaudeResponse(
                success=False,
                output="",
                error=result.stderr.strip()
            )

        return ClaudeResponse(
            success=True,
            output=result.stdout.strip()
        )

    def compact_session(self, session_id: str) -> bool:
        """
        Compact a Claude session to reduce context size.

        Args:
            session_id: The session ID to compact

        Returns:
            True if successful, False otherwise
        """
        cmd = [
            CLAUDE_EXECUTABLE,
            "-p", "/compact",
            "--resume", session_id
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace),
                timeout=30  # Compact should be quick
            )

            success = result.returncode == 0
            if success:
                logger.info(f"Successfully compacted session {session_id}")
            else:
                logger.error(f"Failed to compact session: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"Compact failed: {e}")
            return False
```

### 9.3 Integration with Bot

**File: `bot/bot.py`**

Update the bot to use the ClaudeExecutor:

```python
#!/usr/bin/env python3
"""
Telegram bot for Claude Code voice control.
"""

import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime

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
import openai

# Import our Claude executor
from claude_executor import ClaudeExecutor, ClaudeResponse

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.environ.get('ALLOWED_USER_IDS', '').split(',')
    if uid.strip()
]

# Set OpenAI API key
openai.api_key = DEEPGRAM_API_KEY

# Workspace directory
WORKSPACE_DIR = Path('/workspace')

# Initialize Claude executor
claude_executor = ClaudeExecutor(
    workspace=WORKSPACE_DIR,
    timeout=120,  # 2 minute timeout
    max_turns=10
)

# Session persistence
SESSIONS_DIR = Path('sessions')
SESSIONS_DIR.mkdir(exist_ok=True)
persistence = PicklePersistence(filepath=str(SESSIONS_DIR / 'bot_data.pkl'))


def check_authorization(user_id: int) -> bool:
    """Check if user is authorized."""
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


def initialize_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Initialize user data with defaults."""
    if 'claude_session_id' not in context.user_data:
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0
        context.user_data['last_active'] = datetime.now().isoformat()


async def execute_claude_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str
):
    """
    Execute a Claude Code command and send response to user.

    Args:
        update: Telegram update object
        context: Bot context
        prompt: User's prompt/command
    """
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
            # Handle execution error
            error_text = response.error or "Unknown error"
            await status_msg.edit_text(
                f"❌ Claude encountered an error:\n\n"
                f"```\n{error_text[:3000]}\n```",
                parse_mode='Markdown'
            )
            return

        # Update session ID if returned
        if response.session_id:
            context.user_data['claude_session_id'] = response.session_id
            logger.info(f"Updated session ID: {response.session_id}")

        # Increment turn count
        context.user_data['turn_count'] = context.user_data.get('turn_count', 0) + 1
        turn_count = context.user_data['turn_count']

        # Auto-compact every 20 turns
        if turn_count >= 20:
            logger.info(f"Auto-compacting session after {turn_count} turns")
            if claude_executor.compact_session(context.user_data['claude_session_id']):
                context.user_data['turn_count'] = 0
                await update.message.reply_text("🗜️ Session auto-compacted")

        # Format response
        output_text = response.output

        # Add metadata if tools were used
        metadata_parts = []
        if response.tools_used:
            metadata_parts.append(f"🔧 Tools: {', '.join(response.tools_used)}")
        if response.files_modified:
            metadata_parts.append(f"📝 Modified: {len(response.files_modified)} files")

        metadata = "\n".join(metadata_parts)

        # Truncate if too long (Telegram limit: 4096 chars)
        max_length = 3800
        if len(output_text) > max_length:
            output_text = output_text[:max_length] + "\n\n...(truncated)"

        # Create inline keyboard for actions
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data='approve'),
                InlineKeyboardButton("❌ Reject", callback_data='reject')
            ],
            [
                InlineKeyboardButton("📝 Show Diff", callback_data='diff'),
                InlineKeyboardButton("📊 Git Status", callback_data='gitstatus')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Format final message
        final_message = f"🤖 Claude:\n\n{output_text}"
        if metadata:
            final_message += f"\n\n{metadata}"

        # Update status message with response
        await status_msg.edit_text(
            final_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Unexpected error executing Claude: {e}", exc_info=True)
        await status_msg.edit_text(
            f"💥 Unexpected error:\n```\n{str(e)[:3000]}\n```",
            parse_mode='Markdown'
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    text = update.message.text
    logger.info(f"Text message from user {user_id}: {text[:100]}")

    await execute_claude_command(update, context, text)


async def handle_compact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compact command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_id = context.user_data.get('claude_session_id')

    if not session_id:
        await update.message.reply_text("❌ No active session to compact")
        return

    await update.message.reply_text("⏳ Compacting session...")

    success = claude_executor.compact_session(session_id)

    if success:
        context.user_data['turn_count'] = 0
        await update.message.reply_text(
            "✅ Session compacted successfully!\n"
            "Turn count reset to 0."
        )
    else:
        await update.message.reply_text(
            "❌ Failed to compact session.\n"
            "Check logs for details."
        )


def build_application():
    """Build the Telegram bot application."""
    app = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .persistence(persistence) \
        .build()

    # Register handlers
    app.add_handler(CommandHandler("compact", handle_compact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


def main():
    """Start the bot."""
    app = build_application()

    logger.info("Starting bot with Claude Code integration")
    logger.info(f"Workspace: {WORKSPACE_DIR}")

    if WEBHOOK_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=WEBHOOK_URL,
            allowed_updates=Update.ALL_TYPES
        )
    else:
        logger.info("Using polling mode")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
```

### 9.4 Update Dockerfile/Requirements

**File: `bot/requirements.txt`**

```txt
python-telegram-bot[webhooks]==21.9
openai==1.59.5
anthropic==0.41.0
```

No changes needed - we're using subprocess to call Claude Code CLI directly.

---

## Testing Procedures

### Test 1: Basic Claude Execution

**Objective:** Verify Claude Code can be executed via subprocess.

**Steps:**
1. Start bot locally or in Docker
2. Send text message: "Hello Claude, what can you do?"
3. Wait for response

**Expected Output:**
```
🤖 Claude:

I'm Claude, an AI assistant created by Anthropic. I can help you with:
- Writing and editing code
- Creating files and projects
- Answering questions
- Refactoring and debugging
...
```

**Verification:**
- Response appears within 10 seconds
- No error messages
- Inline keyboard appears with Approve/Reject buttons

### Test 2: Session Resumption

**Objective:** Verify session context is maintained across messages.

**Steps:**
1. Send: "Create a file called test.py with a hello world function"
2. Wait for response, note session ID from logs
3. Send: "Now add a main function that calls it"
4. Verify Claude remembers the previous context

**Expected Output:**
```
🤖 Claude:

I'll add a main function to test.py that calls the hello_world function...

[Shows updated code with both functions]
```

**Verification:**
- Claude references the previously created file
- Session ID is the same in logs for both commands
- Turn count increments: 1 → 2

### Test 3: Error Handling

**Objective:** Verify graceful handling of Claude errors.

**Steps:**
1. Temporarily set invalid ANTHROPIC_API_KEY
2. Send message: "Create a test file"
3. Observe error handling

**Expected Output:**
```
❌ Claude encountered an error:

```
Error: Invalid API key
```
```

**Verification:**
- Error message is user-friendly
- Bot doesn't crash
- Logs contain detailed error information

### Test 4: Timeout Handling

**Objective:** Verify command timeout works correctly.

**Steps:**
1. Modify timeout to 5 seconds in `claude_executor`
2. Send complex command: "Analyze this entire codebase and refactor everything"
3. Wait for timeout

**Expected Output (after 5 seconds):**
```
❌ Claude encountered an error:

Command timeout after 5 seconds
```

**Verification:**
- Timeout occurs after exactly 5 seconds
- Process is killed (check with `ps aux | grep claude`)
- Bot remains responsive

### Test 5: Tool Usage Tracking

**Objective:** Verify tool usage is tracked and displayed.

**Steps:**
1. Send: "Create a file called utils.py with a helper function"
2. Check response for tool usage metadata

**Expected Output:**
```
🤖 Claude:

I'll create utils.py with a helper function...

🔧 Tools: WriteFile
```

**Verification:**
- Tools used are listed
- Correct tool names appear

### Test 6: Long Response Handling

**Objective:** Verify long responses are truncated properly.

**Steps:**
1. Send: "Generate a detailed explanation of Python decorators with 20 examples"
2. Check that response is truncated if > 3800 chars

**Expected Output:**
```
🤖 Claude:

[Long explanation...]

...(truncated)
```

**Verification:**
- Message doesn't exceed Telegram's 4096 char limit
- Truncation indicator is shown
- No Telegram API errors in logs

### Test 7: Auto-Compact

**Objective:** Verify auto-compact triggers after 20 turns.

**Steps:**
1. Send 20 simple messages: "Hello 1", "Hello 2", ..., "Hello 20"
2. On 20th message, verify compact is triggered

**Expected Output (after 20th message):**
```
🗜️ Session auto-compacted
```

**Verification:**
- Compact message appears after turn 20
- Turn count resets to 0 (check with /status)
- Session continues working after compact

### Test 8: Manual Compact

**Objective:** Verify /compact command works.

**Steps:**
1. Start a session, send a few messages
2. Send `/compact` command
3. Verify session is compacted

**Expected Output:**
```
⏳ Compacting session...

✅ Session compacted successfully!
Turn count reset to 0.
```

**Verification:**
- Turn count resets to 0
- Session ID remains the same
- Subsequent messages work normally

### Test 9: Stream JSON Parsing

**Objective:** Verify streaming JSON events are parsed correctly.

**Steps:**
1. Enable debug logging:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```
2. Send a message
3. Check logs for parsed events

**Expected Log Output:**
```
DEBUG: Parsed event: {'type': 'message_start', ...}
DEBUG: Parsed event: {'type': 'content_block_delta', 'delta': {'type': 'text_delta', 'text': 'Hello'}}
...
```

**Verification:**
- All JSON lines are parsed successfully
- No JSON parsing errors in logs
- Events are structured correctly

---

## Acceptance Criteria

### Functional Requirements

- [ ] Claude Code executes successfully via subprocess
- [ ] Streaming JSON output is parsed correctly
- [ ] Text responses are extracted and displayed
- [ ] Session IDs are captured and stored
- [ ] Session resumption works with `--resume` flag
- [ ] Tool usage is tracked and displayed
- [ ] Auto-compact triggers after 20 turns
- [ ] Manual `/compact` command works
- [ ] Errors are handled gracefully

### Performance Requirements

- [ ] Commands complete within 2 minute timeout
- [ ] Response parsing is < 100ms
- [ ] No memory leaks on repeated execution
- [ ] Subprocess cleanup is proper (no zombie processes)

### Error Handling

- [ ] Invalid API key shows user-friendly error
- [ ] Timeout errors are caught and reported
- [ ] JSON parsing errors don't crash bot
- [ ] Subprocess errors are logged properly
- [ ] Network errors are handled gracefully

### Integration

- [ ] Works with persistence from Step 8
- [ ] Session IDs persist across bot restarts
- [ ] Turn counts increment correctly
- [ ] User data is updated properly

---

## Troubleshooting Guide

### Issue 1: Claude command not found

**Symptoms:**
- Error: "FileNotFoundError: [Errno 2] No such file or directory: 'claude'"

**Diagnosis:**
```bash
# Check if Claude is installed
which claude

# Check PATH
echo $PATH
```

**Solutions:**
- Install Claude Code CLI: `npm install -g @claude/cli`
- Or use full path: `CLAUDE_EXECUTABLE = "/usr/local/bin/claude"`
- In Docker, ensure Claude is installed in container

### Issue 2: Timeout on all commands

**Symptoms:**
- Every command times out after 2 minutes
- Bot says "Command timeout after 120 seconds"

**Diagnosis:**
```bash
# Test Claude directly
time claude -p "Hello" --output-format text

# Check if it's hanging
```

**Solutions:**
- Increase timeout: `timeout=300` (5 minutes)
- Check ANTHROPIC_API_KEY is valid
- Check network connectivity from container
- Check Claude API status

### Issue 3: Empty responses

**Symptoms:**
- Bot says "(Claude completed task with no text output)"
- No error, but no meaningful response

**Diagnosis:**
```bash
# Test Claude directly
claude -p "Hello" --output-format stream-json

# Check if output format is correct
```

**Solutions:**
- Verify `--output-format stream-json` is supported
- Check Claude Code CLI version: `claude --version`
- Try different output format: `json` or `text`
- Check for stderr output

### Issue 4: JSON parsing errors

**Symptoms:**
- Logs show: "Failed to parse JSON line"
- Responses are incomplete

**Diagnosis:**
- Enable debug logging to see raw output
- Check if output is actually JSON

**Solutions:**
- Handle non-JSON lines gracefully
- Use `output_format='text'` as fallback
- Update Claude Code CLI to latest version

### Issue 5: Session not resuming

**Symptoms:**
- Claude doesn't remember previous context
- Each message starts fresh conversation

**Diagnosis:**
```bash
# Check session files
ls -la ~/.claude/projects/

# Check if session ID is being passed
# (Add debug logging)
```

**Solutions:**
- Verify `session_id` is not None
- Check `--resume` flag is being passed
- Verify session ID format is correct
- Check Claude session files exist

### Issue 6: High API costs

**Symptoms:**
- Anthropic bill higher than expected
- Many tokens consumed

**Diagnosis:**
- Check Anthropic console for usage
- Review `max_turns` setting

**Solutions:**
- Reduce `max_turns` from 10 to 5
- Enable auto-compact more frequently (every 10 turns)
- Use `/compact` regularly
- Monitor token usage per request

---

## Rollback Procedure

### Quick Rollback

1. **Revert to echo bot:**
   ```bash
   # In bot.py, replace execute_claude_command with:
   async def execute_claude_command(update, context, prompt):
       await update.message.reply_text(f"Echo: {prompt}")
   ```

2. **Restart bot:**
   ```bash
   docker-compose restart telegram-bot
   ```

### Full Rollback

1. **Revert code:**
   ```bash
   git checkout HEAD~1 bot/bot.py
   rm bot/claude_executor.py
   ```

2. **Restart services:**
   ```bash
   docker-compose restart telegram-bot
   ```

### Data Recovery

Session data is preserved in `sessions/bot_data.pkl`, so no data loss on rollback.

---

## Next Steps

After completing Step 9:

1. **Proceed to Step 10:** Session ID Management
   - Implement proper session ID extraction from Claude output
   - Add session listing and switching
   - Implement session cleanup

2. **Test integration:**
   - Verify sessions work end-to-end
   - Test with voice messages (from Step 7)
   - Ensure persistence works correctly

3. **Performance tuning:**
   - Monitor execution times
   - Optimize timeout values
   - Consider parallel execution for multiple users

---

**Step Status:** Ready for Implementation
**Next Step:** Step 10 - Session ID Management
**Estimated Completion:** 1-2 hours
