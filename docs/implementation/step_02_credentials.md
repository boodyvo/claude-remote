# Step 2: Obtain API Keys & Credentials

**Estimated Time:** 30 minutes
**Prerequisites:**
- Step 1 completed (project structure initialized)
- Internet connection
- Email address for account creation
- Mobile phone (for Telegram)
- Credit card (for OpenAI/Anthropic billing)

**Deliverable:** All API keys obtained, documented, and stored in .env file ready for use

## Overview

This step focuses on obtaining all necessary API credentials for the project. We'll create accounts with Telegram, Anthropic, and OpenAI, generate API keys, and securely store them. This is a critical step as without these credentials, the system cannot function.

The process is straightforward but requires attention to detail. Each service has different sign-up processes and key generation mechanisms. We'll walk through each one systematically and test the keys to ensure they're valid before proceeding.

**Why This Matters:**
- API keys are the authentication mechanism for all services
- Invalid or improperly configured keys will cause deployment failures
- Proper key management prevents security vulnerabilities
- Testing keys early prevents debugging issues later

## Implementation Details

### What to Build

1. **Telegram Bot Token:** Create bot via BotFather and obtain token
2. **Telegram User ID:** Get your personal Telegram user ID for authorization
3. **Anthropic API Key:** Sign up for Claude Code API access and generate key
4. **Deepgram API Key:** Sign up for Deepgram API access and generate key
5. **.env File:** Store all credentials securely in local .env file
6. **Test Credentials:** Verify each API key works with simple test calls

### How to Implement

#### Step 2.1: Create Telegram Bot

**Process:**

1. Open Telegram app (mobile or desktop)
2. Search for `@BotFather` (official Telegram bot creation tool)
3. Start conversation with `/start`
4. Create new bot with `/newbot` command

**Detailed Steps:**

```
You: /newbot

BotFather: Alright, a new bot. How are we going to call it?
Please choose a name for your bot.

You: Claude Remote Runner

BotFather: Good. Now let's choose a username for your bot.
It must end in `bot`. Like this, for example: TetrisBot or tetris_bot.

You: claude_remote_runner_bot
(or any unique name ending in _bot)

BotFather: Done! Congratulations on your new bot. You will find it at
t.me/claude_remote_runner_bot. You can now add a description, about
section and profile picture for your bot, see /help for a list of commands.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

Keep your token secure and store it safely, it can be used by anyone
to control your bot.

For a description of the Bot API, see this page:
https://core.telegram.org/bots/api
```

**Save the Token:**
```bash
# Open your .env file
nano .env  # or vim, code, etc.

# Add the token
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
```

**Optional: Configure Bot Settings**

```
# Set description (shown in chat)
/setdescription
Select your bot
Type: "Remote Claude Code execution with voice control"

# Set about text (shown in profile)
/setabouttext
Select your bot
Type: "This bot enables voice-controlled Claude Code execution on a remote server. Speak your coding tasks and Claude will execute them."

# Set commands menu
/setcommands
Select your bot
Type:
start - Initialize bot and show welcome message
status - Check current session information
clear - Clear conversation history and start fresh
help - Show available commands and usage guide

# Set profile picture (optional)
/setuserpic
Select your bot
Upload an image (512x512 recommended)
```

#### Step 2.2: Get Your Telegram User ID

Your Telegram User ID is needed to restrict bot access to only you (security feature).

**Method 1: Using @userinfobot**

1. Open Telegram
2. Search for `@userinfobot`
3. Start conversation with `/start`
4. Bot will reply with your User ID

```
@userinfobot:
Id: 123456789
First name: Vlad
Username: @yourusername
Language: en
```

**Method 2: Using Your Own Bot (Alternative)**

```python
# Temporarily add this to bot.py to log user IDs
async def handle_start(update, context):
    user_id = update.effective_user.id
    print(f"User ID: {user_id}")  # This will appear in logs
    await update.message.reply_text(f"Your User ID is: {user_id}")
```

**Save Your User ID:**
```bash
# Add to .env file
ALLOWED_USER_IDS=123456789
```

**For Multiple Users:**
```bash
# Comma-separated list
ALLOWED_USER_IDS=123456789,987654321,555555555
```

#### Step 2.3: Obtain Anthropic API Key

**Sign Up Process:**

1. Visit: https://console.anthropic.com/
2. Click "Sign Up" or "Get Started"
3. Create account with email and password
4. Verify email address
5. Complete account setup

**Generate API Key:**

1. Log into Anthropic Console: https://console.anthropic.com/
2. Navigate to "API Keys" section (usually in left sidebar or top menu)
3. Click "Create Key" or "Generate New Key"
4. Give it a name: `claude-remote-runner-production`
5. Click "Create"
6. **IMPORTANT:** Copy the key immediately - it's shown only once

**Key Format:**
```
sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Add to .env:**
```bash
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Billing Setup:**

1. Navigate to "Billing" in Anthropic Console
2. Add credit card information
3. Set spending limits (recommended: $50/month for personal use)
4. Enable spending alerts

**Pricing Notes (as of 2026):**
- Claude 3.5 Sonnet: $3/MTok input, $15/MTok output
- Typical usage: $20-50/month for moderate personal use
- 200K context window

#### Step 2.4: Obtain OpenAI API Key

**Sign Up Process:**

1. Visit: https://platform.openai.com/signup
2. Create account with email/Google/Microsoft
3. Verify email address
4. Complete phone verification (required for API access)

**Generate API Key:**

1. Log into OpenAI Platform: https://platform.openai.com/
2. Click on your profile icon (top right)
3. Select "API keys" or navigate to https://platform.openai.com/api-keys
4. Click "+ Create new secret key"
5. Give it a name: `claude-remote-runner-whisper`
6. Select permissions: "All" (or specific: Deepgram API only)
7. Click "Create secret key"
8. **IMPORTANT:** Copy the key immediately - shown only once

**Key Format:**
```
sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Add to .env:**
```bash
DEEPGRAM_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Billing Setup:**

1. Navigate to "Billing" at https://platform.openai.com/account/billing/overview
2. Add credit card (required for API access)
3. Add initial credit ($5-10 recommended for testing)
4. Set up spending limits:
   - Hard limit: $50/month
   - Soft limit: $40/month (get email alert)

**Pricing Notes (as of 2026):**
- Deepgram API: $0.0043/minute = $0.36/hour
- 100 hours/month = $25.80
- Alternative: GPT-4o Mini Transcribe at $0.003/min = $18 for 100 hours

#### Step 2.5: Create Complete .env File

Now compile all credentials into your `.env` file:

```bash
# Create .env from template
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Complete .env file:**
```bash
# Anthropic API Key (required)
# Obtained from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Telegram Bot Configuration (required)
# Created via @BotFather: https://t.me/botfather
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

# Webhook URL (required for production, update domain later)
# Format: https://your-domain.com/${TELEGRAM_TOKEN}
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}

# OpenAI API Key for Whisper transcription (required)
# Obtained from: https://platform.openai.com/api-keys
DEEPGRAM_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Allowed Telegram User IDs (comma-separated, STRONGLY RECOMMENDED)
# Get your ID from @userinfobot on Telegram
ALLOWED_USER_IDS=123456789

# Basic Auth for Web UI (optional, recommended for production)
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your-secure-password-here

# Port Configuration (optional, defaults shown)
WEB_PORT=3000
BOT_PORT=8443
```

**Security Check:**
```bash
# Verify .env is in .gitignore
grep "^\.env$" .gitignore

# If not, add it
echo ".env" >> .gitignore

# Verify .env is not tracked by git
git status
# Should NOT show .env in untracked files
```

#### Step 2.6: Test All Credentials

**Test Telegram Bot Token:**

```bash
# Replace <TOKEN> with your actual token
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

Expected response:
```json
{
  "ok": true,
  "result": {
    "id": 1234567890,
    "is_bot": true,
    "first_name": "Claude Remote Runner",
    "username": "claude_remote_runner_bot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false
  }
}
```

**Test Anthropic API Key:**

```bash
# Create test script
cat > test_anthropic.sh << 'EOF'
#!/bin/bash
source .env

curl https://api.anthropic.com/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 50,
    "messages": [
      {"role": "user", "content": "Say hello"}
    ]
  }'
EOF

chmod +x test_anthropic.sh
./test_anthropic.sh
```

Expected response:
```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello!"
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 5
  }
}
```

**Test OpenAI API Key:**

```bash
# Create test script
cat > test_openai.sh << 'EOF'
#!/bin/bash
source .env

curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $DEEPGRAM_API_KEY"
EOF

chmod +x test_openai.sh
./test_openai.sh
```

Expected response (truncated):
```json
{
  "object": "list",
  "data": [
    {
      "id": "whisper-1",
      "object": "model",
      "created": 1677610602,
      "owned_by": "openai"
    },
    ...
  ]
}
```

### Code Examples

**Python Script to Test All Keys:**

```python
#!/usr/bin/env python3
"""
Test all API credentials are valid.
Run with: python test_credentials.py
"""

import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def test_telegram():
    """Test Telegram bot token."""
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        return False, "TELEGRAM_TOKEN not found in .env"

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_name = data['result']['first_name']
                return True, f"✓ Telegram bot: {bot_name}"
        return False, f"✗ Invalid token: {response.text}"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def test_anthropic():
    """Test Anthropic API key."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return False, "ANTHROPIC_API_KEY not found in .env"

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "content-type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Hi"}]
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return True, "✓ Anthropic API key valid"
        return False, f"✗ Invalid key: {response.status_code} {response.text[:100]}"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def test_openai():
    """Test OpenAI API key."""
    api_key = os.getenv('DEEPGRAM_API_KEY')
    if not api_key:
        return False, "DEEPGRAM_API_KEY not found in .env"

    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Check if whisper-1 model is available
            models = [m['id'] for m in data['data']]
            if 'whisper-1' in models:
                return True, "✓ OpenAI API key valid (Whisper available)"
            return True, "⚠ OpenAI API key valid (Whisper not found)"
        return False, f"✗ Invalid key: {response.status_code}"
    except Exception as e:
        return False, f"✗ Error: {str(e)}"

def main():
    print("Testing API Credentials...")
    print("=" * 50)

    tests = [
        ("Telegram Bot", test_telegram),
        ("Anthropic API", test_anthropic),
        ("OpenAI API", test_openai)
    ]

    all_passed = True
    for name, test_func in tests:
        success, message = test_func()
        print(f"\n{name}:")
        print(f"  {message}")
        if not success:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All credentials are valid!")
        print("\nReady to proceed to Step 3: Local Docker Compose Testing")
        return 0
    else:
        print("✗ Some credentials are invalid. Please check and retry.")
        return 1

if __name__ == "__main__":
    exit(main())
```

**Save as `test_credentials.py` and run:**

```bash
# Install requests library if needed
pip install requests python-dotenv

# Run test
python test_credentials.py
```

### Project Structure

After this step, your files should include:

```
claude-remote-runner/
├── .env                        # ← NEW: Your actual credentials (git-ignored)
├── .env.example                # Template with placeholder values
├── test_credentials.py         # ← NEW: Credential testing script
├── test_anthropic.sh           # ← NEW: Anthropic test script
├── test_openai.sh              # ← NEW: OpenAI test script
├── .gitignore                  # Must include .env
├── README.md
├── LICENSE
├── bot/
├── workspace/
├── sessions/
├── backups/
└── docs/
```

## Testing & Validation

### Test Cases

**Test 1: Telegram Bot Token Validity**
```bash
curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe"
# Expected: {"ok":true, ...} with bot details
```

**Test 2: Telegram User ID Obtained**
```bash
# Check .env file
grep "ALLOWED_USER_IDS" .env
# Expected: ALLOWED_USER_IDS=123456789 (or your actual ID)
```

**Test 3: Anthropic API Key Validity**
```bash
./test_anthropic.sh
# Expected: JSON response with "Hello!" message
```

**Test 4: OpenAI API Key Validity**
```bash
./test_openai.sh
# Expected: JSON response with list of models including "whisper-1"
```

**Test 5: .env File Not in Git**
```bash
git status
# Expected: .env should NOT appear (neither tracked nor untracked)

cat .gitignore | grep "^.env$"
# Expected: Line exists
```

**Test 6: All Credentials Work Together**
```bash
python test_credentials.py
# Expected: All tests pass with ✓ marks
```

### Acceptance Criteria

- [ ] Telegram bot created via @BotFather
- [ ] Telegram bot token obtained (format: `NNNNNNNNNN:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
- [ ] Telegram User ID obtained (format: 9-10 digit number)
- [ ] Anthropic account created and API key generated
- [ ] Anthropic billing configured with spending limits
- [ ] OpenAI account created and API key generated
- [ ] OpenAI billing configured with credit added
- [ ] .env file created with all required variables
- [ ] .env file is in .gitignore (not tracked by Git)
- [ ] Telegram bot token tested successfully with curl
- [ ] Anthropic API key tested successfully (sample message works)
- [ ] OpenAI API key tested successfully (Whisper model accessible)
- [ ] All test scripts pass without errors
- [ ] Spending limits configured on all paid APIs

### How to Test

**Comprehensive Test Procedure:**

1. **Visual Inspection of .env:**
   ```bash
   cat .env
   # Verify all variables are present with actual values (not placeholders)
   ```

2. **Run Individual API Tests:**
   ```bash
   # Test each API individually
   ./test_anthropic.sh
   ./test_openai.sh
   curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe"
   ```

3. **Run Comprehensive Test:**
   ```bash
   python test_credentials.py
   ```

4. **Verify Security:**
   ```bash
   # Ensure .env is not in git
   git status --ignored | grep "\.env"
   # Expected: Shows .env in ignored files section

   # Try to stage .env (should fail or be ignored)
   git add .env
   git status
   # Expected: .env should NOT appear in staged files
   ```

5. **Verify Billing:**
   - Log into Anthropic Console → Billing
   - Log into OpenAI Platform → Billing
   - Confirm credit card added and limits set

Expected output from `test_credentials.py`:
```
Testing API Credentials...
==================================================

Telegram Bot:
  ✓ Telegram bot: Claude Remote Runner

Anthropic API:
  ✓ Anthropic API key valid

OpenAI API:
  ✓ OpenAI API key valid (Whisper available)

==================================================
✓ All credentials are valid!

Ready to proceed to Step 3: Local Docker Compose Testing
```

## Troubleshooting

### Issue 1: Telegram Bot Token Invalid

**Symptoms:**
```json
{"ok":false,"error_code":401,"description":"Unauthorized"}
```

**Causes:**
- Token copied incorrectly (extra spaces, missing characters)
- Used old/revoked token
- Token not fully generated

**Solutions:**
1. Check for whitespace:
   ```bash
   # Remove any whitespace
   TELEGRAM_TOKEN=$(echo $TELEGRAM_TOKEN | tr -d ' \n')
   ```

2. Regenerate token:
   - Go to @BotFather
   - Send `/revoke` and select your bot
   - Generate new token with `/token`
   - Update .env file

3. Verify token format:
   ```bash
   # Should be: NNNNNNNNNN:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   echo $TELEGRAM_TOKEN | grep -E '^[0-9]+:[A-Za-z0-9_-]+$'
   ```

### Issue 2: Anthropic API Key Invalid

**Symptoms:**
```json
{"error":{"type":"authentication_error","message":"invalid x-api-key"}}
```

**Causes:**
- Key copied incorrectly
- Account not fully activated
- Billing not set up
- Using wrong API endpoint

**Solutions:**
1. Verify key format:
   ```bash
   # Should start with sk-ant-api03-
   echo $ANTHROPIC_API_KEY | grep '^sk-ant-api03-'
   ```

2. Check account status:
   - Log into https://console.anthropic.com/
   - Verify email is confirmed
   - Check billing section has payment method

3. Regenerate key:
   - Go to API Keys section
   - Delete old key
   - Create new key
   - Update .env immediately

### Issue 3: OpenAI API Key Invalid or Insufficient Credits

**Symptoms:**
```json
{"error":{"message":"Incorrect API key provided","type":"invalid_request_error"}}
```
or
```json
{"error":{"message":"You exceeded your current quota","type":"insufficient_quota"}}
```

**Causes:**
- Key copied incorrectly
- No billing configured
- No credits added
- Quota exceeded

**Solutions:**
1. Verify key format:
   ```bash
   # Should start with sk-
   echo $DEEPGRAM_API_KEY | grep '^sk-'
   ```

2. Add billing:
   - Go to https://platform.openai.com/account/billing/overview
   - Click "Add payment method"
   - Add credit card
   - Add at least $5 in credits

3. Check quota:
   - Go to Usage page
   - Verify you have available credits
   - Check usage limits haven't been exceeded

### Issue 4: Cannot Find Telegram User ID

**Symptoms:**
- @userinfobot doesn't respond
- Unsure what User ID is

**Solutions:**

**Method 1: Use temporary bot code**
```python
# Add to a test script
from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your User ID: {user_id}")

app = Application.builder().token("YOUR_TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
```

**Method 2: Check bot logs**
When you send any message to your bot, the user ID is in the webhook payload.

**Method 3: Use another bot**
Search for other User ID bots:
- @myidbot
- @getidsbot
- @RawDataBot

### Issue 5: .env File Accidentally Committed to Git

**Symptoms:**
```bash
git status
# Shows: .env in staged or committed files
```

**Solutions:**

**If not yet committed:**
```bash
git reset HEAD .env
git status
```

**If already committed:**
```bash
# Remove from Git but keep local file
git rm --cached .env
git commit -m "Remove .env from repository"

# Ensure .gitignore is correct
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Update .gitignore"

# If pushed to remote, update there too
git push
```

**If pushed to public repository (CRITICAL):**
1. **IMMEDIATELY revoke all API keys:**
   - Anthropic: Delete key in Console
   - OpenAI: Delete key in Dashboard
   - Telegram: Use @BotFather to revoke token with `/revoke`

2. Generate new keys and update .env

3. Remove from Git history:
   ```bash
   # Use BFG Repo-Cleaner or git filter-branch
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push
   git push origin --force --all
   ```

### Issue 6: Spending Limits Not Working

**Symptoms:**
- Higher than expected charges
- No spending alerts received

**Solutions:**

**Anthropic:**
1. Log into Console
2. Go to Settings → Billing
3. Set "Budget limit"
4. Enable email alerts
5. Set threshold (e.g., $40 for $50 limit)

**OpenAI:**
1. Go to Billing settings
2. Set "Hard limit" (system stops at this amount)
3. Set "Soft limit" (alert at this amount)
4. Verify email notifications enabled

## Rollback Procedure

### If API Keys Are Compromised

1. **Immediately revoke all keys:**
   ```bash
   # Anthropic
   # → Go to console.anthropic.com → API Keys → Delete key

   # OpenAI
   # → Go to platform.openai.com → API keys → Delete key

   # Telegram
   # → Message @BotFather → /revoke → Select bot
   ```

2. **Remove .env file:**
   ```bash
   rm .env
   ```

3. **Check Git history:**
   ```bash
   git log --all --full-history -- .env
   # If found, use git filter-branch to remove
   ```

4. **Generate new keys:**
   - Follow Steps 2.1-2.4 again
   - Use different key names

### If Incorrect Keys Were Used

1. **Delete incorrect .env:**
   ```bash
   rm .env
   ```

2. **Recreate from template:**
   ```bash
   cp .env.example .env
   ```

3. **Re-follow Steps 2.1-2.4** with correct values

### If Billing Issues Occur

1. **Pause all API usage:**
   - Don't proceed to next steps
   - Don't test APIs further

2. **Contact support:**
   - Anthropic: support@anthropic.com
   - OpenAI: https://help.openai.com/

3. **Review billing:**
   - Check transactions
   - Verify spending limits
   - Adjust as needed

## Next Step

Once all acceptance criteria are met and all tests pass, proceed to:

**Step 3: Local Docker Compose Testing**
- File: `docs/implementation/step_03_local_docker.md`
- Duration: 1-2 hours
- Goal: Create and test Docker Compose configuration locally before deploying to Coolify

Before proceeding, ensure:
1. All API keys obtained and valid
2. .env file created with all required variables
3. .env file is git-ignored
4. All test scripts pass
5. Billing configured with spending limits
6. `python test_credentials.py` shows all ✓ marks

**Checkpoint:** You should now have all necessary API credentials stored securely and tested. The next step will use these credentials to build and test the Docker-based system locally.

**Security Reminder:** Never commit .env to Git, never share keys publicly, and rotate keys every 90 days for security.
