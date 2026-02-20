#!/usr/bin/env python3
"""
Telegram bot for Claude Code voice control.
This is the foundation implementation (Step 4).
Voice and Claude integration will be added in Steps 5-10.
"""

import os
import sys
import logging
import subprocess
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PicklePersistence,
    filters
)
from deepgram import DeepgramClient, PrerecordedOptions

# Import configuration
import config

# Import Claude executor
from claude_executor import ClaudeExecutor, ClaudeResponse

# Import response formatter
from formatters import ResponseFormatter

# Import logging and error handling
from logging_config import setup_logging, log_access, ContextLogger
from error_handlers import handle_error, BotError, ErrorCode

# Import keyboards and callback handlers
from keyboards import KeyboardBuilder
from callback_handlers import handle_callback_query

# Import git operations
from git_operations import GitOperations, GitStatus, GitDiff

# Setup logging before anything else
setup_logging(level=getattr(logging, config.LOG_LEVEL), log_to_file=True)
logger = logging.getLogger(__name__)

# Initialize Deepgram client
deepgram = DeepgramClient(config.DEEPGRAM_API_KEY)

# Initialize Claude executor
claude_executor = ClaudeExecutor()

# Initialize response formatter
formatter = ResponseFormatter()

# Initialize keyboard builder
keyboards = KeyboardBuilder()

# Initialize git operations
git_ops = GitOperations()

# Change state constants (for approval workflow)
CHANGE_STATE_PENDING = 'pending'
CHANGE_STATE_APPROVED = 'approved'
CHANGE_STATE_REJECTED = 'rejected'


# User data schema (stored per user in context.user_data)
USER_DATA_SCHEMA = {
    'claude_session_id': None,      # str or None
    'turn_count': 0,                # int
    'last_active': None,            # datetime or None
    'workspace_path': '/workspace', # str
    'last_transcription': None,     # str or None
    'github_repo': None,            # str: "owner/repo" or None
    'repo_path': None,              # str: local path to cloned repo
    'preferences': {                # dict
        'auto_compact': True,
        'show_transcription': True,
        'max_turns_before_compact': 20
    }
}

WORKSPACE_BASE = Path('/workspace')


def initialize_user_data(context):
    """Initialize user data with default values if not present."""
    if 'claude_session_id' not in context.user_data:
        context.user_data.update(USER_DATA_SCHEMA.copy())

    # Update last active timestamp
    context.user_data['last_active'] = datetime.now().isoformat()


def get_or_create_session_id(context, user_id: int) -> Optional[str]:
    """
    Get existing Claude session ID.

    Returns None if no session exists (Claude will create one).
    Session IDs are UUIDs created by Claude CLI, not custom IDs.
    """
    initialize_user_data(context)

    session_id = context.user_data.get('claude_session_id')

    if session_id:
        logger.info(f"Using existing session for user {user_id}: {session_id}")
    else:
        logger.info(f"No existing session for user {user_id}, Claude will create new one")

    return session_id


def increment_turn_count(context) -> int:
    """Increment and return the current turn count."""
    initialize_user_data(context)
    context.user_data['turn_count'] = context.user_data.get('turn_count', 0) + 1
    return context.user_data['turn_count']


def reset_session(context):
    """Reset the session to default state."""
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0
    logger.info("Session reset to default state")


def get_session_info(context) -> dict:
    """Get current session information."""
    initialize_user_data(context)
    session_id = context.user_data.get('claude_session_id')
    return {
        'session_id': session_id if session_id else 'No active session',
        'turn_count': context.user_data.get('turn_count', 0),
        'last_active': context.user_data.get('last_active', 'Never'),
        'workspace_path': context.user_data.get('workspace_path', '/workspace'),
        'preferences': context.user_data.get('preferences', {})
    }


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

    # Initialize user data and get session info
    initialize_user_data(context)
    session_info = get_session_info(context)
    session_status = "active" if session_info['session_id'] != 'No active session' else "new"

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
        "/help - Detailed usage guide\n\n"
        "**Session Management:**\n"
        "/sessions - List your sessions\n"
        "/sessioninfo - Show active session details\n"
        "/newsession - Start a new session\n"
        "/cleansessions - Delete old sessions (>30 days)\n"
        "/clear - Clear conversation history\n\n"
        "**Git Commands:**\n"
        "/gitinit - Initialize git repository\n"
        "/gitstatus - Show repository status\n"
        "/gitdiff - Show diff of changes\n"
        "/commit [message] - Commit changes\n"
        "/gitlog - Show commit history\n\n"
        "**Session Status:**\n"
        f"📊 Status: {session_status}\n"
        f"🔄 Turn Count: {session_info['turn_count']}\n"
        f"✓ Your User ID: {user_id}\n\n"
        "Send me a voice message to get started!"
    )

    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )


async def handle_help(update: Update, context) -> None:
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
`/info` - Show system information
`/compact` - Compress session context
`/workspace` - Show workspace contents

**📚 Session Management:**
`/sessions` - List all your sessions
`/sessioninfo` - Show active session details
`/newsession` - Start a new session
`/cleansessions` - Delete old sessions

**🔧 Git Commands:**
`/gitinit` - Initialize git repository
`/gitstatus` - Show repository status
`/gitdiff` - Show diff of changes
`/commit [message]` - Commit changes
`/gitlog` - Show commit history

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

Last updated: February 6, 2026
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_info(update: Update, context) -> None:
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
    workspace_exists = Path('/workspace').exists()
    workspace_writable = os.access('/workspace', os.W_OK) if workspace_exists else False

    # Check disk space
    try:
        disk_usage = subprocess.run(
            ['df', '-h', '/workspace'],
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
    uptime_str = "Unknown"
    if 'start_time' in context.bot_data:
        uptime = datetime.now() - context.bot_data['start_time']
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

    info_text = f"""ℹ️ **System Information**

**Bot Configuration:**
└─ Python: {python_version}
└─ Uptime: {uptime_str}
└─ Mode: {config.BOT_MODE}

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
└─ Anthropic: {'✅ Configured' if config.ANTHROPIC_API_KEY else '❌ Missing'}
└─ Deepgram: {'✅ Configured' if config.DEEPGRAM_API_KEY else '❌ Missing'}
└─ Telegram: {'✅ Configured' if config.TELEGRAM_TOKEN else '❌ Missing'}

**Session Storage:**
└─ Path: `{config.SESSIONS_DIR}`
└─ Backend: PicklePersistence

**Allowed Users:**
└─ Count: {len(config.ALLOWED_USER_IDS) if config.ALLOWED_USER_IDS else 'Unlimited'}
└─ You: {'✅ Authorized' if check_authorization(user_id) else '❌ Not authorized'}

Use /status for session details
Use /help for available commands
"""

    await update.message.reply_text(info_text, parse_mode='Markdown')


async def handle_status(update: Update, context) -> None:
    """Handle /status command - show comprehensive session status."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Get session info
    session_id = context.user_data.get('claude_session_id', 'None')
    turn_count = context.user_data.get('turn_count', 0)
    pending_change = context.user_data.get('pending_change')
    approval_history = context.user_data.get('approval_history', [])

    # Git repository status
    git_branch = 'Not initialized'
    git_commit = 'None'
    if git_ops.is_git_repo():
        try:
            status = git_ops.get_status()
            if status:
                git_branch = status.branch
                # Get latest commit hash
                import subprocess
                commit_result = subprocess.run(
                    ['git', '-C', '/workspace', 'rev-parse', '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                git_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else 'None'
        except Exception as e:
            logger.error(f"Git status check failed: {e}")

    # Workspace files count
    file_count = 'Unknown'
    try:
        import subprocess
        file_count_result = subprocess.run(
            ['find', '/workspace', '-type', 'f', '!', '-path', '*/.git/*'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if file_count_result.returncode == 0 and file_count_result.stdout:
            files = [f for f in file_count_result.stdout.strip().split('\n') if f]
            file_count = len(files)
    except Exception:
        pass

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
                time_str = timestamp[:8]
        else:
            time_str = 'unknown'
        pending_status = f"{state.title()} (created at {time_str})"

    # Recent approvals
    recent_approvals = len([h for h in approval_history if h.get('state') == CHANGE_STATE_APPROVED])
    recent_rejections = len([h for h in approval_history if h.get('state') == CHANGE_STATE_REJECTED])

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


async def handle_clear(update: Update, context) -> None:
    """Handle /clear command - reset session with confirmation."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Store old session info for reference
    old_session_id = context.user_data.get('claude_session_id', 'None')
    old_turn_count = context.user_data.get('turn_count', 0)
    pending_change = context.user_data.get('pending_change')

    # Warn if there are pending changes
    if pending_change and pending_change.get('state') == CHANGE_STATE_PENDING:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, clear everything", callback_data='clear:confirm'),
                InlineKeyboardButton("❌ Cancel", callback_data='clear:cancel')
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


async def handle_compact(update: Update, context) -> None:
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

    # Reset turn count (session compacting will be implemented later)
    context.user_data['turn_count'] = 0

    await update.message.reply_text("✅ Session compacted! Turn count reset.")


async def handle_workspace(update: Update, context) -> None:
    """Handle /workspace command - show workspace contents."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    try:
        # Get directory tree (max 3 levels deep)
        tree_result = subprocess.run(
            ['find', '/workspace', '-maxdepth', '3', '-type', 'f', '!', '-path', '*/.git/*'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if tree_result.returncode != 0:
            await update.message.reply_text("❌ Failed to read workspace")
            return

        files = [f.replace('/workspace/', '') for f in tree_result.stdout.strip().split('\n') if f]
        files = [f for f in files if f]  # Remove empty strings

        if not files:
            await update.message.reply_text(
                "📁 **Workspace Contents**\n\n"
                "The workspace is empty.\n"
                "Send a command to create files!",
                parse_mode='Markdown'
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

        output += "\nUse /gitstatus or /gitdiff to explore changes"

        await update.message.reply_text(output, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Workspace command error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error reading workspace: {str(e)}")


async def handle_sessions(update: Update, context) -> None:
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
            "📭 **No sessions found**\n\n"
            "Send a message to start a new session!",
            parse_mode='Markdown'
        )
        return

    # Format session list
    current_session_id = context.user_data.get('claude_session_id')

    message_parts = ["📚 **Your Claude Sessions**\n" + "=" * 30 + "\n\n"]

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
        session_short = session_id[:30] + "..." if len(session_id) > 30 else session_id
        message_parts.append(
            f"{prefix}`{session_short}`\n"
            f"   📅 {modified_str} | 💾 {size_str} | 📁 {session['file_count']} files\n\n"
        )

    if len(sessions) > 10:
        message_parts.append(f"_...and {len(sessions) - 10} more sessions_\n\n")

    message_parts.append(
        f"💡 Use /newsession to start fresh\n"
        f"💡 Use /cleansessions to delete old sessions"
    )

    await update.message.reply_text(''.join(message_parts), parse_mode='Markdown')


async def handle_newsession(update: Update, context) -> None:
    """Handle /newsession command - start a new session."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    old_session = context.user_data.get('claude_session_id', 'None')

    # Clear current session
    reset_session(context)

    await update.message.reply_text(
        f"🆕 **New session started!**\n\n"
        f"Previous session: `{old_session}`\n\n"
        f"Send a message to begin.",
        parse_mode='Markdown'
    )


async def handle_cleansessions(update: Update, context) -> None:
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
            f"🗑️ **Cleaned up {deleted_count} old session(s)**\n"
            f"(older than 30 days)",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "✨ **No old sessions to clean up!**\n"
            "All your sessions are recent.",
            parse_mode='Markdown'
        )


async def handle_sessioninfo(update: Update, context) -> None:
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
        f"📊 **Session Information**\n"
        f"{'=' * 30}\n\n"
        f"🆔 **ID:** `{info['session_id']}`\n\n"
        f"📅 **Created:** {created_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📅 **Modified:** {modified_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"💾 **Size:** {info['size_bytes'] / 1024:.2f} KB\n"
        f"📁 **Files:** {info['file_count']}\n"
        f"🔄 **Turns:** {context.user_data.get('turn_count', 0)}\n\n"
        f"📂 **Location:** `~/.claude/projects/{info['session_id']}/`"
    )

    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_text(update: Update, context) -> None:
    """Handle text messages and execute via Claude Code."""
    user_id = update.effective_user.id
    user_logger = ContextLogger(__name__, user_id=user_id, handler='text')

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    text = update.message.text
    log_access(user_id, 'text_message', f"length={len(text)}")
    user_logger.info(f"Text message: {text[:100]}")

    # Store for retry functionality
    context.user_data['last_prompt'] = text

    # Get or create session ID
    session_id = get_or_create_session_id(context, user_id)
    turn_count = increment_turn_count(context)

    # Send processing message
    status_msg = await update.message.reply_text(
        "⏳ **Processing with Claude Code...**",
        parse_mode='Markdown'
    )

    try:
        # Progress callback - updates status message with live tool activity
        last_edit_time = [0.0]
        progress_lines = []

        async def on_progress(line: str):
            progress_lines.append(line)
            # Throttle edits to avoid Telegram rate limits (max once per 2s)
            import time
            now = time.time()
            if now - last_edit_time[0] >= 2.0:
                last_edit_time[0] = now
                recent = progress_lines[-5:]  # Show last 5 steps
                body = '\n'.join(recent)
                try:
                    await status_msg.edit_text(
                        f"⏳ **Processing with Claude Code...**\n\n{body}",
                        parse_mode='Markdown'
                    )
                except Exception:
                    pass  # Ignore edit errors (message unchanged, flood limits)

        # Inject repo context into prompt if a repo is linked
        prompt = text
        github_repo = context.user_data.get('github_repo')
        repo_path = context.user_data.get('repo_path')
        if github_repo and repo_path:
            prompt = (
                f"[Context: Working on GitHub repo `{github_repo}` at `{repo_path}`. "
                f"Use this as the working directory for all file operations, git commands, etc.]\n\n"
                f"{text}"
            )

        # Execute with Claude (streaming)
        logger.info(f"Executing Claude for user {user_id}, session {session_id}, turn {turn_count}")
        claude_response: ClaudeResponse = await claude_executor.execute_streaming(prompt, session_id, on_progress)

        # Store new session ID if created
        if claude_response.session_id:
            context.user_data['claude_session_id'] = claude_response.session_id

        if claude_response.success:
            # Store pending changes state for approval workflow
            change_id = f"change_{user_id}_{int(datetime.now().timestamp())}"
            context.user_data['pending_change'] = {
                'id': change_id,
                'state': CHANGE_STATE_PENDING,
                'prompt': text,
                'timestamp': datetime.now().isoformat(),
                'output': claude_response.output,
                'session_id': context.user_data.get('claude_session_id'),
                'tools_used': claude_response.tools_used
            }

            # Format the main response
            formatted_messages = formatter.format_response(claude_response.output)

            # Build details section
            details = (
                f"\n\n**Details:**\n"
                f"• Model: {claude_response.model or 'N/A'}\n"
                f"• Tokens: {claude_response.input_tokens} in / {claude_response.output_tokens} out\n"
                f"• Cost: ${claude_response.cost_usd:.4f}\n"
                f"• Duration: {claude_response.duration_ms}ms\n"
                f"• Turn: {turn_count}"
            )

            if claude_response.tools_used:
                details += "\n" + formatter.format_tool_list(claude_response.tools_used)

            # Create keyboard based on response
            has_changes = 'Write' in claude_response.tools_used or 'Edit' in claude_response.tools_used
            session_active = bool(claude_response.session_id)
            reply_markup = keyboards.main_actions(
                has_changes=has_changes,
                session_active=session_active
            )

            # Send first message (edit status message)
            first_msg = formatted_messages[0].text + (details if len(formatted_messages) == 1 else "")
            await status_msg.edit_text(
                first_msg,
                parse_mode='Markdown',
                reply_markup=reply_markup if len(formatted_messages) == 1 else None
            )

            # Send additional messages if response was split
            for i, msg in enumerate(formatted_messages[1:]):
                # Add keyboard to last message only
                is_last = (i == len(formatted_messages) - 2)
                await update.message.reply_text(
                    msg.text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup if is_last and len(formatted_messages) > 1 else None
                )

            # Send details as separate message if response was split
            if len(formatted_messages) > 1:
                await update.message.reply_text(
                    details,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

            logger.info(f"Claude execution successful for user {user_id}")

        else:
            # Error occurred
            error_text = (
                "❌ **Claude execution failed**\n\n"
                f"Error: {claude_response.error}\n\n"
                "Please try again or rephrase your request."
            )
            await status_msg.edit_text(error_text, parse_mode='Markdown')
            logger.error(f"Claude execution failed for user {user_id}: {claude_response.error}")

    except Exception as e:
        user_logger.error(f"Error during Claude execution: {e}", exc_info=True)
        error_msg = handle_error(e, "text_handler", user_id)
        await status_msg.edit_text(
            f"❌ **Execution error**\n\n{error_msg}",
            parse_mode='Markdown'
        )


async def handle_voice(update: Update, context) -> None:
    """
    Handle voice messages from users.

    Downloads voice message from Telegram, converts to WAV format.
    In Step 6, this will add Deepgram transcription.
    """
    user_id = update.effective_user.id
    user_logger = ContextLogger(__name__, user_id=user_id, handler='voice')

    # Check authorization
    if not check_authorization(user_id):
        user_logger.warning("Unauthorized access attempt")
        await update.message.reply_text("⛔ Unauthorized")
        return

    duration = update.message.voice.duration
    log_access(user_id, 'voice_message', f"duration={duration}s")
    user_logger.info(f"Voice message received, duration: {duration}s")

    # Track start time for cost monitoring
    start_time = time.time()

    # Send "processing" message
    status_msg = await update.message.reply_text(
        "🎤 **Voice message received**\n\n"
        "⏳ Downloading...",
        parse_mode='Markdown'
    )

    ogg_path = None
    wav_path = None

    try:
        # Step 1: Download voice file from Telegram
        voice_file_id = update.message.voice.file_id

        user_logger.debug(f"Voice file ID: {voice_file_id}")

        # Create unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ogg_path = f'{config.SESSIONS_DIR}/voice_{user_id}_{timestamp}.ogg'
        wav_path = f'{config.SESSIONS_DIR}/voice_{user_id}_{timestamp}.wav'

        # Download file
        voice_file = await context.bot.get_file(voice_file_id)
        await voice_file.download_to_drive(ogg_path)

        file_size = os.path.getsize(ogg_path)
        user_logger.debug(f"Downloaded voice file: {ogg_path} ({file_size} bytes)")

        # Update status
        await status_msg.edit_text(
            "🎤 **Voice message received**\n\n"
            f"✓ Downloaded ({duration}s)\n"
            "⏳ Converting format...",
            parse_mode='Markdown'
        )

        # Step 2: Convert OGG to WAV using ffmpeg
        conversion_result = subprocess.run(
            [
                'ffmpeg',
                '-y',                    # Overwrite output file if exists
                '-i', ogg_path,         # Input file
                '-ar', '16000',         # Sample rate: 16kHz (optimal for speech)
                '-ac', '1',             # Audio channels: 1 (mono)
                '-acodec', 'pcm_s16le', # Codec: 16-bit PCM
                wav_path                # Output file
            ],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        if conversion_result.returncode != 0:
            user_logger.error(f"ffmpeg conversion failed: {conversion_result.stderr}")
            await status_msg.edit_text(
                "❌ **Conversion failed**\n\n"
                "Failed to convert audio format.\n"
                "Please try recording again.",
                parse_mode='Markdown'
            )
            return

        wav_size = os.path.getsize(wav_path)
        user_logger.debug(f"Converted to WAV: {wav_path} ({wav_size} bytes)")

        # Update status
        await status_msg.edit_text(
            "🎤 **Voice message received**\n\n"
            f"✓ Downloaded ({duration}s)\n"
            f"✓ Converted to WAV\n"
            "⏳ Transcribing...",
            parse_mode='Markdown'
        )

        # Step 3: Transcribe with Deepgram API
        user_logger.info(f"Starting Deepgram transcription")

        with open(wav_path, 'rb') as audio:
            # Prepare audio source
            source = {'buffer': audio, 'mimetype': 'audio/wav'}

            # Configure Deepgram options
            options = PrerecordedOptions(
                model='nova-3',  # Nova-3 multilingual model for best accuracy
                smart_format=True,  # Enable smart formatting
                language='multi'  # Multilingual auto-detection
            )

            # Call Deepgram API
            response = deepgram.listen.prerecorded.v('1').transcribe_file(source, options)

        # Extract transcribed text
        transcribed_text = response.results.channels[0].alternatives[0].transcript

        user_logger.info(f"Transcription complete: {len(transcribed_text)} characters")
        user_logger.debug(f"Transcribed text: {transcribed_text}")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Estimate cost (Deepgram API: $0.0043/minute)
        duration_minutes = duration / 60
        estimated_cost = duration_minutes * 0.0043

        user_logger.info(f"Processing took {processing_time:.2f}s, estimated cost: ${estimated_cost:.4f}")

        # Store transcription in context
        context.user_data['last_transcription'] = transcribed_text

        # Step 4: Execute with Claude Code
        if not transcribed_text or len(transcribed_text.strip()) == 0:
            await status_msg.edit_text(
                "❌ **Empty transcription**\n\n"
                "Could not transcribe any text from your voice message.\n"
                "Please try again and speak more clearly.",
                parse_mode='Markdown'
            )
            return

        # Get or create session ID
        session_id = get_or_create_session_id(context, user_id)
        turn_count = increment_turn_count(context)

        # Update status
        await status_msg.edit_text(
            "🎤 **Voice transcribed successfully**\n\n"
            f"**Transcription:**\n{transcribed_text}\n\n"
            "⏳ **Executing with Claude Code...**",
            parse_mode='Markdown'
        )

        try:
            # Progress callback for voice handler
            voice_last_edit_time = [0.0]
            voice_progress_lines = []
            voice_transcription_header = (
                f"🎤 **Voice transcribed:**\n_{transcribed_text}_\n\n"
            )

            async def on_voice_progress(line: str):
                voice_progress_lines.append(line)
                import time as _time
                now = _time.time()
                if now - voice_last_edit_time[0] >= 2.0:
                    voice_last_edit_time[0] = now
                    recent = voice_progress_lines[-5:]
                    body = '\n'.join(recent)
                    try:
                        await status_msg.edit_text(
                            voice_transcription_header + f"⏳ **Executing with Claude Code...**\n\n{body}",
                            parse_mode='Markdown'
                        )
                    except Exception:
                        pass

            # Inject repo context into prompt if a repo is linked
            voice_prompt = transcribed_text
            github_repo = context.user_data.get('github_repo')
            repo_path = context.user_data.get('repo_path')
            if github_repo and repo_path:
                voice_prompt = (
                    f"[Context: Working on GitHub repo `{github_repo}` at `{repo_path}`. "
                    f"Use this as the working directory for all file operations, git commands, etc.]\n\n"
                    f"{transcribed_text}"
                )

            # Execute with Claude (streaming)
            user_logger.info(f"Executing Claude, session {session_id}, turn {turn_count}")
            claude_response: ClaudeResponse = await claude_executor.execute_streaming(voice_prompt, session_id, on_voice_progress)

            # Store new session ID if created
            if claude_response.session_id:
                context.user_data['claude_session_id'] = claude_response.session_id

            # Calculate total processing time
            total_time = time.time() - start_time
            total_cost = estimated_cost + claude_response.cost_usd

            if claude_response.success:
                # Store pending changes state for approval workflow
                change_id = f"change_{user_id}_{int(datetime.now().timestamp())}"
                context.user_data['pending_change'] = {
                    'id': change_id,
                    'state': CHANGE_STATE_PENDING,
                    'prompt': transcribed_text,
                    'timestamp': datetime.now().isoformat(),
                    'output': claude_response.output,
                    'session_id': context.user_data.get('claude_session_id'),
                    'tools_used': claude_response.tools_used
                }

                # Format Claude's response
                formatted_messages = formatter.format_response(claude_response.output)

                # Build details section
                details = (
                    f"\n\n**Details:**\n"
                    f"• Model: {claude_response.model or 'N/A'}\n"
                    f"• Tokens: {claude_response.input_tokens} in / {claude_response.output_tokens} out\n"
                    f"• Total cost: ${total_cost:.4f} (Deepgram: ${estimated_cost:.4f}, Claude: ${claude_response.cost_usd:.4f})\n"
                    f"• Duration: {total_time:.1f}s (Transcription: {processing_time:.1f}s, Claude: {claude_response.duration_ms/1000:.1f}s)\n"
                    f"• Turn: {turn_count}"
                )

                if claude_response.tools_used:
                    details += "\n" + formatter.format_tool_list(claude_response.tools_used)

                # Create keyboard based on response
                has_changes = 'Write' in claude_response.tools_used or 'Edit' in claude_response.tools_used
                session_active = bool(claude_response.session_id)
                reply_markup = keyboards.main_actions(
                    has_changes=has_changes,
                    session_active=session_active
                )

                # Build first message with transcription
                first_msg = f"🎤 **Transcription:**\n{transcribed_text}\n\n" + formatted_messages[0].text
                if len(formatted_messages) == 1:
                    first_msg += details

                await status_msg.edit_text(
                    first_msg,
                    parse_mode='Markdown',
                    reply_markup=reply_markup if len(formatted_messages) == 1 else None
                )

                # Send additional messages if response was split
                for i, msg in enumerate(formatted_messages[1:]):
                    # Add keyboard to last message only
                    is_last = (i == len(formatted_messages) - 2)
                    await update.message.reply_text(
                        msg.text,
                        parse_mode='Markdown',
                        reply_markup=reply_markup if is_last and len(formatted_messages) > 1 else None
                    )

                # Send details as separate message if response was split
                if len(formatted_messages) > 1:
                    await update.message.reply_text(
                        details,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )

                user_logger.info(f"Voice + Claude execution successful")

            else:
                # Claude execution failed
                error_text = (
                    f"🎤 **Transcription:**\n{transcribed_text}\n\n"
                    f"❌ **Claude execution failed**\n\n"
                    f"Error: {claude_response.error}\n\n"
                    "Please try again or rephrase your request."
                )
                await status_msg.edit_text(error_text, parse_mode='Markdown')
                user_logger.error(f"Claude execution failed: {claude_response.error}")

        except Exception as claude_error:
            user_logger.error(f"Error during Claude execution: {claude_error}", exc_info=True)
            error_msg = handle_error(claude_error, "voice_claude_execution", user_id)
            await status_msg.edit_text(
                f"🎤 **Transcription:**\n{transcribed_text}\n\n"
                f"❌ **Claude execution error**\n\n{error_msg}",
                parse_mode='Markdown'
            )

        # Step 5: Cleanup audio files to save space
        try:
            os.remove(ogg_path)
            os.remove(wav_path)
            user_logger.debug(f"Cleaned up audio files")
        except Exception as cleanup_error:
            user_logger.warning(f"Cleanup failed: {cleanup_error}")

        user_logger.info(f"Voice processing complete")

    except subprocess.TimeoutExpired as timeout_error:
        user_logger.error("ffmpeg conversion timeout")
        error_msg = handle_error(timeout_error, "voice_conversion", user_id)
        await status_msg.edit_text(
            f"❌ **Conversion timeout**\n\n{error_msg}",
            parse_mode='Markdown'
        )
        # Cleanup
        if ogg_path and os.path.exists(ogg_path):
            os.remove(ogg_path)

    except Exception as e:
        user_logger.error(f"Voice processing error: {e}", exc_info=True)
        error_msg = handle_error(e, "voice_handler", user_id)
        await status_msg.edit_text(
            f"❌ **Processing failed**\n\n{error_msg}",
            parse_mode='Markdown'
        )
        # Cleanup
        if ogg_path and os.path.exists(ogg_path):
            os.remove(ogg_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


async def handle_repo(update: Update, context) -> None:
    """
    Link a GitHub repository to the current session.
    Usage:
      /repo owner/repo       - clone/pull repo and link to session
      /repo                  - show current linked repo
      /repo clear            - unlink repo from session
    """
    user_id = update.effective_user.id
    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    initialize_user_data(context)
    args = context.args

    # Show current repo
    if not args:
        repo = context.user_data.get('github_repo')
        repo_path = context.user_data.get('repo_path')
        if repo:
            await update.message.reply_text(
                f"📁 **Linked repository:** `{repo}`\n"
                f"📂 **Local path:** `{repo_path}`\n\n"
                f"Use `/repo owner/repo` to switch or `/repo clear` to unlink.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "No repository linked.\n\n"
                "Usage: `/repo owner/repo`\nExample: `/repo torvalds/linux`",
                parse_mode='Markdown'
            )
        return

    # Clear repo
    if args[0].lower() == 'clear':
        old = context.user_data.get('github_repo', 'none')
        context.user_data['github_repo'] = None
        context.user_data['repo_path'] = None
        context.user_data['claude_session_id'] = None  # new session for new context
        await update.message.reply_text(
            f"✅ Unlinked repository `{old}`.\nSession reset.",
            parse_mode='Markdown'
        )
        return

    # Link repo: clone or pull
    repo_slug = args[0].strip('/')
    if '/' not in repo_slug:
        await update.message.reply_text(
            "❌ Invalid format. Use `owner/repo`\nExample: `/repo torvalds/linux`",
            parse_mode='Markdown'
        )
        return

    repo_name = repo_slug.split('/')[-1]
    repo_path = WORKSPACE_BASE / repo_name
    github_token = os.environ.get('GITHUB_TOKEN', '')

    if github_token:
        clone_url = f"https://{github_token}@github.com/{repo_slug}.git"
    else:
        clone_url = f"https://github.com/{repo_slug}.git"

    status_msg = await update.message.reply_text(
        f"⏳ Setting up repository `{repo_slug}`...",
        parse_mode='Markdown'
    )

    try:
        if repo_path.exists():
            # Pull latest
            result = subprocess.run(
                ['git', 'pull'],
                cwd=str(repo_path),
                capture_output=True, text=True, timeout=60
            )
            action = "updated"
            detail = result.stdout.strip() or result.stderr.strip()
        else:
            # Clone
            result = subprocess.run(
                ['git', 'clone', clone_url, str(repo_path)],
                capture_output=True, text=True, timeout=120
            )
            action = "cloned"
            detail = result.stdout.strip() or result.stderr.strip()

        if result.returncode != 0:
            await status_msg.edit_text(
                f"❌ Failed to {action.replace('d','')}: `{repo_slug}`\n\n```\n{detail[:500]}\n```",
                parse_mode='Markdown'
            )
            return

        # Link repo to session and reset session for fresh context
        context.user_data['github_repo'] = repo_slug
        context.user_data['repo_path'] = str(repo_path)
        context.user_data['claude_session_id'] = None  # fresh session with repo context

        # Get branch info
        branch_result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=str(repo_path), capture_output=True, text=True
        )
        branch = branch_result.stdout.strip() or 'unknown'

        await status_msg.edit_text(
            f"✅ Repository `{repo_slug}` {action}!\n\n"
            f"📂 **Path:** `{repo_path}`\n"
            f"🌿 **Branch:** `{branch}`\n\n"
            f"Session reset. Claude will now work in this repository.\n"
            f"You can ask me to: create branches, make changes, push, create PRs, etc.",
            parse_mode='Markdown'
        )
        logger.info(f"User {user_id} linked repo {repo_slug} at {repo_path}")

    except subprocess.TimeoutExpired:
        await status_msg.edit_text(f"❌ Timeout cloning `{repo_slug}`. Repository may be too large.")
    except Exception as e:
        logger.error(f"Repo setup failed: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Error: {str(e)}")


async def handle_gitinit(update: Update, context) -> None:
    """Handle /gitinit command - initialize git repository."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    log_access(user_id, 'command', '/gitinit')

    success, message = git_ops.init_repo()

    if success:
        await update.message.reply_text(
            f"✅ **{message}**\n\n"
            f"You can now commit changes with /commit",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(f"❌ **{message}**", parse_mode='Markdown')


async def handle_gitstatus(update: Update, context) -> None:
    """Handle /gitstatus command - show repository status."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    log_access(user_id, 'command', '/gitstatus')

    status = git_ops.get_status()

    if not status:
        await update.message.reply_text(
            "❌ **Not a git repository**\n\n"
            "Initialize one with: /gitinit",
            parse_mode='Markdown'
        )
        return

    # Format status message
    status_emoji = "✅" if status.is_clean else "📝"

    message = f"{status_emoji} **Git Status**\n\n"
    message += f"**Branch:** `{status.branch}`\n"

    if status.ahead > 0:
        message += f"**Ahead:** {status.ahead} commit(s)\n"
    if status.behind > 0:
        message += f"**Behind:** {status.behind} commit(s)\n"

    if status.is_clean:
        message += "\n✨ Working directory clean"
    else:
        if status.staged:
            message += f"\n📦 **Staged** ({len(status.staged)}):\n"
            for file in status.staged[:10]:
                message += f"  • `{file}`\n"
            if len(status.staged) > 10:
                message += f"  • ...and {len(status.staged) - 10} more\n"

        if status.modified:
            message += f"\n📝 **Modified** ({len(status.modified)}):\n"
            for file in status.modified[:10]:
                message += f"  • `{file}`\n"
            if len(status.modified) > 10:
                message += f"  • ...and {len(status.modified) - 10} more\n"

        if status.untracked:
            message += f"\n❓ **Untracked** ({len(status.untracked)}):\n"
            for file in status.untracked[:10]:
                message += f"  • `{file}`\n"
            if len(status.untracked) > 10:
                message += f"  • ...and {len(status.untracked) - 10} more\n"

    # Add keyboard for actions
    keyboard = keyboards.git_actions()

    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def handle_gitdiff(update: Update, context) -> None:
    """Handle /gitdiff command - show diff of changes."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    log_access(user_id, 'command', '/gitdiff')

    diff = git_ops.get_diff()

    if not diff:
        await update.message.reply_text(
            "❌ **Not a git repository**",
            parse_mode='Markdown'
        )
        return

    if not diff.has_changes:
        await update.message.reply_text(
            "✅ **No changes in working directory**",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )
        return

    # Format diff
    diff_text = diff.diff_output

    # Truncate if too long
    if len(diff_text) > 3500:
        diff_text = diff_text[:3500] + "\n\n...(truncated)"

    summary = (
        f"📝 **Git Diff**\n\n"
        f"**Files changed:** {len(diff.files_changed)}\n"
        f"**Insertions:** +{diff.insertions}\n"
        f"**Deletions:** -{diff.deletions}\n\n"
    )

    formatted = formatter.format_code_block(diff_text, 'diff', max_lines=100)

    await update.message.reply_text(
        summary + formatted,
        parse_mode='Markdown',
        reply_markup=keyboards.close_button()
    )


async def handle_commit(update: Update, context) -> None:
    """Handle /commit command - create a commit."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    log_access(user_id, 'command', '/commit')

    # Parse commit message from command
    message_parts = update.message.text.split(' ', 1)
    commit_message = message_parts[1] if len(message_parts) > 1 else None

    # Check if git repo exists
    if not git_ops.is_git_repo():
        await update.message.reply_text(
            "❌ **No git repository found**\n\n"
            "Initialize one with: /gitinit",
            parse_mode='Markdown'
        )
        return

    # Stage all changes
    success, msg = git_ops.add_files()
    if not success:
        await update.message.reply_text(
            f"❌ **Failed to stage files:** {msg}",
            parse_mode='Markdown'
        )
        return

    # Generate message if not provided
    if not commit_message:
        commit_message = git_ops.generate_commit_message()
        status_msg = await update.message.reply_text(
            f"📝 **Auto-generated message:** {commit_message}\n\n"
            f"Committing...",
            parse_mode='Markdown'
        )
    else:
        status_msg = await update.message.reply_text(
            "⏳ **Creating commit...**",
            parse_mode='Markdown'
        )

    # Create commit
    success, result = git_ops.commit(commit_message)

    if success:
        await status_msg.edit_text(
            f"✅ **Committed successfully!**\n\n"
            f"**Commit hash:** `{result}`\n"
            f"**Message:** {commit_message}",
            parse_mode='Markdown'
        )
    else:
        await status_msg.edit_text(
            f"❌ **Commit failed:** {result}",
            parse_mode='Markdown'
        )


async def handle_gitlog(update: Update, context) -> None:
    """Handle /gitlog command - show commit history."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    log_access(user_id, 'command', '/gitlog')

    commits = git_ops.get_log(count=10)

    if not commits:
        await update.message.reply_text(
            "📜 **No commits yet**\n\n"
            "Create your first commit with /commit",
            parse_mode='Markdown'
        )
        return

    message = "📜 **Recent Commits**\n\n"

    for commit in commits:
        message += (
            f"`{commit['hash']}` - {commit['message']}\n"
            f"  _by {commit['author']}, {commit['date']}_\n\n"
        )

    await update.message.reply_text(
        message,
        parse_mode='Markdown',
        reply_markup=keyboards.close_button()
    )


async def error_handler(update: Update, context) -> None:
    """
    Global error handler for unhandled exceptions.

    Logs errors and sends user-friendly message.
    """
    logger.error(f"Unhandled exception: {context.error}", exc_info=context.error)

    # Get user ID if available
    user_id = update.effective_user.id if update and update.effective_user else None

    # Get user-friendly error message
    error_msg = handle_error(context.error, "global_handler", user_id)

    # Try to notify user
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"❌ **An error occurred**\n\n{error_msg}"
            )
        except Exception:
            pass  # Can't send message to user


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

    # Store bot start time
    app.bot_data['start_time'] = datetime.now()

    # Register command handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("info", handle_info))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("sessions", handle_sessions))
    app.add_handler(CommandHandler("sessioninfo", handle_sessioninfo))
    app.add_handler(CommandHandler("newsession", handle_newsession))
    app.add_handler(CommandHandler("cleansessions", handle_cleansessions))
    app.add_handler(CommandHandler("clear", handle_clear))
    app.add_handler(CommandHandler("compact", handle_compact))
    app.add_handler(CommandHandler("workspace", handle_workspace))

    # Register repo command handler
    app.add_handler(CommandHandler("repo", handle_repo))

    # Register git command handlers
    app.add_handler(CommandHandler("gitinit", handle_gitinit))
    app.add_handler(CommandHandler("gitstatus", handle_gitstatus))
    app.add_handler(CommandHandler("gitdiff", handle_gitdiff))
    app.add_handler(CommandHandler("commit", handle_commit))
    app.add_handler(CommandHandler("gitlog", handle_gitlog))

    # Register callback query handler
    app.add_handler(CallbackQueryHandler(handle_callback_query))

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
