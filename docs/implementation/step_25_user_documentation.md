# Step 25: User Documentation

**Estimated Time:** 30 minutes
**Phase:** 7 - Documentation & Handoff
**Prerequisites:** Security hardening complete (Step 24)

---

## Overview

This step creates comprehensive user-facing documentation that enables both technical and non-technical users to effectively use the claude-remote-runner system. The documentation includes quick start guides, tutorials, command references, and troubleshooting help.

### Context

Good documentation is critical for:
- Enabling independent use without constant support
- Reducing onboarding time for new users
- Providing reference material for occasional users
- Troubleshooting common issues
- Building confidence in using voice control

### Goals

- Create user-friendly quick start guide
- Document all available commands and features
- Provide clear usage examples
- Include troubleshooting FAQ
- Write in accessible language
- Add visual aids where helpful

---

## Implementation Details

### 1. User Guide Structure

Create the following documentation files:

```
docs/user/
├── README.md                    # Overview and quick start
├── getting-started.md           # Detailed onboarding guide
├── voice-commands.md            # Voice command best practices
├── command-reference.md         # Complete command list
├── workflows.md                 # Common workflows and examples
├── troubleshooting.md          # FAQ and common issues
└── tips-and-tricks.md          # Advanced usage tips
```

### 2. Main User README

**docs/user/README.md:**

```markdown
# Claude Remote Runner - User Guide

Welcome! This guide will help you get started with using Claude Code via voice control through Telegram.

## What is Claude Remote Runner?

Claude Remote Runner lets you control Claude Code (Anthropic's AI coding assistant) using your voice through a Telegram bot. You can:

- 🎤 Give coding instructions by voice
- 💻 Execute commands remotely from your phone
- 📱 Work on code from anywhere
- ✅ Review and approve changes before applying
- 🔄 Maintain conversation context across sessions

## Quick Start

### 1. Get Access

Contact your administrator to get your Telegram user ID added to the allowed users list.

**Find your Telegram ID:**
1. Open Telegram
2. Search for `@userinfobot`
3. Send any message
4. Bot will reply with your user ID (e.g., `123456789`)

### 2. Start the Bot

1. Open Telegram
2. Search for your bot: `@your_claude_bot`
3. Send `/start` command
4. You should see a welcome message

### 3. Send Your First Command

**Option A: Voice Command**
1. Tap the microphone icon
2. Speak clearly: "Create a Python hello world script"
3. Release to send
4. Wait for Claude to respond

**Option B: Text Command**
1. Type your command
2. Example: `Create a Python hello world script`
3. Press send

### 4. Review and Approve

1. Claude will respond with what it plans to do
2. Tap **✅ Approve** to apply changes
3. Tap **❌ Reject** to cancel
4. Tap **📝 Show Diff** to review changes first

## Available Commands

### Bot Commands

- `/start` - Initialize the bot
- `/status` - Check your current session
- `/clear` - Start a fresh conversation
- `/help` - Show help message
- `/usage` - Check your rate limit usage

### Voice/Text Commands

Speak or type natural language instructions:

- "Create a Python script that..."
- "Add a function to calculate..."
- "Fix the bug in main.py"
- "Show me the contents of config.json"
- "Explain how the authentication works"

## Need Help?

- 📖 [Getting Started Guide](getting-started.md) - Detailed walkthrough
- 🎤 [Voice Command Tips](voice-commands.md) - Best practices for voice
- 📚 [Command Reference](command-reference.md) - Complete command list
- ❓ [Troubleshooting](troubleshooting.md) - Common issues and solutions
- 💡 [Tips & Tricks](tips-and-tricks.md) - Advanced usage

## Web Interface (Optional)

You can also access Claude Code directly through your browser:

1. Navigate to: `https://claude.yourdomain.com`
2. Enter credentials (ask your admin)
3. Use the terminal interface directly

---

**Need support?** Contact your system administrator or check the troubleshooting guide.
```

### 3. Getting Started Guide

**docs/user/getting-started.md:**

```markdown
# Getting Started with Claude Remote Runner

This guide walks you through your first session using Claude Code via voice control.

## Prerequisites

- ✅ Telegram account
- ✅ Access granted by administrator
- ✅ Bot username from administrator

## Step-by-Step Tutorial

### Step 1: Find and Start the Bot

1. **Open Telegram** on your phone or computer
2. **Tap the search icon** (magnifying glass)
3. **Search for your bot**: `@your_claude_bot_name`
4. **Tap the bot** in search results
5. **Press "START"** button or send `/start` command

**Expected Result:**
You should see a welcome message like:
```
👋 Hello John!

I'm your Claude Code voice assistant.

📱 Send me a voice message with your coding task
💬 Or send a text message with your request
📝 I'll execute it and show you the results
```

**Troubleshooting:**
- ❌ Can't find bot? → Ask admin for exact bot username
- ❌ Bot doesn't respond? → Check with admin that your user ID is authorized

### Step 2: Your First Voice Command

Let's create a simple Python script using voice:

1. **Tap the microphone icon** (bottom right)
2. **Speak clearly**:
   ```
   "Create a Python script called greet.py that asks for a name and says hello to that person"
   ```
3. **Release to send** the voice message

**Tips for Best Results:**
- 🔇 Minimize background noise
- 🗣️ Speak at normal pace (not too fast)
- 📱 Hold phone at comfortable distance
- ✅ Complete sentences work better than fragments

### Step 3: Review the Transcription

Claude will first show you what it heard:

```
🎤 Heard: Create a Python script called greet.py that asks for a name and says hello to that person
```

**Check the transcription:**
- ✅ Accurate? Great, proceed to next step
- ❌ Inaccurate? Send a text message to correct it

### Step 4: Wait for Claude's Response

You'll see:
```
⏳ Claude is working on this...
```

This typically takes **10-30 seconds** depending on the complexity.

### Step 5: Review Claude's Response

Claude will reply with what it created:

```
🤖 Claude:
I'll create a Python script called greet.py that prompts for a name and greets the person.

Created file: greet.py
```python
def main():
    name = input("What is your name? ")
    print(f"Hello, {name}! Nice to meet you.")

if __name__ == "__main__":
    main()
```

Would you like me to make any changes?

[✅ Approve] [❌ Reject]
[📝 Show Diff] [📊 Git Status]
```

### Step 6: Review Changes (Optional)

Before approving, you can check what changed:

1. **Tap "📝 Show Diff"** to see the git diff
2. **Tap "📊 Git Status"** to see file status

The bot will show:
```diff
+ Created: greet.py
```

### Step 7: Approve or Reject

**To approve and apply changes:**
1. Tap **✅ Approve**
2. Claude will apply the changes
3. You'll see: `✅ Changes approved and applied!`

**To reject changes:**
1. Tap **❌ Reject**
2. Changes will be discarded
3. You can send a new command to try again

### Step 8: Continue the Conversation

Claude remembers the conversation context. You can continue:

**Voice message:**
```
"Add error handling to the script"
```

Claude will modify the existing `greet.py` file based on context.

### Step 9: Check Your Session

At any time, send `/status` to see:
```
📊 Status:
Session ID: session_123456789_1707087234
Turn count: 2
Workspace: /workspace
```

### Step 10: Start Fresh (When Needed)

If Claude seems confused or you want to start a new task:

1. Send `/clear` command
2. You'll see: `🗑️ Conversation history cleared. Starting fresh!`
3. Begin with a new task

## Common Workflows

### Workflow 1: Create New File

```
Voice: "Create a JavaScript file called calculator.js with add and subtract functions"
→ Review response
→ Tap ✅ Approve
→ Done!
```

### Workflow 2: Modify Existing File

```
Voice: "Add a multiply function to calculator.js"
→ Claude modifies existing file
→ Tap 📝 Show Diff to review changes
→ Tap ✅ Approve if looks good
```

### Workflow 3: Debug Code

```
Voice: "There's a bug in calculator.js, the subtract function returns the wrong result"
→ Claude analyzes and fixes
→ Review the fix
→ Tap ✅ Approve
```

### Workflow 4: Explain Code

```
Voice: "Explain how the calculator.js file works"
→ Claude provides explanation
→ No approval needed (read-only)
```

## Next Steps

Now that you've completed your first session:

- 📖 Read [Voice Commands Best Practices](voice-commands.md)
- 📚 Explore [Common Workflows](workflows.md)
- 💡 Learn [Tips & Tricks](tips-and-tricks.md)

## Getting Help

If something doesn't work as expected:

1. Check [Troubleshooting Guide](troubleshooting.md)
2. Send `/help` to the bot
3. Contact your system administrator

---

**Congratulations!** You've completed your first Claude Code session via voice control. 🎉
```

### 4. Voice Commands Best Practices

**docs/user/voice-commands.md:**

```markdown
# Voice Commands Best Practices

Tips for getting the best transcription accuracy and Claude responses.

## Recording Environment

### ✅ DO:
- Use a quiet room
- Speak in a quiet office or home
- Use headphones with microphone for calls
- Record in noise-cancelling environment

### ❌ DON'T:
- Record in loud cafes or public spaces
- Record with TV/music in background
- Record while driving (dangerous!)
- Record in windy conditions outdoors

## Speaking Technique

### Speak Clearly and Naturally

**Good:**
```
"Create a Python script called data_processor.py that reads a CSV file and calculates the average of the price column"
```

**Bad (too fast/mumbled):**
```
"uhh make a python thing that uh reads csv and gets average prices or something"
```

### Use Complete Sentences

**Good:**
```
"Add error handling to the login function in auth.py"
```

**Bad (fragments):**
```
"error handling... login... auth.py"
```

### Be Specific

**Good:**
```
"Create a React component called UserProfile that displays a user's name, email, and profile picture"
```

**Bad (too vague):**
```
"make a user thing"
```

## Command Structure

### Action + Target + Details

Follow this pattern for best results:

```
[ACTION] + [TARGET] + [DETAILS]
```

**Examples:**

1. **Create** + **a Python function** + **that validates email addresses**
   ```
   "Create a Python function that validates email addresses using regex"
   ```

2. **Update** + **the README file** + **with installation instructions**
   ```
   "Update the README file to include detailed installation instructions"
   ```

3. **Fix** + **the bug in calculator.js** + **where division by zero crashes**
   ```
   "Fix the bug in calculator.js where division by zero causes the app to crash"
   ```

4. **Explain** + **the authentication flow** + **in simple terms**
   ```
   "Explain how the authentication flow works in simple terms"
   ```

## Common Voice Commands

### File Operations

- "Create a new file called [filename] with [description]"
- "Delete the file [filename]"
- "Rename [old_name] to [new_name]"
- "Show me the contents of [filename]"
- "List all files in the workspace"

### Code Modification

- "Add a function called [name] that [description]"
- "Update the [function/class] to [change]"
- "Remove the [function/variable/code]"
- "Refactor [code element] to be more efficient"

### Debugging

- "Fix the error in [filename] where [description]"
- "Debug why [problem description]"
- "Find and fix the bug causing [symptom]"

### Documentation

- "Add comments to [filename]"
- "Create a README explaining [topic]"
- "Document the [function/class/module]"
- "Explain how [code/feature] works"

### Testing

- "Create unit tests for [function/class]"
- "Add test cases for edge cases in [filename]"
- "Run the tests and fix any failures"

### Git Operations

- "Show git status"
- "Show me the diff of my changes"
- "Create a git commit with message [message]"

## Handling Transcription Errors

If the transcription is wrong:

1. **Check the transcription** Claude shows you
2. **If wrong:** Send a text message to correct it
3. **Example:**
   ```
   Bot: 🎤 Heard: "Create a Python strict called hello"
   You: (text) "Create a Python *script* called hello"
   ```

## Rate Limits

Be aware of usage limits:

- **Per minute:** 10 commands
- **Per hour:** 60 commands
- **Per day:** 300 commands

**Check your usage:** Send `/usage` command

## Voice Message Length

- **Recommended:** 5-30 seconds
- **Maximum:** 120 seconds (2 minutes)
- **Too short:** <1 second may fail
- **Too long:** >2 minutes will be rejected

## Language and Accent

- **Supported:** English (US/UK/International)
- **Tips for non-native speakers:**
  - Speak slowly and enunciate
  - Use standard technical terms in English
  - Consider using text for complex commands
  - Practice with simple commands first

## Examples of Great Voice Commands

### Example 1: Web Development
```
"Create an Express.js server on port 3000 with routes for GET /users, POST /users, and DELETE /users/:id. Include error handling middleware."
```

### Example 2: Data Processing
```
"Write a Python script that reads a JSON file called data.json, filters out entries where status is inactive, and saves the results to active_data.json."
```

### Example 3: Testing
```
"Add Jest unit tests for the UserController class in controllers/UserController.js, covering all public methods including edge cases."
```

### Example 4: Refactoring
```
"Refactor the database connection logic in db.js to use connection pooling and add retry logic for failed connections."
```

### Example 5: Documentation
```
"Add JSDoc comments to all functions in utils/helpers.js, including parameter types, return types, and usage examples."
```

## Troubleshooting Voice Issues

| Problem | Solution |
|---------|----------|
| Transcription always wrong | Check environment noise, speak slower |
| Cuts off mid-sentence | Speak continuously, don't pause >1 second |
| Bot doesn't hear technical terms | Spell out acronyms (SQL → "S Q L") |
| Echo/distortion in recording | Move away from walls, use headset |
| Voice message too long | Break into multiple shorter commands |

---

**Pro Tip:** Start with simple commands to build confidence, then gradually use more complex instructions as you get comfortable with the system.
```

### 5. Quick Reference Card

**docs/user/quick-reference.md:**

```markdown
# Quick Reference Card

## Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start/restart bot | `/start` |
| `/status` | Show session info | `/status` |
| `/clear` | Clear conversation | `/clear` |
| `/help` | Show help | `/help` |
| `/usage` | Show rate limits | `/usage` |

## Interactive Buttons

| Button | Action |
|--------|--------|
| ✅ Approve | Apply changes |
| ❌ Reject | Discard changes |
| 📝 Show Diff | View file changes |
| 📊 Git Status | Check working tree |

## Common Voice Commands

### Files
- "Create a file called [name]"
- "Show contents of [file]"
- "Delete [file]"
- "List all files"

### Code
- "Add function [name] that [does X]"
- "Fix the bug in [file]"
- "Refactor [code]"
- "Add error handling to [function]"

### Git
- "Show git status"
- "Show diff"
- "Commit with message [msg]"

### Help
- "Explain [code/concept]"
- "How does [feature] work"
- "Show documentation for [topic]"

## Rate Limits

- **Per minute:** 10 commands
- **Per hour:** 60 commands
- **Per day:** 300 commands

Check usage: `/usage`

## Tips

1. ✅ Speak clearly in quiet environment
2. ✅ Use complete sentences
3. ✅ Be specific in commands
4. ✅ Review transcription before approving
5. ✅ Use /clear if Claude seems confused

## Web Access

URL: `https://claude.yourdomain.com`

Login with credentials from admin.

## Support

- 📖 Full docs: [User Guide](README.md)
- ❓ Issues: [Troubleshooting](troubleshooting.md)
- 👤 Admin: contact@yourdomain.com

---

Print this reference card for quick access! 📄
```

### 6. Troubleshooting Guide

**docs/user/troubleshooting.md:**

```markdown
# Troubleshooting Guide

Common issues and solutions.

## Bot Access Issues

### Problem: Bot doesn't respond to /start

**Symptoms:**
- Send `/start` command
- No response from bot

**Solutions:**
1. Check you're messaging the correct bot username
2. Verify bot is online (ask admin)
3. Check your internet connection
4. Try restarting Telegram app
5. Contact admin to verify your user ID is authorized

### Problem: "Unauthorized" message

**Symptoms:**
- Bot replies: "⛔ Unauthorized"

**Solutions:**
1. Contact admin with your Telegram user ID
2. Get user ID: Message `@userinfobot` in Telegram
3. Wait for admin to add you to allowed users
4. Try `/start` again after being added

## Voice Command Issues

### Problem: Transcription is inaccurate

**Symptoms:**
- Bot shows: "🎤 Heard: [wrong text]"

**Solutions:**
1. **Immediate:** Send correct version as text message
2. **Prevention:**
   - Record in quieter environment
   - Speak slower and more clearly
   - Hold phone at comfortable distance
   - Avoid background noise

### Problem: Voice message rejected

**Symptoms:**
- "⚠️ Voice message too long (max 120 seconds)"

**Solutions:**
1. Break command into smaller parts
2. Record shorter message (<2 minutes)
3. Use text for complex multi-step instructions

### Problem: Technical terms transcribed wrong

**Symptoms:**
- "React" becomes "re-act"
- "SQL" becomes "sequel"

**Solutions:**
1. Spell out acronyms: "S-Q-L" instead of "SQL"
2. Speak technical terms slowly
3. Use text for commands with many technical terms
4. Correct via text after seeing transcription

## Claude Response Issues

### Problem: Claude seems confused

**Symptoms:**
- Responses don't make sense
- Claude asks about unrelated topics
- Same response repeated

**Solutions:**
1. Send `/clear` to start fresh conversation
2. Be more specific in next command
3. Provide more context in your request
4. Check if you're in middle of previous task

### Problem: "Claude encountered an error"

**Symptoms:**
- Bot shows error message
- Command doesn't execute

**Solutions:**
1. Try rephrasing the command
2. Check command is reasonable/possible
3. Send `/status` to check session
4. Try `/clear` and start fresh
5. Contact admin if persists

### Problem: Response takes too long

**Symptoms:**
- "⏳ Claude is working..." for >2 minutes

**Solutions:**
1. Wait patiently (complex tasks take time)
2. If >5 minutes, try sending new command
3. Use simpler, more specific commands
4. Contact admin if consistently slow

## Rate Limiting Issues

### Problem: "Too many requests" message

**Symptoms:**
- "⏱️ Slow down! Maximum 10 requests per minute"

**Solutions:**
1. Wait the indicated time
2. Check usage: `/usage`
3. Space out commands more
4. If limits are too restrictive, contact admin

### Problem: "Daily limit reached"

**Symptoms:**
- "⏱️ Daily limit reached (300 requests/day)"

**Solutions:**
1. Wait until next day
2. Prioritize essential tasks
3. Use commands more efficiently
4. Contact admin about increasing limits

## Approval Workflow Issues

### Problem: Buttons don't work

**Symptoms:**
- Tap button, nothing happens

**Solutions:**
1. Wait a moment and try again
2. Check internet connection
3. Restart Telegram app
4. Send new command if stuck

### Problem: Already approved but need to undo

**Symptoms:**
- Tapped ✅ Approve by mistake
- Want to revert changes

**Solutions:**
1. Send voice/text: "Undo the last change"
2. Or: "Revert the changes to [file]"
3. Use web interface to manually revert
4. Contact admin for help with git revert

## Web Interface Issues

### Problem: Can't access web interface

**Symptoms:**
- https://claude.yourdomain.com doesn't load

**Solutions:**
1. Verify URL is correct
2. Check internet connection
3. Try different browser
4. Try incognito/private mode
5. Contact admin to verify site is up

### Problem: "Authentication required"

**Symptoms:**
- Login prompt appears
- Credentials don't work

**Solutions:**
1. Verify username and password with admin
2. Check for typos (passwords are case-sensitive)
3. Try resetting credentials with admin
4. Clear browser cache and try again

## Session Issues

### Problem: Claude doesn't remember previous commands

**Symptoms:**
- Each command starts fresh
- Context is lost

**Solutions:**
1. Check session status: `/status`
2. Don't use `/clear` unless needed
3. Continue in same chat (don't create new chat)
4. Contact admin if session persistence is broken

### Problem: Session seems stuck

**Symptoms:**
- Commands don't execute
- Bot always shows old context

**Solutions:**
1. Send `/clear` to reset session
2. Restart with `/start`
3. Contact admin if problem persists

## File and Git Issues

### Problem: "Show Diff" shows nothing

**Symptoms:**
- Tap 📝 Show Diff
- Bot says "(No changes)"

**Solutions:**
1. Claude might not have made changes yet
2. Changes might have been already applied
3. Check git status: Tap 📊 Git Status

### Problem: Git commands fail

**Symptoms:**
- "Not a git repository" error

**Solutions:**
1. Workspace might not be initialized as git repo
2. Contact admin to initialize git
3. Or use web interface to run: `git init`

## Getting More Help

If your issue isn't listed here:

1. **Check full documentation:**
   - [Getting Started](getting-started.md)
   - [Voice Commands](voice-commands.md)
   - [Common Workflows](workflows.md)

2. **Try the bot help:**
   - Send `/help` for basic info
   - Send `/status` to check system state

3. **Contact Support:**
   - Email: admin@yourdomain.com
   - Include:
     - Your Telegram username
     - Description of issue
     - What you've tried
     - Screenshots if relevant

4. **Emergency Issues:**
   - System down completely
   - Security concerns
   - Data loss
   - Contact admin immediately

---

**Most common solutions:**
1. Try `/clear` and start fresh
2. Use text instead of voice
3. Restart Telegram app
4. Wait a few minutes and try again
5. Contact admin
```

---

## Testing

### Documentation Review Checklist

- [ ] **Clarity:** Can a non-technical user understand it?
- [ ] **Completeness:** All features documented?
- [ ] **Accuracy:** Information is correct and up-to-date?
- [ ] **Examples:** Concrete examples provided?
- [ ] **Structure:** Easy to navigate and find information?
- [ ] **Troubleshooting:** Common issues addressed?

### User Testing

1. **Ask a colleague to follow the getting started guide**
   - Can they complete it without help?
   - Note any confusion or questions
   - Update docs based on feedback

2. **Test all example commands**
   - Verify each example works as described
   - Update examples if needed

3. **Check all links**
   - Verify internal links work
   - Verify external links are current

---

## Acceptance Criteria

- [ ] User guide README created
- [ ] Getting started guide with step-by-step tutorial
- [ ] Voice commands best practices documented
- [ ] Quick reference card created
- [ ] Comprehensive troubleshooting guide
- [ ] All documentation is clear and easy to understand
- [ ] Examples are concrete and tested
- [ ] Links between documents work
- [ ] At least one non-technical person has reviewed docs
- [ ] Documentation is accessible in the repository

---

## Related Documentation

- [Implementation Plan - Phase 7](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation_plan.md#phase-7-documentation--handoff-1-2-hours)
- [Step 26: Operational Runbooks](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_26_operational_runbooks.md)
- [Design Document - Section 5: Usage Guide](/Users/vlad/WebstormProjects/claude-remote-runner/docs/design.md#5-usage-guide)

---

**Status:** Complete
**Last Updated:** February 4, 2026
**Next Step:** [Step 26: Operational Runbooks](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_26_operational_runbooks.md)
