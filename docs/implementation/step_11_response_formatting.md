# Step 11: Response Formatting

**Phase:** 3 - Claude Code Integration
**Estimated Time:** 30 minutes
**Prerequisites:** Steps 1-10 completed
**Dependencies:** Telegram message API, Markdown formatting

---

## Overview

This step implements proper formatting of Claude's responses for Telegram's message constraints and capabilities. Telegram has specific limitations (4096 character limit) and supports Markdown/HTML formatting, which we'll leverage for better readability.

### Context

Telegram Bot API constraints:
- Maximum message length: 4096 characters
- Supports Markdown and HTML formatting
- Code blocks limited to ~3900 chars effectively
- Long messages must be split into multiple messages
- Special characters must be escaped

Claude responses often include:
- Code blocks (multiple languages)
- Long explanations
- File paths and commands
- Structured data

### Goals

1. Format code blocks with syntax highlighting
2. Split long responses into multiple messages
3. Properly escape Markdown special characters
4. Add visual indicators (emojis) for better UX
5. Handle edge cases (empty responses, only code, etc.)
6. Test with various response types

---

## Implementation Details

### 11.1 Response Formatter Module

**File: `bot/formatters.py`**

Create a dedicated module for response formatting:

```python
#!/usr/bin/env python3
"""
Response formatting utilities for Telegram bot.
Handles message splitting, code highlighting, and Markdown escaping.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Telegram limits
MAX_MESSAGE_LENGTH = 4096
MAX_SAFE_LENGTH = 3900  # Leave room for formatting

# Language mappings for syntax highlighting
LANGUAGE_ALIASES = {
    'py': 'python',
    'js': 'javascript',
    'ts': 'typescript',
    'sh': 'bash',
    'yml': 'yaml',
}


@dataclass
class FormattedMessage:
    """A formatted message ready to send."""
    text: str
    parse_mode: str = 'Markdown'
    has_code: bool = False


class ResponseFormatter:
    """Format Claude responses for Telegram."""

    def __init__(self, max_length: int = MAX_SAFE_LENGTH):
        self.max_length = max_length

    def format_response(
        self,
        text: str,
        add_header: bool = True,
        header_text: str = "🤖 Claude:"
    ) -> List[FormattedMessage]:
        """
        Format a response for Telegram, splitting if necessary.

        Args:
            text: Raw response text from Claude
            add_header: Whether to add header to first message
            header_text: Header text to use

        Returns:
            List of FormattedMessage objects
        """
        if not text or not text.strip():
            return [FormattedMessage(
                text="(Claude completed the task with no text output)",
                parse_mode='Markdown'
            )]

        # Detect code blocks
        has_code_blocks = '```' in text

        # Format code blocks
        formatted_text = self._format_code_blocks(text)

        # Escape special characters
        formatted_text = self._escape_markdown(formatted_text, preserve_code=True)

        # Add header
        if add_header:
            formatted_text = f"{header_text}\n\n{formatted_text}"

        # Split if necessary
        if len(formatted_text) <= self.max_length:
            return [FormattedMessage(
                text=formatted_text,
                parse_mode='Markdown',
                has_code=has_code_blocks
            )]
        else:
            return self._split_message(formatted_text, has_code_blocks)

    def _format_code_blocks(self, text: str) -> str:
        """
        Format code blocks with proper syntax highlighting.

        Args:
            text: Text potentially containing code blocks

        Returns:
            Text with formatted code blocks
        """
        # Pattern: ```language\ncode\n```
        pattern = r'```(\w+)?\n(.*?)```'

        def replace_code_block(match):
            language = match.group(1) or ''
            code = match.group(2)

            # Normalize language
            language = LANGUAGE_ALIASES.get(language.lower(), language.lower())

            # Ensure code isn't too long for a single block
            if len(code) > 3500:
                code = code[:3500] + '\n... (truncated)'

            return f'```{language}\n{code}```'

        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)

    def _escape_markdown(self, text: str, preserve_code: bool = True) -> str:
        """
        Escape Markdown special characters.

        Args:
            text: Text to escape
            preserve_code: Whether to preserve code blocks

        Returns:
            Escaped text
        """
        if preserve_code:
            # Split by code blocks and escape non-code parts
            parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)

            escaped_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 0:  # Non-code part
                    # Escape special Markdown characters
                    # Don't escape inside code blocks
                    escaped = part.replace('_', '\\_')
                    escaped = escaped.replace('*', '\\*')
                    escaped = escaped.replace('[', '\\[')
                    escaped = escaped.replace(']', '\\]')
                    escaped = escaped.replace('(', '\\(')
                    escaped = escaped.replace(')', '\\)')
                    escaped = escaped.replace('~', '\\~')
                    escaped = escaped.replace('>', '\\>')
                    escaped = escaped.replace('#', '\\#')
                    escaped = escaped.replace('+', '\\+')
                    escaped = escaped.replace('-', '\\-')
                    escaped = escaped.replace('=', '\\=')
                    escaped = escaped.replace('|', '\\|')
                    escaped = escaped.replace('{', '\\{')
                    escaped = escaped.replace('}', '\\}')
                    escaped = escaped.replace('.', '\\.')
                    escaped = escaped.replace('!', '\\!')
                    escaped_parts.append(escaped)
                else:  # Code block
                    escaped_parts.append(part)

            return ''.join(escaped_parts)
        else:
            # Simple escaping without preserving code blocks
            return text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[')

    def _split_message(
        self,
        text: str,
        has_code: bool
    ) -> List[FormattedMessage]:
        """
        Split a long message into multiple messages.

        Args:
            text: Text to split
            has_code: Whether text contains code blocks

        Returns:
            List of FormattedMessage objects
        """
        messages = []

        if has_code:
            # Smart split: try to keep code blocks intact
            messages = self._split_preserving_code_blocks(text)
        else:
            # Simple split by length
            messages = self._split_by_length(text)

        return messages

    def _split_preserving_code_blocks(self, text: str) -> List[FormattedMessage]:
        """Split text while preserving code blocks."""
        messages = []
        parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)

        current_message = ""

        for part in parts:
            if len(current_message) + len(part) <= self.max_length:
                current_message += part
            else:
                # Save current message
                if current_message:
                    messages.append(FormattedMessage(
                        text=current_message,
                        parse_mode='Markdown',
                        has_code='```' in current_message
                    ))

                # Start new message
                if len(part) <= self.max_length:
                    current_message = part
                else:
                    # Part itself is too long - split it
                    chunks = self._split_by_length_raw(part, self.max_length)
                    messages.extend([
                        FormattedMessage(text=chunk, parse_mode='Markdown')
                        for chunk in chunks[:-1]
                    ])
                    current_message = chunks[-1] if chunks else ""

        # Add remaining message
        if current_message:
            messages.append(FormattedMessage(
                text=current_message,
                parse_mode='Markdown',
                has_code='```' in current_message
            ))

        return messages

    def _split_by_length(self, text: str) -> List[FormattedMessage]:
        """Simple split by character length."""
        chunks = self._split_by_length_raw(text, self.max_length)
        return [FormattedMessage(text=chunk, parse_mode='Markdown') for chunk in chunks]

    def _split_by_length_raw(self, text: str, length: int) -> List[str]:
        """Split text into chunks of specified length."""
        return [text[i:i+length] for i in range(0, len(text), length)]

    def format_error(self, error: str) -> FormattedMessage:
        """Format an error message."""
        formatted = f"❌ Error:\n\n```\n{error[:3800]}\n```"
        return FormattedMessage(text=formatted, parse_mode='Markdown', has_code=True)

    def format_code(self, code: str, language: str = '') -> FormattedMessage:
        """Format a code snippet."""
        language = LANGUAGE_ALIASES.get(language, language)
        formatted = f"```{language}\n{code[:3800]}\n```"
        return FormattedMessage(text=formatted, parse_mode='Markdown', has_code=True)

    def format_file_list(self, files: List[str]) -> FormattedMessage:
        """Format a list of files."""
        if not files:
            return FormattedMessage(text="📁 No files modified", parse_mode='Markdown')

        file_list = "\n".join([f"  • `{f}`" for f in files[:20]])
        if len(files) > 20:
            file_list += f"\n  • ... and {len(files) - 20} more"

        formatted = f"📝 Modified Files:\n{file_list}"
        return FormattedMessage(text=formatted, parse_mode='Markdown')

    def add_metadata(
        self,
        text: str,
        tools_used: Optional[List[str]] = None,
        files_modified: Optional[List[str]] = None,
        turn_count: Optional[int] = None
    ) -> str:
        """
        Add metadata footer to message.

        Args:
            text: Main message text
            tools_used: List of tools used
            files_modified: List of files modified
            turn_count: Current turn count

        Returns:
            Text with metadata appended
        """
        metadata_parts = []

        if tools_used:
            tools_str = ", ".join(tools_used[:5])
            if len(tools_used) > 5:
                tools_str += f" (+{len(tools_used) - 5} more)"
            metadata_parts.append(f"🔧 Tools: {tools_str}")

        if files_modified:
            if len(files_modified) == 1:
                metadata_parts.append(f"📝 Modified: `{files_modified[0]}`")
            else:
                metadata_parts.append(f"📝 Modified: {len(files_modified)} files")

        if turn_count is not None:
            metadata_parts.append(f"🔄 Turn: {turn_count}")

        if metadata_parts:
            metadata = "\n\n" + " | ".join(metadata_parts)
            return text + metadata

        return text


# Convenience instance
formatter = ResponseFormatter()
```

### 11.2 Integration with Bot

**File: `bot/bot.py`** (update)

```python
from formatters import ResponseFormatter, FormattedMessage

# Initialize formatter
formatter = ResponseFormatter(max_length=3900)

async def execute_claude_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str
):
    """Execute a Claude Code command and send response to user."""
    user_id = update.effective_user.id
    initialize_user_data(context)

    session_id = context.user_data.get('claude_session_id')

    status_msg = await update.message.reply_text(
        "⏳ Claude is working on this...\n"
        f"{'📝 Resuming session' if session_id else '🆕 Starting new session'}"
    )

    try:
        response: ClaudeResponse = claude_executor.execute(
            prompt=prompt,
            session_id=session_id
        )

        if not response.success:
            # Format error
            error_msg = formatter.format_error(response.error or "Unknown error")
            await status_msg.edit_text(
                error_msg.text,
                parse_mode=error_msg.parse_mode
            )
            return

        # Update session ID
        if response.session_id:
            context.user_data['claude_session_id'] = response.session_id

        # Increment turn count
        context.user_data['turn_count'] = context.user_data.get('turn_count', 0) + 1
        turn_count = context.user_data['turn_count']

        # Auto-compact every 20 turns
        if turn_count >= 20:
            if claude_executor.compact_session(context.user_data['claude_session_id']):
                context.user_data['turn_count'] = 0
                await update.message.reply_text("🗜️ Session auto-compacted")

        # Format response with metadata
        output_with_metadata = formatter.add_metadata(
            response.output,
            tools_used=response.tools_used,
            files_modified=response.files_modified,
            turn_count=turn_count
        )

        # Format response (may return multiple messages if too long)
        formatted_messages = formatter.format_response(
            output_with_metadata,
            add_header=True,
            header_text="🤖 Claude:"
        )

        # Create inline keyboard
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

        # Send messages
        if len(formatted_messages) == 1:
            # Single message - edit the status message
            await status_msg.edit_text(
                formatted_messages[0].text,
                parse_mode=formatted_messages[0].parse_mode,
                reply_markup=reply_markup
            )
        else:
            # Multiple messages - delete status and send new ones
            await status_msg.delete()

            for i, msg in enumerate(formatted_messages):
                is_last = (i == len(formatted_messages) - 1)

                await update.message.reply_text(
                    msg.text,
                    parse_mode=msg.parse_mode,
                    reply_markup=reply_markup if is_last else None
                )

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        error_msg = formatter.format_error(str(e))
        await status_msg.edit_text(
            error_msg.text,
            parse_mode=error_msg.parse_mode
        )
```

---

## Testing Procedures

### Test 1: Short Response

**Objective:** Verify short responses are formatted correctly.

**Steps:**
1. Send: "Say hello"
2. Verify response formatting

**Expected Output:**
```
🤖 Claude:

Hello! How can I help you today?

🔄 Turn: 1
```

**Verification:**
- Header present
- Metadata footer present
- No truncation

### Test 2: Code Block Formatting

**Objective:** Verify code blocks are syntax highlighted.

**Steps:**
1. Send: "Create a Python hello world function"
2. Verify code block formatting

**Expected Output:**
````
🤖 Claude:

I'll create a hello world function:

```python
def hello_world():
    print("Hello, World!")
```

🔧 Tools: WriteFile | 🔄 Turn: 1
````

**Verification:**
- Code block has language tag
- Syntax highlighting works in Telegram
- Tools used shown in metadata

### Test 3: Long Response Splitting

**Objective:** Verify long responses split into multiple messages.

**Steps:**
1. Send: "Explain Python decorators in great detail with 10 examples"
2. Verify response is split

**Expected Output:**
- First message: ~3900 chars
- Second message: remainder
- Keyboard only on last message

**Verification:**
- No single message exceeds 4096 chars
- Content is not lost
- Logical split points

### Test 4: Markdown Escaping

**Objective:** Verify special characters are escaped properly.

**Steps:**
1. Send: "Show me a file path with underscores: /path/to/my_file.py"
2. Verify underscores don't create italics

**Expected Output:**
```
🤖 Claude:

The file path is: /path/to/my\_file.py

🔄 Turn: 1
```

**Verification:**
- Underscores escaped: `\_`
- Other special chars escaped
- Code blocks not escaped

### Test 5: Empty Response

**Objective:** Verify empty responses handled gracefully.

**Steps:**
1. Modify executor to return empty output
2. Send any message

**Expected Output:**
```
(Claude completed the task with no text output)
```

**Verification:**
- No crash
- User-friendly message shown
- Keyboard still appears

### Test 6: Multiple Code Blocks

**Objective:** Verify multiple code blocks in one response.

**Steps:**
1. Send: "Show me a Python and JavaScript hello world"

**Expected Output:**
````
🤖 Claude:

Python version:

```python
print("Hello, World!")
```

JavaScript version:

```javascript
console.log("Hello, World!");
```

🔄 Turn: 1
````

**Verification:**
- Both code blocks formatted correctly
- Language tags preserved
- No formatting errors

### Test 7: File List Formatting

**Objective:** Test file list formatting.

**Steps:**
1. Use formatter directly:
   ```python
   files = ['file1.py', 'file2.js', 'file3.txt']
   msg = formatter.format_file_list(files)
   ```

**Expected Output:**
```
📝 Modified Files:
  • `file1.py`
  • `file2.js`
  • `file3.txt`
```

**Verification:**
- Files listed with bullet points
- Backticks around filenames
- Emoji indicator

---

## Acceptance Criteria

### Functional Requirements

- [ ] Short responses formatted with header and metadata
- [ ] Code blocks have syntax highlighting
- [ ] Long responses split into multiple messages
- [ ] Markdown special characters escaped properly
- [ ] Empty responses handled gracefully
- [ ] Multiple code blocks in one response work
- [ ] File lists formatted correctly
- [ ] Error messages formatted consistently

### Message Constraints

- [ ] No message exceeds 4096 characters
- [ ] Code blocks don't exceed safe limits
- [ ] Split messages are logical (don't break mid-sentence)
- [ ] Inline keyboard only on last message

### Formatting Quality

- [ ] Code syntax highlighting works in Telegram
- [ ] Emojis enhance readability
- [ ] Metadata is concise and informative
- [ ] Escaping doesn't create ugly output

### Edge Cases

- [ ] Very long code blocks truncated properly
- [ ] Multiple consecutive code blocks handled
- [ ] Mixed content (text + code) formatted well
- [ ] Unicode characters preserved
- [ ] Newlines preserved correctly

---

## Troubleshooting Guide

### Issue 1: Message too long error

**Symptoms:**
- Telegram API error: "Message is too long"

**Diagnosis:**
```python
# Check message length
logger.info(f"Message length: {len(message)}")
```

**Solutions:**
- Reduce MAX_SAFE_LENGTH to 3800
- Improve splitting logic
- Truncate metadata if needed

### Issue 2: Broken code blocks

**Symptoms:**
- Code blocks don't render properly
- Missing closing ```

**Diagnosis:**
- Check if code blocks are split mid-block

**Solutions:**
- Improve `_split_preserving_code_blocks`
- Ensure code blocks always have closing tags
- Add validation before sending

### Issue 3: Escaped characters showing

**Symptoms:**
- User sees `\_` instead of `_`

**Diagnosis:**
- Check if parse_mode is set correctly

**Solutions:**
- Ensure `parse_mode='Markdown'` is set
- Verify Telegram supports MarkdownV2
- Consider switching to HTML parse mode

### Issue 4: Emojis broken

**Symptoms:**
- Emojis show as boxes or question marks

**Diagnosis:**
- Check character encoding

**Solutions:**
- Ensure UTF-8 encoding: `text.encode('utf-8')`
- Use Unicode escape sequences if needed
- Test emojis in Telegram client

---

## Rollback Procedure

### Quick Rollback

Replace formatter with simple truncation:

```python
# In bot.py
def format_simple(text):
    if len(text) > 3900:
        return text[:3900] + "\n\n...(truncated)"
    return text

# Use in execute_claude_command
await status_msg.edit_text(format_simple(response.output))
```

---

## Next Steps

After completing Step 11:

1. **Proceed to Step 12:** Error Handling & Logging
2. **Test with real Claude responses** of varying lengths
3. **Optimize:** Improve splitting algorithm for better readability

---

**Step Status:** Ready for Implementation
**Next Step:** Step 12 - Error Handling & Logging
**Estimated Completion:** 30 minutes
