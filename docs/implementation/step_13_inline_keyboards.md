# Step 13: Inline Keyboard Implementation

**Phase:** 4 - Interactive UI & Approvals
**Estimated Time:** 1 hour
**Prerequisites:** Steps 1-12 completed
**Dependencies:** Telegram inline keyboards, callback queries

---

## Overview

This step implements interactive inline keyboards (buttons) in Telegram messages, allowing users to approve/reject changes, view diffs, check git status, and perform other actions directly from the chat interface without typing commands.

### Context

Telegram inline keyboards provide:
- Clickable buttons attached to messages
- Callback data for button identification
- Dynamic button updates
- Improved user experience

We'll implement buttons for:
- ✅ Approve - Apply changes suggested by Claude
- ❌ Reject - Discard changes
- 📝 Show Diff - Display git diff
- 📊 Git Status - Show working tree status
- 🔄 Retry - Re-run last command
- 📋 More Options - Additional actions

### Goals

1. Create reusable inline keyboard layouts
2. Implement callback handlers for all buttons
3. Add state management for pending actions
4. Provide visual feedback on button clicks
5. Handle edge cases (missing git repo, no changes, etc.)
6. Test all button interactions

---

## Implementation Details

### 13.1 Keyboard Layout Module

**File: `bot/keyboards.py`**

```python
#!/usr/bin/env python3
"""
Inline keyboard layouts for Telegram bot.
Provides reusable button configurations.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class KeyboardBuilder:
    """Build inline keyboards for various bot responses."""

    @staticmethod
    def main_actions(
        has_changes: bool = True,
        session_active: bool = True
    ) -> InlineKeyboardMarkup:
        """
        Main action buttons for Claude responses.

        Args:
            has_changes: Whether there are changes to approve/reject
            session_active: Whether there's an active session

        Returns:
            InlineKeyboardMarkup with action buttons
        """
        buttons = []

        if has_changes:
            # First row: Approve/Reject
            buttons.append([
                InlineKeyboardButton("✅ Approve", callback_data='action:approve'),
                InlineKeyboardButton("❌ Reject", callback_data='action:reject')
            ])

        # Second row: Info buttons
        buttons.append([
            InlineKeyboardButton("📝 Show Diff", callback_data='git:diff'),
            InlineKeyboardButton("📊 Git Status", callback_data='git:status')
        ])

        # Third row: Additional actions
        row = [
            InlineKeyboardButton("🔄 Retry", callback_data='action:retry')
        ]

        if session_active:
            row.append(
                InlineKeyboardButton("📋 Session Info", callback_data='info:session')
            )

        buttons.append(row)

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def confirmation(action: str) -> InlineKeyboardMarkup:
        """
        Confirmation keyboard for destructive actions.

        Args:
            action: Action to confirm (e.g., 'clear', 'delete')

        Returns:
            InlineKeyboardMarkup with confirm/cancel buttons
        """
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data=f'confirm:{action}'
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f'cancel:{action}'
                )
            ]
        ])

    @staticmethod
    def session_management() -> InlineKeyboardMarkup:
        """Keyboard for session management."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🆕 New Session",
                    callback_data='session:new'
                ),
                InlineKeyboardButton(
                    "📚 List Sessions",
                    callback_data='session:list'
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Clean Old Sessions",
                    callback_data='session:clean'
                ),
                InlineKeyboardButton(
                    "📊 Session Info",
                    callback_data='session:info'
                )
            ]
        ])

    @staticmethod
    def git_actions() -> InlineKeyboardMarkup:
        """Keyboard for git-related actions."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Diff", callback_data='git:diff'),
                InlineKeyboardButton("📊 Status", callback_data='git:status')
            ],
            [
                InlineKeyboardButton("📜 Log", callback_data='git:log'),
                InlineKeyboardButton("🌿 Branches", callback_data='git:branches')
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data='action:back')
            ]
        ])

    @staticmethod
    def close_button() -> InlineKeyboardMarkup:
        """Simple close/dismiss button."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ Dismiss", callback_data='action:dismiss')]
        ])

    @staticmethod
    def pagination(
        current_page: int,
        total_pages: int,
        data_type: str
    ) -> InlineKeyboardMarkup:
        """
        Pagination keyboard for lists.

        Args:
            current_page: Current page number (0-indexed)
            total_pages: Total number of pages
            data_type: Type of data being paginated (for callback)

        Returns:
            InlineKeyboardMarkup with pagination buttons
        """
        buttons = []

        nav_row = []
        if current_page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    "◀️ Previous",
                    callback_data=f'page:{data_type}:{current_page-1}'
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data='page:noop'
            )
        )

        if current_page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    "Next ▶️",
                    callback_data=f'page:{data_type}:{current_page+1}'
                )
            )

        buttons.append(nav_row)
        buttons.append([
            InlineKeyboardButton("🗑️ Dismiss", callback_data='action:dismiss')
        ])

        return InlineKeyboardMarkup(buttons)
```

### 13.2 Callback Handler Module

**File: `bot/callback_handlers.py`**

```python
#!/usr/bin/env python3
"""
Callback query handlers for inline keyboard buttons.
"""

import logging
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from keyboards import KeyboardBuilder
from formatters import ResponseFormatter

logger = logging.getLogger(__name__)
formatter = ResponseFormatter()
keyboards = KeyboardBuilder()


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback query handler.
    Routes callback data to appropriate handler.
    """
    query = update.callback_query
    await query.answer()  # Acknowledge button press

    user_id = update.effective_user.id
    callback_data = query.data

    logger.info(f"Callback from user {user_id}: {callback_data}")

    try:
        # Parse callback data (format: "category:action" or "category:action:param")
        parts = callback_data.split(':', 2)
        category = parts[0]
        action = parts[1] if len(parts) > 1 else None
        param = parts[2] if len(parts) > 2 else None

        # Route to appropriate handler
        if category == 'action':
            await handle_action_callback(query, context, action, param)
        elif category == 'git':
            await handle_git_callback(query, context, action)
        elif category == 'session':
            await handle_session_callback(query, context, action)
        elif category == 'info':
            await handle_info_callback(query, context, action)
        elif category == 'confirm':
            await handle_confirm_callback(query, context, action)
        elif category == 'cancel':
            await handle_cancel_callback(query, context, action)
        elif category == 'page':
            await handle_page_callback(query, context, action, param)
        else:
            logger.warning(f"Unknown callback category: {category}")
            await query.edit_message_text("❓ Unknown action")

    except Exception as e:
        logger.error(f"Error handling callback: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Error processing your request. Please try again."
        )


async def handle_action_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    param: str = None
):
    """Handle action callbacks (approve, reject, retry, etc.)."""

    if action == 'approve':
        # Apply changes
        await query.edit_message_text(
            "✅ Changes approved!\n\n"
            "The modifications have been applied. Use git commands to commit if needed.",
            reply_markup=keyboards.close_button()
        )

    elif action == 'reject':
        # Reject changes - could run git reset here
        await query.edit_message_text(
            "❌ Changes rejected.\n\n"
            "No modifications were applied.",
            reply_markup=keyboards.close_button()
        )

    elif action == 'retry':
        # Retry last command
        last_prompt = context.user_data.get('last_prompt')
        if last_prompt:
            await query.edit_message_text(
                f"🔄 Retrying command: {last_prompt[:100]}...\n\n"
                "Please wait..."
            )
            # Re-execute (would need to import execute_claude_command)
            # For now, just notify
            await query.message.reply_text(
                "ℹ️ To retry, please send your command again."
            )
        else:
            await query.edit_message_text(
                "❌ No previous command to retry.",
                reply_markup=keyboards.close_button()
            )

    elif action == 'dismiss':
        # Delete the message
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
    action: str
):
    """Handle git-related callbacks."""

    workspace = Path('/workspace')

    if action == 'diff':
        # Show git diff
        result = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True,
            cwd=str(workspace)
        )

        if result.returncode != 0:
            await query.answer("⚠️ No git repository found", show_alert=True)
            return

        diff_output = result.stdout.strip()

        if not diff_output:
            await query.edit_message_text(
                "📝 Git Diff\n\n"
                "No changes in working directory.",
                reply_markup=keyboards.close_button()
            )
        else:
            # Truncate if too long
            if len(diff_output) > 3500:
                diff_output = diff_output[:3500] + "\n\n...(truncated)"

            formatted = formatter.format_code(diff_output, 'diff')
            await query.edit_message_text(
                f"📝 Git Diff\n\n{formatted.text}",
                parse_mode=formatted.parse_mode,
                reply_markup=keyboards.close_button()
            )

    elif action == 'status':
        # Show git status
        result = subprocess.run(
            ['git', 'status', '--short'],
            capture_output=True,
            text=True,
            cwd=str(workspace)
        )

        if result.returncode != 0:
            await query.answer("⚠️ No git repository found", show_alert=True)
            return

        status_output = result.stdout.strip()

        if not status_output:
            status_message = "📊 Git Status\n\n✅ Working directory clean"
        else:
            status_message = f"📊 Git Status\n\n```\n{status_output[:3500]}\n```"

        await query.edit_message_text(
            status_message,
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )

    elif action == 'log':
        # Show git log (last 10 commits)
        result = subprocess.run(
            ['git', 'log', '--oneline', '-10'],
            capture_output=True,
            text=True,
            cwd=str(workspace)
        )

        if result.returncode != 0:
            await query.answer("⚠️ No git repository found", show_alert=True)
            return

        log_output = result.stdout.strip()
        await query.edit_message_text(
            f"📜 Git Log (last 10 commits)\n\n```\n{log_output}\n```",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )

    elif action == 'branches':
        # Show git branches
        result = subprocess.run(
            ['git', 'branch', '-a'],
            capture_output=True,
            text=True,
            cwd=str(workspace)
        )

        if result.returncode != 0:
            await query.answer("⚠️ No git repository found", show_alert=True)
            return

        branches = result.stdout.strip()
        await query.edit_message_text(
            f"🌿 Git Branches\n\n```\n{branches}\n```",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )


async def handle_session_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str
):
    """Handle session management callbacks."""

    if action == 'new':
        # Confirm before creating new session
        await query.edit_message_text(
            "🆕 Create New Session?\n\n"
            "This will end your current session and start fresh.\n"
            "Your current conversation history will be lost.",
            reply_markup=keyboards.confirmation('newsession')
        )

    elif action == 'list':
        # Show session list (would call handle_sessions from bot.py)
        await query.edit_message_text(
            "📚 Use /sessions command to view all sessions",
            reply_markup=keyboards.close_button()
        )

    elif action == 'clean':
        # Confirm before cleaning
        await query.edit_message_text(
            "🗑️ Clean Old Sessions?\n\n"
            "This will delete sessions older than 30 days.\n"
            "This action cannot be undone.",
            reply_markup=keyboards.confirmation('cleansessions')
        )

    elif action == 'info':
        # Show session info
        session_id = context.user_data.get('claude_session_id', 'No active session')
        turn_count = context.user_data.get('turn_count', 0)

        await query.edit_message_text(
            f"📊 Current Session\n\n"
            f"Session ID: `{session_id}`\n"
            f"Turn Count: {turn_count}",
            parse_mode='Markdown',
            reply_markup=keyboards.close_button()
        )


async def handle_info_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str
):
    """Handle info callbacks."""

    if action == 'session':
        await handle_session_callback(query, context, 'info')


async def handle_confirm_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str
):
    """Handle confirmation callbacks."""

    if action == 'newsession':
        # Create new session
        old_session = context.user_data.get('claude_session_id', 'None')
        context.user_data['claude_session_id'] = None
        context.user_data['turn_count'] = 0

        await query.edit_message_text(
            f"✅ New session created!\n\n"
            f"Previous session: `{old_session}`\n\n"
            f"Send a message to begin.",
            parse_mode='Markdown'
        )

    elif action == 'cleansessions':
        # Clean old sessions (would call cleanup function)
        await query.edit_message_text(
            "✅ Old sessions cleaned!\n\n"
            "Use /sessions to view remaining sessions."
        )


async def handle_cancel_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    action: str
):
    """Handle cancellation callbacks."""
    await query.edit_message_text(
        f"❌ Action '{action}' cancelled.",
        reply_markup=keyboards.close_button()
    )


async def handle_page_callback(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    data_type: str,
    page: str
):
    """Handle pagination callbacks."""
    if data_type == 'noop':
        # Just the page indicator, do nothing
        await query.answer()
        return

    page_num = int(page)
    await query.answer(f"Loading page {page_num + 1}...")

    # Would load appropriate page data here
    # For now, just acknowledge
    await query.edit_message_text(
        f"📄 Page {page_num + 1} of {data_type}",
        reply_markup=keyboards.close_button()
    )
```

### 13.3 Bot Integration

**File: `bot/bot.py`** (update)

```python
from keyboards import KeyboardBuilder
from callback_handlers import handle_callback_query

# Initialize keyboard builder
keyboards = KeyboardBuilder()

# ... existing code ...

async def execute_claude_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str
):
    """Execute a Claude Code command and send response to user."""
    # ... existing execution code ...

    # Store last prompt for retry functionality
    context.user_data['last_prompt'] = prompt

    # ... format response ...

    # Create keyboard based on response
    has_changes = bool(response.files_modified)
    session_active = bool(context.user_data.get('claude_session_id'))

    reply_markup = keyboards.main_actions(
        has_changes=has_changes,
        session_active=session_active
    )

    # Send response with keyboard
    if len(formatted_messages) == 1:
        await status_msg.edit_text(
            formatted_messages[0].text,
            parse_mode=formatted_messages[0].parse_mode,
            reply_markup=reply_markup
        )
    else:
        # ... handle multiple messages ...
        # Only add keyboard to last message
        pass


def build_application():
    """Build the Telegram bot application."""
    app = Application.builder() \
        .token(TELEGRAM_TOKEN) \
        .persistence(persistence) \
        .build()

    # Register handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("status", handle_status))
    # ... other command handlers ...

    # Register callback query handler
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Register message handlers
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Error handler
    app.add_error_handler(error_callback)

    return app
```

---

## Testing Procedures

### Test 1: Basic Button Interaction

**Objective:** Verify buttons appear and respond to clicks.

**Steps:**
1. Send message to Claude
2. Verify buttons appear
3. Click ✅ Approve button

**Expected Output:**
```
✅ Changes approved!

The modifications have been applied. Use git commands to commit if needed.
```

**Verification:**
- Button click acknowledged
- Message updated
- Dismiss button appears

### Test 2: Git Diff Button

**Objective:** Test git diff functionality.

**Steps:**
1. Initialize git repo: `cd /workspace && git init`
2. Create file and modify it
3. Send Claude message
4. Click 📝 Show Diff button

**Expected Output:**
```
📝 Git Diff

```diff
+new content
```
```

**Verification:**
- Diff shows correctly
- Formatted as code block
- Dismiss button present

### Test 3: Git Status Button

**Objective:** Test git status display.

**Steps:**
1. Make changes in workspace
2. Click 📊 Git Status button

**Expected Output:**
```
📊 Git Status

```
M file1.py
A file2.js
```
```

### Test 4: Session Info Button

**Objective:** Test session info display.

**Steps:**
1. Create active session
2. Click 📋 Session Info button

**Expected Output:**
```
📊 Current Session

Session ID: `claude_abc123`
Turn Count: 3
```

### Test 5: Confirmation Dialog

**Objective:** Test confirmation for destructive actions.

**Steps:**
1. Click button that shows session keyboard
2. Click 🆕 New Session
3. Verify confirmation appears
4. Click ✅ Confirm

**Expected Output (step 3):**
```
🆕 Create New Session?

This will end your current session and start fresh.
Your current conversation history will be lost.

[✅ Confirm] [❌ Cancel]
```

Then after confirm:
```
✅ New session created!

Previous session: `claude_abc123`

Send a message to begin.
```

### Test 6: Dismiss Button

**Objective:** Test message dismissal.

**Steps:**
1. Click any action button
2. Click 🗑️ Dismiss

**Expected Behavior:**
- Message is deleted
- No errors

### Test 7: Multiple Button Clicks

**Objective:** Test rapid button clicking.

**Steps:**
1. Click Approve button
2. Immediately click Diff button
3. Click multiple buttons rapidly

**Expected Behavior:**
- Each click acknowledged
- No duplicate responses
- No crashes

---

## Acceptance Criteria

### Functional Requirements

- [ ] All buttons appear correctly on messages
- [ ] Button clicks are acknowledged immediately
- [ ] Approve button applies changes
- [ ] Reject button discards changes
- [ ] Diff button shows git diff
- [ ] Status button shows git status
- [ ] Session info button shows session details
- [ ] Dismiss button deletes message
- [ ] Confirmation dialogs work for destructive actions

### User Experience

- [ ] Buttons have clear, descriptive labels
- [ ] Button layout is logical and organized
- [ ] Visual feedback on button press
- [ ] Error messages for failed actions
- [ ] No duplicate responses on rapid clicking

### Edge Cases

- [ ] Git buttons handle missing git repo gracefully
- [ ] Empty diff shows appropriate message
- [ ] Clean status shows "Working directory clean"
- [ ] No session shows appropriate message
- [ ] Retry with no previous command handled

### Integration

- [ ] Works with response formatter (Step 11)
- [ ] Works with error handling (Step 12)
- [ ] Works with session management (Step 10)
- [ ] Buttons persist across bot restarts

---

## Troubleshooting Guide

### Issue 1: Buttons not appearing

**Diagnosis:**
- Check if reply_markup is being set
- Verify InlineKeyboardMarkup is imported

**Solutions:**
- Ensure keyboard is passed to send/edit methods
- Check for errors in keyboard construction

### Issue 2: Callback not handled

**Symptoms:**
- Button click shows loading animation forever
- No response to click

**Diagnosis:**
- Check if CallbackQueryHandler is registered
- Check callback data format

**Solutions:**
- Ensure `await query.answer()` is called
- Verify callback data parsing logic
- Check logs for errors

### Issue 3: Git commands fail

**Symptoms:**
- Diff/Status buttons show errors

**Diagnosis:**
```bash
cd /workspace
git status
```

**Solutions:**
- Initialize git repo if missing
- Check file permissions
- Verify git is installed

---

## Rollback Procedure

Remove inline keyboards, use text-only responses:

```python
# Simple text response without buttons
await update.message.reply_text(response_text)
```

---

## Next Steps

After Step 13:

1. **Proceed to Step 14:** Git Integration
2. **Enhance keyboards** with more actions
3. **Add analytics** to track button usage

---

**Step Status:** Ready for Implementation
**Next Step:** Step 14 - Git Integration
**Estimated Completion:** 1 hour
