# Step 20: Webhook Configuration

**Estimated Time:** 30 minutes
**Phase:** Phase 5 - Production Deployment
**Prerequisites:** Step 19 (Production Deployment) completed with all services healthy
**Status:** Not Started

---

## Overview

This step configures the Telegram webhook to enable the production bot to receive messages via HTTPS callbacks instead of polling. Webhooks are essential for production deployments as they provide real-time message delivery, reduce server load, and scale better than polling. This is the final step to make your Telegram bot fully operational in production.

### Context

Telegram bots can receive updates via two methods:
1. **Polling** (getUpdates) - Bot repeatedly asks Telegram servers for new messages
2. **Webhook** (setWebhook) - Telegram servers push messages to your server via HTTPS POST

Webhooks are **required** for production because:
- Lower latency (messages arrive instantly)
- More efficient (no constant polling)
- Better scalability (handles multiple bots easily)
- **Required** for this deployment (bot configured for webhook mode)

This step configures Telegram to send all messages to your deployed bot's webhook endpoint.

### Goals

- ✅ Set Telegram webhook to production URL
- ✅ Verify webhook SSL certificate accepted
- ✅ Test webhook connectivity
- ✅ Validate message delivery
- ✅ Test complete voice message workflow
- ✅ Verify approval workflow functions
- ✅ Document webhook configuration

---

## Implementation Details

### 1. Prepare Webhook URL

**Construct Webhook URL:**

```
Format: https://claude.yourdomain.com/${TELEGRAM_TOKEN}

Example:
https://claude.yourdomain.com/1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
```

**Get Your Telegram Token:**

From Coolify environment variables or your .env file:
```bash
# Your token format:
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
```

**Full Webhook URL:**
```
https://claude.yourdomain.com/1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890
```

**Security Note:**
- The token in the URL acts as authentication
- Only Telegram knows this URL (don't publish it)
- Unique token prevents unauthorized webhook calls

### 2. Set Telegram Webhook

**Method 1: Using curl (Recommended)**

From your local machine or server:

```bash
# Set webhook
curl -X POST "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://claude.yourdomain.com/<YOUR_TELEGRAM_TOKEN>",
    "allowed_updates": ["message", "callback_query"],
    "drop_pending_updates": true,
    "max_connections": 40
  }'
```

**Replace:**
- `<YOUR_TELEGRAM_TOKEN>` with your actual token (both places)
- `claude.yourdomain.com` with your actual domain

**Parameter Explanation:**

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `url` | Your webhook endpoint | Where Telegram sends updates |
| `allowed_updates` | `["message", "callback_query"]` | Only receive messages and button clicks |
| `drop_pending_updates` | `true` | Discard old messages (clean start) |
| `max_connections` | `40` | Max simultaneous connections from Telegram |

**Expected Response (Success):**

```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

**If Error Response:**

```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: bad webhook: ..."
}
```

See [Troubleshooting Guide](#troubleshooting-guide) for solutions.

**Method 2: Using Telegram Bot API Browser**

Visit in browser:
```
https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/setWebhook?url=https://claude.yourdomain.com/<YOUR_TELEGRAM_TOKEN>&allowed_updates=["message","callback_query"]
```

Same response as Method 1.

**Method 3: Using Python Script**

```python
#!/usr/bin/env python3
import requests
import os

TOKEN = os.environ['TELEGRAM_TOKEN']
WEBHOOK_URL = f"https://claude.yourdomain.com/{TOKEN}"

response = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True,
        "max_connections": 40
    }
)

print(response.json())
```

Run:
```bash
python set_webhook.py
```

### 3. Verify Webhook Configuration

**Get Webhook Info:**

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getWebhookInfo"
```

**Expected Response (Success):**

```json
{
  "ok": true,
  "result": {
    "url": "https://claude.yourdomain.com/1234567890:ABC...",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40,
    "allowed_updates": ["message", "callback_query"],
    "ip_address": "95.123.45.67",
    "last_error_date": 0,
    "last_error_message": ""
  }
}
```

**Verification Checklist:**

- [x] `url` matches your webhook URL exactly
- [x] `has_custom_certificate`: false (using Let's Encrypt)
- [x] `pending_update_count`: 0 (or low number)
- [x] `ip_address` matches your server IP
- [x] `last_error_date`: 0 (no errors)
- [x] `last_error_message`: "" (empty)

**If `last_error_message` not empty:**

Common errors and solutions:

| Error Message | Cause | Solution |
|---------------|-------|----------|
| "Connection refused" | Bot not listening on port | Check container logs |
| "SSL certificate verification failed" | SSL certificate invalid | Verify Let's Encrypt cert |
| "Wrong response from the webhook" | Bot returning non-200 status | Check bot response code |
| "Read timeout" | Bot taking too long to respond | Optimize bot response time (<10s) |

**Screenshot Location:** Terminal showing successful `getWebhookInfo` response

### 4. Test Webhook Delivery

**Initial Test - Send /start Command:**

1. Open Telegram app on your phone
2. Find your bot (search for bot username)
3. Send: `/start`
4. Wait 2-3 seconds

**Expected Response:**

```
👋 Hello [Your Name]!

I'm your Claude Code voice assistant.

📱 Send me a voice message with your coding task
💬 Or send a text message with your request
📝 I'll execute it and show you the results

Commands:
/start - Show this message
/status - Check current session
/clear - Clear conversation history
```

**If No Response:**

Check bot logs:
```bash
# Via Coolify UI
Resource → Logs → telegram-bot

# Via SSH
docker logs claude-remote-runner-telegram-bot-1 --tail 50 -f
```

Look for:
- "Received webhook POST request"
- Processing log messages
- Any error messages

**Monitor Bot Logs During Test:**

```bash
# SSH to server
ssh root@your-server-ip

# Follow bot logs
docker logs -f claude-remote-runner-telegram-bot-1

# Expected log output when sending /start:
# INFO - Received update: message from user 123456789
# INFO - Command: /start
# INFO - User authorized: 123456789
# INFO - Sent welcome message
```

### 5. Test Voice Message Workflow

**Complete End-to-End Test:**

**Step 1: Send Voice Message**

1. In Telegram bot chat, tap microphone icon
2. Record voice message: "Check if the workspace directory is empty"
3. Release to send

**Expected Bot Response Sequence:**

```
🎤 Heard: Check if the workspace directory is empty

⏳ Claude is working on this...

🤖 Claude:
I'll check the workspace directory for you.

[Claude's response about directory contents]

[Buttons: ✅ Approve | ❌ Reject]
[Buttons: 📝 Show Diff | 📊 Git Status]
```

**Step 2: Test Approval Buttons**

Tap: **✅ Approve**

**Expected:**
```
✅ Changes approved and committed!

📝 Commit: Apply changes from Claude

Prompt: Check if the workspace directory is empty
🕐 2026-02-04 16:45:23
```

Or if no git changes:
```
✅ Changes approved!

ℹ️ No git changes detected (may have been informational output)
```

**Verification in Logs:**

```bash
# Bot logs should show:
INFO - Voice message from user 123456789
INFO - Downloaded voice file: sessions/voice_123456789_1707...ogg
INFO - ffmpeg conversion successful
INFO - Deepgram API transcription: "Check if the workspace directory is empty"
INFO - Executing Claude command
INFO - Claude execution successful
INFO - Approval workflow initiated
INFO - User approved change: change_123456789_1707...
```

### 6. Test Additional Commands

**Test /status Command:**

Send: `/status`

**Expected:**
```
📊 Session Status

Claude Session:
└─ ID: session_123456789_1707...
└─ Turn Count: 1/20 (auto-compact at 20)

Pending Changes:
└─ None

Approval History:
└─ Approved: 1
└─ Rejected: 0
└─ Total: 1

Git Repository:
└─ Branch: main
└─ Latest Commit: abc1234

Workspace:
└─ Path: /workspace
└─ Files: 0

User Info:
└─ Telegram ID: 123456789
└─ Name: [Your Name]
```

**Test /help Command:**

Send: `/help`

**Expected:**
Full help text with all commands documented.

**Test /info Command:**

Send: `/info`

**Expected:**
System diagnostics showing all dependencies installed.

### 7. Test Error Handling

**Test Unauthorized User (if ALLOWED_USER_IDS configured):**

Have a friend send a message to the bot (someone NOT in ALLOWED_USER_IDS).

**Expected:**
```
⛔ You are not authorized to use this bot.
```

**Test Invalid Voice Message:**

Send very short voice message (<1 second).

**Expected:**
Should still transcribe, or show appropriate error if too short.

### 8. Monitor Webhook Statistics

**Check Webhook Metrics:**

```bash
curl "https://api.telegram.org/bot<YOUR_TELEGRAM_TOKEN>/getWebhookInfo" | jq .result
```

**Key Metrics:**

```json
{
  "pending_update_count": 0,      // Should stay at 0 or very low
  "last_synchronization_error_date": 0,  // Should be 0
  "last_error_date": 0,           // Should be 0
  "last_error_message": ""        // Should be empty
}
```

**If `pending_update_count` > 10:**
- Bot may be slow responding
- Messages queuing up
- Check bot performance

**If `last_error_date` recent:**
- Check `last_error_message` for details
- Review bot logs
- Fix underlying issue

### 9. Document Webhook Configuration

**Create Configuration Record:**

Add to `DEPLOYMENT.md` or create `WEBHOOK_CONFIG.md`:

```markdown
# Webhook Configuration

**Configured:** 2026-02-04 16:45 UTC
**Configured By:** Your Name

## Webhook Details

**URL:** https://claude.yourdomain.com/[TOKEN]
**Allowed Updates:** message, callback_query
**Max Connections:** 40
**Drop Pending Updates:** true

## Verification

**Status:** ✓ Active
**Last Error:** None
**Pending Updates:** 0
**IP Address:** 95.123.45.67

## Testing

**Tests Completed:**
- [x] /start command
- [x] Voice message transcription
- [x] Claude command execution
- [x] Approval workflow
- [x] Inline buttons
- [x] /status command
- [x] /help command
- [x] /info command
- [x] Error handling
- [x] Unauthorized user rejection

**Test Date:** 2026-02-04
**All Tests:** PASSED

## Webhook Statistics

**Total Messages Received:** 12
**Success Rate:** 100%
**Average Response Time:** <3 seconds
**Errors:** 0
```

---

## Testing Procedures

### Test Case 1: Basic Webhook Delivery

**Steps:**
1. Set webhook using curl
2. Send /start in Telegram
3. Verify response within 3 seconds

**Expected:**
- Welcome message received
- Logs show webhook POST received
- No errors

### Test Case 2: Voice Transcription Pipeline

**Steps:**
1. Send clear voice message: "Hello Claude"
2. Wait for transcription
3. Verify transcription accuracy

**Expected:**
```
🎤 Heard: Hello Claude
⏳ Claude is working on this...
🤖 Claude: [Response]
```

### Test Case 3: Complete Approval Workflow

**Steps:**
1. Send voice: "Create a file called test.txt with hello world"
2. Wait for response
3. Tap "📝 Show Diff"
4. Review diff
5. Tap "✅ Approve"

**Expected:**
- Diff shows file creation
- Approval commits to git
- File persists in workspace

### Test Case 4: Concurrent Messages

**Steps:**
1. Send 3 text messages rapidly:
   - "What is 2+2?"
   - "What is 3+3?"
   - "What is 4+4?"
2. Verify all process correctly

**Expected:**
- All messages received
- Responses in correct order
- No messages lost
- No errors in logs

### Test Case 5: Large Voice Message

**Steps:**
1. Record 30-second voice message
2. Send to bot
3. Monitor transcription time

**Expected:**
- Transcription completes within 10 seconds
- Accuracy >90%
- No timeout errors

### Test Case 6: Button Callback Handling

**Steps:**
1. Create pending change
2. Test each button:
   - ✅ Approve
   - ❌ Reject
   - 📝 Show Diff
   - 📊 Git Status

**Expected:**
- All buttons respond within 2 seconds
- Correct actions performed
- Confirmation messages shown

### Test Case 7: Webhook Error Recovery

**Steps:**
1. Stop bot container: `docker stop telegram-bot`
2. Send message (will fail)
3. Start bot: `docker start telegram-bot`
4. Check `getWebhookInfo` for error

**Expected:**
- Error recorded in webhook info
- Error cleared after bot restart
- Pending messages delivered

### Test Case 8: SSL Certificate Verification

**Steps:**
```bash
# Verify Telegram accepts our SSL
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://claude.yourdomain.com/<TOKEN>"
```

**Expected:**
- `"ok": true`
- No SSL verification errors
- Webhook set successfully

---

## Screenshots Guidance

### Screenshot 1: Webhook Set Successfully
**Location:** Terminal
**Content:**
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### Screenshot 2: Telegram Conversation
**Location:** Telegram app
**Content:**
- /start command sent
- Welcome message received
- Voice message sent
- Transcription shown
- Claude response with buttons
- Approval confirmation

**Annotations:**
- Highlight voice message bubble
- Circle transcription text
- Point to approval buttons

### Screenshot 3: Webhook Info
**Location:** Terminal
**Content:**
- getWebhookInfo response
- All fields showing correct values
- No errors

### Screenshot 4: Bot Logs
**Location:** SSH session or Coolify logs
**Content:**
- Webhook POST received
- Message processing
- Claude execution
- Response sent
- No errors

---

## Acceptance Criteria

### Webhook Configuration
- ✅ Webhook URL set correctly
- ✅ SSL certificate accepted by Telegram
- ✅ Allowed updates configured
- ✅ Max connections set appropriately
- ✅ Webhook verified via getWebhookInfo

### Functionality
- ✅ Bot responds to /start command
- ✅ Voice messages transcribe accurately (>90%)
- ✅ Claude commands execute successfully
- ✅ Approval workflow functions correctly
- ✅ All inline buttons work
- ✅ All commands (/status, /help, /info) work
- ✅ Error handling graceful

### Performance
- ✅ Messages delivered within 3 seconds
- ✅ Voice transcription <10 seconds
- ✅ No timeout errors
- ✅ Concurrent messages handled
- ✅ No message loss

### Security
- ✅ Unauthorized users rejected
- ✅ Only allowed updates processed
- ✅ HTTPS enforced
- ✅ Token in URL for authentication

---

## Troubleshooting Guide

### Issue 1: Webhook Set Failed - SSL Error

**Symptoms:**
```json
{
  "ok": false,
  "error_code": 400,
  "description": "Bad Request: bad webhook: HTTPS url must be provided for webhook"
}
```

**Solutions:**
1. Verify URL starts with `https://` (not http://)
2. Check SSL certificate valid:
   ```bash
   curl -I https://claude.yourdomain.com
   ```
3. Ensure Let's Encrypt certificate generated (Step 19)
4. Wait a few minutes for SSL propagation

### Issue 2: Webhook Set Failed - Certificate Verification

**Symptoms:**
```json
{
  "description": "Bad Request: bad webhook: failed to resolve host: ..."
}
```

**Solutions:**
1. Verify DNS resolves:
   ```bash
   dig claude.yourdomain.com
   ```
2. Check domain spelling (no typos)
3. Wait for DNS propagation
4. Test from different location

### Issue 3: Bot Not Responding

**Symptoms:**
- Send message, no response
- Webhook shows no errors

**Diagnosis:**
```bash
# Check bot logs
docker logs claude-remote-runner-telegram-bot-1 --tail 100

# Check if webhook POST received
# Look for: "Received update" or similar
```

**Solutions:**
1. Verify bot container running:
   ```bash
   docker ps | grep telegram-bot
   ```
2. Check bot listening on port 8443:
   ```bash
   docker exec telegram-bot netstat -tlnp | grep 8443
   ```
3. Review environment variables (TELEGRAM_TOKEN correct)
4. Restart bot container

### Issue 4: Voice Transcription Failing

**Symptoms:**
- "Transcription failed" message

**Diagnosis:**
```bash
# Check bot logs for Deepgram API errors
docker logs telegram-bot | grep -i whisper
```

**Solutions:**
1. Verify DEEPGRAM_API_KEY correct and has credits
2. Check ffmpeg installed:
   ```bash
   docker exec telegram-bot ffmpeg -version
   ```
3. Test with shorter voice message
4. Review OpenAI API status page

### Issue 5: Pending Updates Piling Up

**Symptoms:**
- getWebhookInfo shows `pending_update_count` > 50

**Diagnosis:**
- Bot responding too slowly
- Bot crashed and queue built up

**Solutions:**
1. Clear pending updates:
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://claude.yourdomain.com/<TOKEN>" \
     -d "drop_pending_updates=true"
   ```
2. Optimize bot response time
3. Increase max_connections
4. Scale bot resources

### Issue 6: Webhook Errors in Logs

**Symptoms:**
- `last_error_message` populated
- `last_error_date` recent

**Common Errors:**

**"Wrong response from the webhook: 500 Internal Server Error"**
- Bot code error
- Check bot logs for Python exceptions
- Fix error and restart

**"Connection timed out"**
- Bot taking >60 seconds to respond
- Optimize Claude command execution
- Implement async processing

**"Read timeout"**
- Similar to connection timeout
- Bot must respond within 60 seconds
- Consider acknowledging webhook immediately, processing async

### Issue 7: Buttons Not Working

**Symptoms:**
- Tap button, nothing happens

**Diagnosis:**
```bash
# Check callback_query handler registered
docker logs telegram-bot | grep -i "callback"
```

**Solutions:**
1. Verify `allowed_updates` includes "callback_query"
2. Check callback handler registered in bot code
3. Review callback_data format
4. Test with simple callback first

---

## Rollback Procedure

### Remove Webhook (Rollback to Polling)

If webhook causing issues, can temporarily switch back to polling:

```bash
# Delete webhook
curl -X POST "https://api.telegram.org/bot<TOKEN>/deleteWebhook" \
  -d "drop_pending_updates=true"

# Verify deletion
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Expected:
# "url": ""  (empty)
```

**Then update bot code to use polling:**

```python
# In bot.py, change from:
app.run_webhook(...)

# To:
app.run_polling()
```

**Restart bot:**
```bash
docker restart telegram-bot
```

**Note:** Polling NOT recommended for production, use only for debugging.

### Re-set Webhook After Fix

After fixing issues:

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://claude.yourdomain.com/<TOKEN>" \
  -d "allowed_updates=[\"message\",\"callback_query\"]" \
  -d "drop_pending_updates=true"
```

---

## Additional Notes

### Webhook vs Polling Comparison

| Feature | Webhook | Polling |
|---------|---------|---------|
| **Latency** | <1 second | 1-3 seconds |
| **Server Load** | Low | High |
| **Scalability** | Excellent | Poor |
| **SSL Required** | Yes | No |
| **Production Ready** | Yes | No |
| **Development** | More setup | Easier |

### Telegram Webhook Limits

- **Max connections:** 40-100 (we use 40)
- **Timeout:** 60 seconds (bot must respond within 60s)
- **Retry:** Telegram retries failed webhooks
- **Queue:** Up to 10,000 pending updates

### Webhook Best Practices

1. **Respond quickly:** Acknowledge webhook within 1 second
2. **Process async:** For long tasks, respond immediately then process
3. **Handle errors:** Return 200 OK even if processing fails (prevents retries)
4. **Monitor pending updates:** Keep `pending_update_count` near 0
5. **Use drop_pending_updates:** When deploying updates (clean slate)

### Security Considerations

**Webhook URL as Authentication:**
- Token in URL prevents unauthorized webhook calls
- Only Telegram knows this URL
- Don't publish webhook URL publicly

**IP Whitelisting (Optional):**
```nginx
# In nginx/Traefik (advanced)
# Allow only from Telegram's IP ranges
allow 149.154.160.0/20;
allow 91.108.4.0/22;
deny all;
```

### Future Enhancements

- [ ] Implement webhook IP validation
- [ ] Add webhook request signing verification
- [ ] Implement async task queue for long operations
- [ ] Add webhook analytics (response times, error rates)
- [ ] Monitor webhook health with alerts

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** After webhook configured and tested, proceed to Step 21 (Monitoring Setup)
**Estimated Completion:** 30 minutes (including all testing)
