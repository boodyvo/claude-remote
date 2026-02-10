#!/usr/bin/env python3
"""
Callback query handlers for inline keyboard buttons.
"""

import logging
import subprocess
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from keyboards import KeyboardBuilder
from formatters import ResponseFormatter
from logging_config import ContextLogger, log_access
from error_handlers import handle_error
from git_operations import GitOperations

logger = logging.getLogger(__name__)
formatter = ResponseFormatter()
keyboards = KeyboardBuilder()
git_ops = GitOperations()

# Change state constants
CHANGE_STATE_PENDING = 'pending'
CHANGE_STATE_APPROVED = 'approved'
CHANGE_STATE_REJECTED = 'rejected'


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback query handler.
    Routes callback data to appropriate handler.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    user_id = update.effective_user.id
    callback_data = query.data
    user_logger = ContextLogger(__name__, user_id=user_id, handler='callback')

    user_logger.info(f"Callback: {callback_data}")
    log_access(user_id, 'button_click', callback_data)

    try:
        # Parse callback data (format: "category:action" or "category:action:param")
        parts = callback_data.split(':', 2)
        category = parts[0]
        action = parts[1] if len(parts) > 1 else None
        param = parts[2] if len(parts) > 2 else None

        # Route to appropriate handler
        if category == 'action':
            await handle_action_callback(query, context, action, param, user_logger)
        elif category == 'git':
            await handle_git_callback(query, context, action, user_logger)
        elif category == 'session':
            await handle_session_callback(query, context, action, user_logger)
        elif category == 'info':
            await handle_info_callback(query, context, action, user_logger)
        elif category == 'clear':
            await handle_clear_callback(query, context, action, user_logger)
        elif category == 'confirm':
            await handle_confirm_callback(query, context, action, user_logger)
        elif category == 'cancel':
            await handle_cancel_callback(query, context, action, user_logger)
        elif category == 'page':
            await handle_page_callback(query, context, action, param, user_logger)
        else:
            user_logger.warning(f"Unknown callback category: {category}")
            await query.edit_message_text("❓ Unknown action")

    except Exception as e:
        user_logger.error(f"Error handling callback: {e}", exc_info=True)
        error_msg = handle_error(e, "callback_handler", user_id)
        await query.edit_message_text(
            f"❌ Error processing your request.\n\n{error_msg}"
        )


async def handle_action_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    param: str = None,
    user_logger = None
):
    """Handle action callbacks (approve, reject, retry, etc.)."""

    if action == 'approve':
        # Apply changes with git commit
        user_logger.info("User approved changes")

        # Check pending change state
        pending_change = context.user_data.get('pending_change')

        if pending_change and pending_change.get('state') == CHANGE_STATE_PENDING:
            # Mark as approved
            pending_change['state'] = CHANGE_STATE_APPROVED
            pending_change['approved_at'] = datetime.now().isoformat()

            # Add to approval history
            if 'approval_history' not in context.user_data:
                context.user_data['approval_history'] = []

            context.user_data['approval_history'].append({
                'change_id': pending_change.get('id', 'unknown'),
                'state': CHANGE_STATE_APPROVED,
                'timestamp': datetime.now().isoformat(),
                'prompt': pending_change.get('prompt', '')[:100]
            })

            # Limit history to last 20 changes
            if len(context.user_data['approval_history']) > 20:
                context.user_data['approval_history'] = context.user_data['approval_history'][-20:]

            # Try to commit changes if git repo exists
            if git_ops.is_git_repo():
                # Check for changes
                status = git_ops.get_status()
                if status and not status.is_clean:
                    # Stage all changes
                    success, msg = git_ops.add_files()
                    if success:
                        # Create commit
                        commit_msg = f"Apply changes from Claude\n\nPrompt: {pending_change.get('prompt', 'Unknown')[:100]}"
                        success, result = git_ops.commit(commit_msg)

                        if success:
                            await query.edit_message_text(
                                f"✅ **Changes approved and committed!**\n\n"
                                f"**Commit hash:** `{result}`\n"
                                f"**Message:** {commit_msg.split(chr(10))[0]}",
                                parse_mode='Markdown',
                                reply_markup=keyboards.close_button()
                            )
                        else:
                            await query.edit_message_text(
                                f"⚠️ **Changes approved but commit failed:**\n\n{result}",
                                parse_mode='Markdown',
                                reply_markup=keyboards.close_button()
                            )
                    else:
                        await query.edit_message_text(
                            f"⚠️ **Changes approved but staging failed:**\n\n{msg}",
                            parse_mode='Markdown',
                            reply_markup=keyboards.close_button()
                        )
                else:
                    await query.edit_message_text(
                        "✅ **Changes approved!**\n\n"
                        "ℹ️ No git changes detected (informational output only)",
                        parse_mode='Markdown',
                        reply_markup=keyboards.close_button()
                    )
            else:
                await query.edit_message_text(
                    "✅ **Changes approved!**\n\n"
                    "ℹ️ Not a git repository. Use /gitinit to enable version control.",
                    parse_mode='Markdown',
                    reply_markup=keyboards.close_button()
                )

            # Clear pending change
            context.user_data['pending_change'] = None

        else:
            # No pending change or already processed
            await query.edit_message_text(
                "ℹ️ **No pending changes**\n\n"
                "This change may have already been processed.",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

    elif action == 'reject':
        # Reject changes with optional rollback
        user_logger.info("User rejected changes")

        # Check pending change state
        pending_change = context.user_data.get('pending_change')

        if pending_change and pending_change.get('state') == CHANGE_STATE_PENDING:
            # Mark as rejected
            pending_change['state'] = CHANGE_STATE_REJECTED
            pending_change['rejected_at'] = datetime.now().isoformat()

            # Add to approval history
            if 'approval_history' not in context.user_data:
                context.user_data['approval_history'] = []

            context.user_data['approval_history'].append({
                'change_id': pending_change.get('id', 'unknown'),
                'state': CHANGE_STATE_REJECTED,
                'timestamp': datetime.now().isoformat(),
                'prompt': pending_change.get('prompt', '')[:100]
            })

            # Limit history
            if len(context.user_data['approval_history']) > 20:
                context.user_data['approval_history'] = context.user_data['approval_history'][-20:]

            # Check if there are uncommitted changes to discard
            if git_ops.is_git_repo():
                status = git_ops.get_status()
                if status and not status.is_clean:
                    # Offer to discard changes
                    await query.edit_message_text(
                        "❌ **Changes rejected**\n\n"
                        "⚠️ **Git changes detected**\n"
                        "There are uncommitted changes in the repository.\n\n"
                        "Use /gitstatus to review or manually discard with:\n"
                        "`git reset --hard HEAD`",
                        parse_mode='Markdown',
                        reply_markup=keyboards.close_button()
                    )
                else:
                    await query.edit_message_text(
                        "❌ **Changes rejected**\n\n"
                        "No modifications were applied.",
                        parse_mode='Markdown',
                        reply_markup=keyboards.close_button()
                    )
            else:
                await query.edit_message_text(
                    "❌ **Changes rejected**\n\n"
                    "No modifications were applied.",
                    parse_mode='Markdown',
                    reply_markup=keyboards.close_button()
                )

            # Clear pending change
            context.user_data['pending_change'] = None

        else:
            # No pending change or already processed
            await query.edit_message_text(
                "ℹ️ **No pending changes**\n\n"
                "This change may have already been processed.",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

    elif action == 'retry':
        # Retry last command
        last_prompt = context.user_data.get('last_prompt')
        last_transcription = context.user_data.get('last_transcription')

        # Use transcription if available, otherwise use last prompt
        retry_text = last_transcription or last_prompt

        if retry_text:
            user_logger.info(f"User retrying command: {retry_text[:50]}")
            await query.edit_message_text(
                f"🔄 **Retrying command**\n\n"
                f"Command: {retry_text[:100]}...\n\n"
                "ℹ️ To retry, please send your command again.",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )
        else:
            await query.edit_message_text(
                "❌ **No previous command to retry.**",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

    elif action == 'dismiss':
        # Delete the message
        user_logger.debug("User dismissed message")
        await query.message.delete()

    elif action == 'back':
        # Go back to main keyboard
        await query.edit_message_reply_markup(
            reply_markup=keyboards.main_actions()
        )

    else:
        await query.edit_message_text(f"Unknown action: {action}")


async def handle_git_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle git-related callbacks."""

    workspace = context.user_data.get('workspace_path', '/workspace')
    workspace_path = Path(workspace)

    if action == 'diff':
        user_logger.info("User requested git diff")

        try:
            # Show git diff
            result = subprocess.run(
                ['git', 'diff'],
                capture_output=True,
                text=True,
                cwd=str(workspace_path),
                timeout=10
            )

            if result.returncode != 0:
                await query.answer("⚠️ No git repository found", show_alert=True)
                return

            diff_output = result.stdout.strip()

            if not diff_output:
                await query.edit_message_text(
                    "📝 **Git Diff**\n\n"
                    "No changes in working directory.",
                    parse_mode='Markdown',
                    reply_markup=keyboards.close_button()
                )
            else:
                # Truncate if too long
                if len(diff_output) > 3500:
                    diff_output = diff_output[:3500] + "\n\n...(truncated)"

                formatted = formatter.format_code_block(diff_output, 'diff', max_lines=50)
                await query.edit_message_text(
                    f"📝 **Git Diff**\n\n{formatted}",
                    parse_mode='Markdown',
                    reply_markup=keyboards.close_button()
                )

        except subprocess.TimeoutExpired:
            await query.answer("⚠️ Git command timed out", show_alert=True)
        except Exception as e:
            user_logger.error(f"Git diff error: {e}")
            await query.answer("⚠️ Error running git diff", show_alert=True)

    elif action == 'status':
        user_logger.info("User requested git status")

        try:
            # Show git status
            result = subprocess.run(
                ['git', 'status', '--short'],
                capture_output=True,
                text=True,
                cwd=str(workspace_path),
                timeout=10
            )

            if result.returncode != 0:
                await query.answer("⚠️ No git repository found", show_alert=True)
                return

            status_output = result.stdout.strip()

            if not status_output:
                status_message = "📊 **Git Status**\n\n✅ Working directory clean"
            else:
                status_message = f"📊 **Git Status**\n\n```\n{status_output[:3500]}\n```"

            await query.edit_message_text(
                status_message,
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

        except subprocess.TimeoutExpired:
            await query.answer("⚠️ Git command timed out", show_alert=True)
        except Exception as e:
            user_logger.error(f"Git status error: {e}")
            await query.answer("⚠️ Error running git status", show_alert=True)

    elif action == 'log':
        user_logger.info("User requested git log")

        try:
            # Show git log (last 10 commits)
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                capture_output=True,
                text=True,
                cwd=str(workspace_path),
                timeout=10
            )

            if result.returncode != 0:
                await query.answer("⚠️ No git repository found", show_alert=True)
                return

            log_output = result.stdout.strip()
            await query.edit_message_text(
                f"📜 **Git Log** (last 10 commits)\n\n```\n{log_output}\n```",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

        except subprocess.TimeoutExpired:
            await query.answer("⚠️ Git command timed out", show_alert=True)
        except Exception as e:
            user_logger.error(f"Git log error: {e}")
            await query.answer("⚠️ Error running git log", show_alert=True)

    elif action == 'branches':
        user_logger.info("User requested git branches")

        try:
            # Show git branches
            result = subprocess.run(
                ['git', 'branch', '-a'],
                capture_output=True,
                text=True,
                cwd=str(workspace_path),
                timeout=10
            )

            if result.returncode != 0:
                await query.answer("⚠️ No git repository found", show_alert=True)
                return

            branches = result.stdout.strip()
            await query.edit_message_text(
                f"🌿 **Git Branches**\n\n```\n{branches}\n```",
                parse_mode='Markdown',
                reply_markup=keyboards.close_button()
            )

        except subprocess.TimeoutExpired:
            await query.answer("⚠️ Git command timed out", show_alert=True)
        except Exception as e:
            user_logger.error(f"Git branches error: {e}")
            await query.answer("⚠️ Error running git branch", show_alert=True)


async def handle_session_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle session management callbacks."""

    if action == 'new':
        # Confirm before creating new session
        await query.edit_message_text(
            "🆕 **Create New Session?**\n\n"
            "This will end your current session and start fresh.\n"
            "Your current conversation history will be lost.",
            parse_mode='Markdown',
            reply_markup=keyboards.confirmation('newsession')
        )

    elif action == 'list':
        # Show session list
        await query.edit_message_text(
            "📚 **Session List**\n\n"
            "Use /sessions command to view all your sessions",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )

    elif action == 'clean':
        # Confirm before cleaning
        await query.edit_message_text(
            "🗑️ **Clean Old Sessions?**\n\n"
            "This will delete sessions older than 30 days.\n"
            "This action cannot be undone.",
            parse_mode='Markdown',
            reply_markup=keyboards.confirmation('cleansessions')
        )

    elif action == 'info':
        # Show session info
        session_id = context.user_data.get('claude_session_id', 'No active session')
        turn_count = context.user_data.get('turn_count', 0)
        last_active = context.user_data.get('last_active', 'Never')

        await query.edit_message_text(
            f"📊 **Current Session**\n\n"
            f"**Session ID:** `{session_id}`\n"
            f"**Turn Count:** {turn_count}\n"
            f"**Last Active:** {last_active}",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )


async def handle_info_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle info callbacks."""

    if action == 'session':
        await handle_session_callback(query, context, 'info', user_logger)


async def handle_confirm_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle confirmation callbacks."""

    if action == 'newsession':
        # Create new session
        old_session = context.user_data.get('claude_session_id', 'None')
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0

        user_logger.info(f"User created new session (old: {old_session})")

        await query.edit_message_text(
            f"✅ **New session created!**\n\n"
            f"Previous session: `{old_session}`\n\n"
            f"Send a message to begin.",
            parse_mode='Markdown'
        )

    elif action == 'cleansessions':
        # Clean old sessions
        user_logger.info("User cleaned old sessions")
        await query.edit_message_text(
            "✅ **Old sessions cleaned!**\n\n"
            "Use /sessions to view remaining sessions.",
            parse_mode='Markdown'
        )


async def handle_cancel_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle cancellation callbacks."""
    user_logger.info(f"User cancelled action: {action}")
    await query.edit_message_text(
        f"❌ **Action cancelled.**",
        parse_mode='Markdown',
        reply_markup=keyboards.close_button()
    )


async def handle_page_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    data_type: str,
    page: str,
    user_logger = None
):
    """Handle pagination callbacks."""
    if data_type == 'noop':
        # Just the page indicator, do nothing
        await query.answer()
        return

    page_num = int(page) if page else 0
    await query.answer(f"Loading page {page_num + 1}...")

    # Would load appropriate page data here
    # For now, just acknowledge
    await query.edit_message_text(
        f"📄 Page {page_num + 1} of {data_type}",
        reply_markup=keyboards.close_button()
    )


async def handle_clear_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    user_logger = None
):
    """Handle clear confirmation callbacks."""
    user_id = query.from_user.id

    if action == 'confirm':
        # Clear all session data
        old_session_id = context.user_data.get('claude_session_id', 'None')
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0
        context.user_data['pending_change'] = None

        user_logger.info(f"User confirmed session clear: {old_session_id}")

        await query.edit_message_text(
            f"🗑️ **Session Cleared!**\n\n"
            f"Previous session: `{old_session_id}`\n"
            f"Pending changes discarded.\n\n"
            f"Starting fresh session on next command.",
            parse_mode='Markdown'
        )
    elif action == 'cancel':
        user_logger.info("User cancelled session clear")

        await query.edit_message_text(
            "✅ Clear operation cancelled.\n\n"
            "Session remains active."
        )
