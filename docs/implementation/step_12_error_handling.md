# Step 12: Error Handling & Logging

**Phase:** 3 - Claude Code Integration
**Estimated Time:** 30 minutes
**Prerequisites:** Steps 1-11 completed
**Dependencies:** Python logging, exception handling

---

## Overview

This step implements comprehensive error handling and structured logging throughout the bot. Proper error handling ensures the bot remains operational even when things go wrong, and good logging helps debug issues quickly.

### Context

Types of errors to handle:
- API errors (Telegram, OpenAI, Anthropic)
- Network timeouts
- File system errors
- Invalid user input
- Rate limiting
- Authentication failures
- Subprocess errors
- Resource exhaustion

### Goals

1. Implement try-catch blocks for all critical operations
2. Add structured logging with appropriate levels
3. Create user-friendly error messages
4. Log all errors with context for debugging
5. Implement graceful degradation
6. Add error metrics/monitoring hooks
7. Test all error paths

---

## Implementation Details

### 12.1 Logging Configuration

**File: `bot/logging_config.py`**

Create centralized logging configuration:

```python
#!/usr/bin/env python3
"""
Logging configuration for the Telegram bot.
Provides structured logging with different levels and formatters.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Log directory
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
MAIN_LOG = LOG_DIR / 'bot.log'
ERROR_LOG = LOG_DIR / 'error.log'
ACCESS_LOG = LOG_DIR / 'access.log'

# Log format
DETAILED_FORMAT = (
    '%(asctime)s - %(name)s - %(levelname)s - '
    '[%(filename)s:%(lineno)d] - %(message)s'
)

SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files in addition to console
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(SIMPLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    if log_to_file:
        # Main log file (rotating, 10MB max, 5 backups)
        main_handler = RotatingFileHandler(
            MAIN_LOG,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(DETAILED_FORMAT)
        main_handler.setFormatter(main_formatter)
        root_logger.addHandler(main_handler)

        # Error log file (errors and above only)
        error_handler = RotatingFileHandler(
            ERROR_LOG,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(DETAILED_FORMAT)
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

    logging.info("Logging configured successfully")


def log_access(user_id: int, action: str, details: str = ""):
    """
    Log user access/actions to access log.

    Args:
        user_id: Telegram user ID
        action: Action performed (e.g., "voice_message", "text_command")
        details: Additional details
    """
    access_logger = logging.getLogger('access')

    # Ensure access log handler exists
    if not access_logger.handlers:
        access_handler = RotatingFileHandler(
            ACCESS_LOG,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        access_formatter = logging.Formatter(
            '%(asctime)s - User:%(user_id)s - %(action)s - %(details)s'
        )
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)

    access_logger.info(
        "",
        extra={
            'user_id': user_id,
            'action': action,
            'details': details
        }
    )


class ContextLogger:
    """Logger with additional context."""

    def __init__(self, name: str, **context):
        self.logger = logging.getLogger(name)
        self.context = context

    def _format_message(self, message: str) -> str:
        """Add context to log message."""
        if self.context:
            ctx = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{ctx}] {message}"
        return message

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_message(message), **kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_message(message), **kwargs)
```

### 12.2 Error Handler Classes

**File: `bot/error_handlers.py`**

```python
#!/usr/bin/env python3
"""
Error handling utilities and custom exceptions.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes for categorization."""
    # API errors
    TELEGRAM_API_ERROR = "telegram_api_error"
    OPENAI_API_ERROR = "openai_api_error"
    ANTHROPIC_API_ERROR = "anthropic_api_error"

    # Authentication/Authorization
    UNAUTHORIZED = "unauthorized"
    INVALID_API_KEY = "invalid_api_key"

    # Execution errors
    CLAUDE_EXECUTION_ERROR = "claude_execution_error"
    TIMEOUT = "timeout"
    SUBPROCESS_ERROR = "subprocess_error"

    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"

    # Input errors
    INVALID_INPUT = "invalid_input"
    MESSAGE_TOO_LONG = "message_too_long"

    # Rate limiting
    RATE_LIMITED = "rate_limited"

    # System errors
    OUT_OF_MEMORY = "out_of_memory"
    UNKNOWN_ERROR = "unknown_error"


class BotError(Exception):
    """Base exception for bot errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.user_message = user_message or message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            'error_code': self.error_code.value,
            'message': str(self),
            'user_message': self.user_message,
            'details': self.details
        }


class APIError(BotError):
    """API-related errors."""
    pass


class ExecutionError(BotError):
    """Execution-related errors."""
    pass


class InputError(BotError):
    """User input errors."""
    pass


def handle_error(
    error: Exception,
    context: str = "",
    user_id: Optional[int] = None
) -> str:
    """
    Handle an error and return user-friendly message.

    Args:
        error: The exception that occurred
        context: Context where error occurred
        user_id: User ID if available

    Returns:
        User-friendly error message
    """
    # Log the error
    log_message = f"Error in {context}: {str(error)}"
    if user_id:
        log_message = f"[User {user_id}] {log_message}"

    # Determine severity and user message
    if isinstance(error, BotError):
        logger.error(log_message, extra=error.to_dict())
        return error.user_message

    # Handle known exception types
    elif isinstance(error, TimeoutError) or "timeout" in str(error).lower():
        logger.error(f"{log_message} - TIMEOUT")
        return (
            "⏱️ Operation timed out. The task may still be running.\n\n"
            "Try a simpler request or check back later."
        )

    elif isinstance(error, PermissionError):
        logger.error(f"{log_message} - PERMISSION_DENIED")
        return (
            "🔒 Permission denied. Unable to access required resource.\n\n"
            "Please contact the administrator."
        )

    elif isinstance(error, FileNotFoundError):
        logger.error(f"{log_message} - FILE_NOT_FOUND")
        return (
            "📁 Required file not found.\n\n"
            "The system may need to be reconfigured."
        )

    elif "rate limit" in str(error).lower():
        logger.warning(f"{log_message} - RATE_LIMITED")
        return (
            "⏱️ Rate limit exceeded. Please wait a moment and try again.\n\n"
            "Tip: Reduce the frequency of requests."
        )

    elif "api key" in str(error).lower() or "unauthorized" in str(error).lower():
        logger.error(f"{log_message} - AUTH_ERROR")
        return (
            "🔑 Authentication error. The API key may be invalid or expired.\n\n"
            "Please contact the administrator."
        )

    elif "out of memory" in str(error).lower():
        logger.critical(f"{log_message} - OUT_OF_MEMORY")
        return (
            "💾 System out of memory. Please try again later.\n\n"
            "If this persists, contact the administrator."
        )

    else:
        # Unknown error
        logger.error(f"{log_message} - UNKNOWN", exc_info=True)
        return (
            "💥 An unexpected error occurred.\n\n"
            "The error has been logged. Please try again or contact support."
        )


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str])
    """
    try:
        result = func(*args, **kwargs)
        return (True, result, None)
    except Exception as e:
        error_msg = handle_error(e, context=func.__name__)
        return (False, None, error_msg)
```

### 12.3 Bot Integration

**File: `bot/bot.py`** (update)

```python
from logging_config import setup_logging, log_access, ContextLogger
from error_handlers import handle_error, BotError, ErrorCode, safe_execute

# Setup logging at startup
setup_logging(level=logging.INFO, log_to_file=True)

logger = logging.getLogger(__name__)

# ... existing code ...

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages with comprehensive error handling."""
    user_id = update.effective_user.id
    user_logger = ContextLogger(__name__, user_id=user_id, handler='voice')

    try:
        # Log access
        log_access(user_id, 'voice_message', f"duration={update.message.voice.duration}s")

        # Authorization check
        if not check_authorization(user_id):
            user_logger.warning("Unauthorized access attempt")
            await update.message.reply_text("⛔ Unauthorized")
            return

        user_logger.info("Processing voice message")

        # Download voice file
        try:
            voice = await context.bot.get_file(update.message.voice.file_id)
            voice_file = f'sessions/voice_{user_id}_{datetime.now().timestamp()}.ogg'
            await voice.download_to_drive(voice_file)
            user_logger.debug(f"Downloaded voice file: {voice_file}")
        except Exception as e:
            user_logger.error(f"Failed to download voice: {e}")
            await update.message.reply_text(
                "❌ Failed to download voice message. Please try again."
            )
            return

        # Convert to WAV
        wav_file = voice_file.replace('.ogg', '.wav')
        try:
            result = subprocess.run(
                ['ffmpeg', '-y', '-i', voice_file, '-ar', '16000', '-ac', '1', wav_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                raise Exception(f"ffmpeg error: {result.stderr}")
            user_logger.debug("Audio conversion successful")
        except subprocess.TimeoutExpired:
            user_logger.error("ffmpeg timeout")
            await update.message.reply_text("❌ Audio conversion timed out")
            return
        except Exception as e:
            user_logger.error(f"Audio conversion failed: {e}")
            await update.message.reply_text("❌ Failed to process audio")
            return
        finally:
            # Cleanup
            Path(voice_file).unlink(missing_ok=True)

        # Transcribe
        try:
            with open(wav_file, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            transcribed_text = transcript['text']
            user_logger.info(f"Transcribed: {transcribed_text[:100]}")
            await update.message.reply_text(f"🎤 Heard: {transcribed_text}")
        except Exception as e:
            user_logger.error(f"Transcription failed: {e}")
            error_msg = handle_error(e, "transcription", user_id)
            await update.message.reply_text(error_msg)
            return
        finally:
            Path(wav_file).unlink(missing_ok=True)

        # Execute Claude command
        await execute_claude_command(update, context, transcribed_text)

    except Exception as e:
        user_logger.error(f"Unexpected error in voice handler: {e}", exc_info=True)
        error_msg = handle_error(e, "voice_handler", user_id)
        await update.message.reply_text(error_msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with error handling."""
    user_id = update.effective_user.id
    user_logger = ContextLogger(__name__, user_id=user_id, handler='text')

    try:
        log_access(user_id, 'text_message', f"length={len(update.message.text)}")

        if not check_authorization(user_id):
            user_logger.warning("Unauthorized access attempt")
            await update.message.reply_text("⛔ Unauthorized")
            return

        text = update.message.text
        user_logger.info(f"Text message: {text[:100]}")

        await execute_claude_command(update, context, text)

    except Exception as e:
        user_logger.error(f"Error in text handler: {e}", exc_info=True)
        error_msg = handle_error(e, "text_handler", user_id)
        await update.message.reply_text(error_msg)


async def error_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler for unhandled exceptions."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

    # Try to notify user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "💥 Sorry, something went wrong. The error has been logged."
            )
        except Exception:
            pass  # Can't send message to user


def main():
    """Start the bot with error handling."""
    try:
        app = build_application()

        # Register error handler
        app.add_error_handler(error_callback)

        # Register other handlers
        # ... existing handler registration ...

        logger.info("Starting bot...")
        logger.info(f"Log files: {LOG_DIR.absolute()}")

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

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
```

---

## Testing Procedures

### Test 1: API Error Handling

**Objective:** Verify API errors are handled gracefully.

**Steps:**
1. Set invalid DEEPGRAM_API_KEY
2. Send voice message
3. Verify error handling

**Expected Output:**
```
🔑 Authentication error. The API key may be invalid or expired.

Please contact the administrator.
```

**Verification:**
- Error logged to error.log
- User gets friendly message
- Bot doesn't crash

### Test 2: Timeout Handling

**Objective:** Verify timeouts are handled.

**Steps:**
1. Set short timeout (5 seconds)
2. Send complex request
3. Wait for timeout

**Expected Output:**
```
⏱️ Operation timed out. The task may still be running.

Try a simpler request or check back later.
```

**Verification:**
- Timeout logged
- Process cleaned up
- Bot remains responsive

### Test 3: File System Errors

**Objective:** Test file permission errors.

**Steps:**
1. Remove write permission: `chmod 444 sessions/`
2. Send voice message
3. Verify error handling
4. Restore: `chmod 755 sessions/`

**Expected Output:**
```
🔒 Permission denied. Unable to access required resource.

Please contact the administrator.
```

### Test 4: Log File Creation

**Objective:** Verify logs are created and rotated.

**Steps:**
1. Start bot
2. Send various messages
3. Check log files

**Expected Files:**
```bash
ls -lh logs/
# Should show:
# bot.log
# error.log
# access.log
```

**Verification:**
- All log files exist
- Contain appropriate entries
- Rotation works (check after 10MB)

### Test 5: Access Logging

**Objective:** Verify user actions are logged.

**Steps:**
1. Send voice message
2. Send text message
3. Check access.log

**Expected Content:**
```
2026-02-04 10:30:45 - User:123456789 - voice_message - duration=5s
2026-02-04 10:31:12 - User:123456789 - text_message - length=25
```

### Test 6: Structured Error Logging

**Objective:** Verify errors have full context.

**Steps:**
1. Trigger error
2. Check error.log

**Expected Content:**
```
2026-02-04 10:30:45 - bot - ERROR - [bot.py:123] - [User 123456789] Error in transcription: API error
```

### Test 7: Global Error Handler

**Objective:** Test unhandled exception catching.

**Steps:**
1. Add intentional error in code
2. Trigger it
3. Verify global handler catches it

**Expected Behavior:**
- Error logged
- User notified
- Bot doesn't crash

---

## Acceptance Criteria

### Error Handling

- [ ] All API errors caught and handled
- [ ] Timeouts handled gracefully
- [ ] File system errors handled
- [ ] Network errors handled
- [ ] Rate limiting handled
- [ ] Unknown errors handled with fallback message

### Logging

- [ ] Logs written to files in logs/ directory
- [ ] Log rotation works (10MB max per file)
- [ ] Different log levels used appropriately
- [ ] Structured logging with context
- [ ] Access logging tracks all user actions
- [ ] Error logs contain stack traces

### User Experience

- [ ] Error messages are user-friendly
- [ ] Technical details hidden from users
- [ ] Actionable suggestions provided
- [ ] Bot remains operational after errors

### Monitoring

- [ ] All errors logged with error code
- [ ] User context included in logs
- [ ] Performance metrics can be extracted from logs
- [ ] Log files don't fill disk (rotation working)

---

## Troubleshooting Guide

### Issue 1: Logs not created

**Diagnosis:**
```bash
ls -la logs/
```

**Solutions:**
- Ensure logs/ directory exists and is writable
- Check file permissions
- Verify logging configuration is called

### Issue 2: Log files too large

**Diagnosis:**
```bash
du -sh logs/*
```

**Solutions:**
- Check rotation is working
- Reduce retention (fewer backups)
- Lower log level (INFO instead of DEBUG)

### Issue 3: Errors not logged

**Diagnosis:**
- Check log level
- Verify error handler is registered

**Solutions:**
- Ensure logging.error() is called
- Check log level isn't set too high
- Verify file permissions

---

## Rollback Procedure

Remove error handling (basic fallback):

```python
# Minimal error handling
try:
    # ... code ...
except Exception as e:
    logger.error(f"Error: {e}")
    await update.message.reply_text("Error occurred")
```

---

## Next Steps

After Step 12:

1. **Proceed to Step 13:** Inline Keyboard Implementation
2. **Monitor logs** in production
3. **Set up alerts** for error rate thresholds

---

**Step Status:** Ready for Implementation
**Next Step:** Step 13 - Inline Keyboard Implementation
**Estimated Completion:** 30 minutes
