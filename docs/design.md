# Remote Claude Code with Voice Control: Deployment Design

**Project:** claude-remote-runner
**Target Platform:** Coolify on Hetzner VPS
**Date:** February 4, 2026
**Version:** 1.0

---

## 1. Executive Summary

This document outlines the complete deployment design for running Claude Code as a persistent remote service with voice control capabilities and comprehensive web UI for monitoring and control.

**Solution Overview:**
- **Infrastructure:** Hetzner CPX21 VPS (3 vCPU, 8GB RAM, €9/month)
- **Platform:** Coolify self-hosted PaaS with automatic SSL
- **Container:** koogle/claudebox for web-based terminal access
- **Voice Interface:** Telegram bot with Deepgram API transcription
- **Web UI:** Optional CloudCLI integration for advanced file/git operations
- **Total Monthly Cost:** ~$36.30/month (infrastructure + STT + Claude Pro)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│           Hetzner CPX21 VPS (3 vCPU, 8GB RAM, €9/mo)                │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓   │
│  ┃                    Coolify Platform                           ┃   │
│  ┃  ┌────────────────────────────────────────────────────────┐  ┃   │
│  ┃  │    Traefik Reverse Proxy (Auto SSL via Let's Encrypt) │  ┃   │
│  ┃  └────────────────┬───────────────────┬───────────────────┘  ┃   │
│  ┃                   │                   │                       ┃   │
│  ┃         ┌─────────▼─────────┐  ┌──────▼────────────┐        ┃   │
│  ┃         │  Web UI Access     │  │  Telegram Webhook │        ┃   │
│  ┃         │  :3000 → HTTPS     │  │  :8443 → HTTPS    │        ┃   │
│  ┃         └─────────┬─────────┘  └──────┬────────────┘        ┃   │
│  ┃                   │                   │                       ┃   │
│  ┃  ┌────────────────────────────────────────────────────────┐  ┃   │
│  ┃  │         Docker Compose Application                     │  ┃   │
│  ┃  │                                                         │  ┃   │
│  ┃  │  ┌──────────────────────────────────────────────────┐ │  ┃   │
│  ┃  │  │  claudebox-web (koogle/claudebox)                │ │  ┃   │
│  ┃  │  │  - Express + xterm.js + node-pty                 │ │  ┃   │
│  ┃  │  │  - WebSocket terminal streaming                  │ │  ┃   │
│  ┃  │  │  - Optional basic authentication                 │ │  ┃   │
│  ┃  │  │  - Mounts: /workspace, /root/.claude             │ │  ┃   │
│  ┃  │  └──────────────────────────────────────────────────┘ │  ┃   │
│  ┃  │                                                         │  ┃   │
│  ┃  │  ┌──────────────────────────────────────────────────┐ │  ┃   │
│  ┃  │  │  telegram-bot (Python + python-telegram-bot)     │ │  ┃   │
│  ┃  │  │  - Voice message download & ffmpeg conversion    │ │  ┃   │
│  ┃  │  │  - Deepgram API transcription (Nova-3)           │ │  ┃   │
│  ┃  │  │  - Session persistence (PicklePersistence)       │ │  ┃   │
│  ┃  │  │  - Inline keyboard UI (Approve/Reject/Diff)      │ │  ┃   │
│  ┃  │  │  - Calls Claude Code in headless mode            │ │  ┃   │
│  ┃  │  └──────────────────────────────────────────────────┘ │  ┃   │
│  ┃  │                                                         │  ┃   │
│  ┃  │  Persistent Volumes:                                   │  ┃   │
│  ┃  │  - workspace → /workspace (project files)             │  ┃   │
│  ┃  │  - claude-config → /root/.claude (session history)    │  ┃   │
│  ┃  │  - bot-sessions → /app/sessions (bot state)           │  ┃   │
│  ┃  └────────────────────────────────────────────────────────┘  ┃   │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛   │
└──────────────────────────────────────────────────────────────────────┘
                              ↑         ↑
                              │         │
                    ┌─────────┴─────────┴────────┐
                    │                             │
            Mobile Browser              Telegram Voice Messages
      https://claude.yourdomain.com    (Mobile/Desktop Telegram App)
```

### 2.2 Component Interaction Flow

**Voice Command Flow:**
```
1. User sends voice message in Telegram
   ↓
2. Telegram servers forward to webhook at https://claude.yourdomain.com/webhook
   ↓
3. telegram-bot container receives webhook POST request
   ↓
4. Bot downloads voice.ogg file via Telegram API
   ↓
5. ffmpeg converts voice.ogg → voice.wav (16kHz, mono)
   ↓
6. Bot uploads voice.wav to Deepgram API
   ↓
7. Deepgram returns transcribed text
   ↓
8. Bot sends transcription confirmation to user (optional)
   ↓
9. Bot executes: claude -p "transcribed_text" --resume <session_id>
   ↓
10. Claude Code processes request, interacts with workspace files
   ↓
11. Bot captures Claude's output (streaming JSON format)
   ↓
12. Bot formats response with inline keyboard (Approve/Reject/Diff)
   ↓
13. User taps button to approve/reject changes
   ↓
14. Bot executes approved actions or rolls back
```

**Web UI Flow:**
```
1. User opens https://claude.yourdomain.com in browser
   ↓
2. Traefik routes to claudebox-web:3000
   ↓
3. User enters credentials (if basic auth enabled)
   ↓
4. xterm.js terminal loads, establishes WebSocket connection
   ↓
5. User types Claude commands directly in terminal
   ↓
6. Commands execute in containerized environment
   ↓
7. Output streams back to browser in real-time
```

---

## 3. Infrastructure Setup

### 3.1 Hetzner VPS Provisioning

**Recommended Configuration:**
- **Server Type:** CPX21 (AMD vCPU)
- **vCPUs:** 3
- **RAM:** 8 GB
- **Storage:** 160 GB NVMe
- **Traffic:** 20 TB included
- **Cost:** ~€9/month
- **Location:** Nuremberg (nbg1) or Falkenstein (fsn1) for EU/GDPR compliance

**Provisioning Steps:**
1. Log into Hetzner Cloud Console: https://console.hetzner.cloud/
2. Create new project: "claude-remote-runner"
3. Add new server:
   - **Image:** Ubuntu 24.04 LTS (recommended) or Ubuntu 22.04 LTS
   - **Type:** CPX21
   - **Location:** nbg1 (Nuremberg)
   - **SSH Key:** Add your public SSH key
   - **Firewall:** Allow ports 22, 80, 443
4. Note the assigned IPv4 address

**Alternative: Terraform Automation**
```hcl
# terraform/main.tf
terraform {
  required_providers {
    hcloud = {
      source = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

resource "hcloud_server" "claude_server" {
  name        = "claude-remote-runner"
  image       = "ubuntu-24.04"
  server_type = "cpx21"
  location    = "nbg1"
  ssh_keys    = [var.ssh_key_id]

  firewall_ids = [hcloud_firewall.claude_firewall.id]

  labels = {
    project = "claude-remote-runner"
    environment = "production"
  }
}

resource "hcloud_firewall" "claude_firewall" {
  name = "claude-firewall"

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

output "server_ip" {
  value = hcloud_server.claude_server.ipv4_address
}
```

### 3.2 Coolify Installation

**Installation Command (as root):**
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

**What This Does:**
- Installs Docker Engine
- Installs Docker Compose
- Installs Coolify application
- Sets up Traefik reverse proxy
- Configures automatic SSL certificate generation
- Creates admin web interface on port 8000

**Post-Installation:**
1. Access Coolify: `http://<server-ip>:8000`
2. Create admin account **immediately** (security critical)
3. Complete initial setup wizard
4. Configure server settings

**Security Hardening:**
```bash
# Create non-root user for SSH access
adduser claude
usermod -aG sudo claude

# Disable root SSH login
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# Enable UFW firewall (Coolify compatible)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3.3 Domain Configuration

**DNS Setup:**
1. Purchase domain (e.g., from Namecheap, Cloudflare, etc.)
2. Add A record pointing to Hetzner server IP:
   ```
   Type: A
   Name: claude (or @ for root domain)
   Value: <server-ip>
   TTL: 300 (5 minutes)
   ```
3. Wait 5-10 minutes for DNS propagation
4. Verify with: `dig claude.yourdomain.com`

**Subdomain Options:**
- `claude.yourdomain.com` - Web UI access
- `api.yourdomain.com` - API endpoint (if needed)
- `bot.yourdomain.com` - Telegram webhook (alternative)

**Coolify Domain Configuration:**
- Coolify will automatically generate SSL certificate via Let's Encrypt
- Traefik handles all routing and SSL termination
- No manual certificate management required

---

## 4. Application Deployment

### 4.1 Project Structure

```
claude-remote-runner/
├── docker-compose.yml          # Main Docker Compose configuration
├── .env.example                 # Template for environment variables
├── .gitignore                   # Git ignore file (includes .env)
├── README.md                    # Project documentation
├── bot/                         # Telegram bot code
│   ├── bot.py                   # Main bot application
│   ├── handlers.py              # Voice/callback handlers
│   ├── requirements.txt         # Python dependencies
│   └── config.py                # Bot configuration
├── workspace/                   # Mounted as /workspace in containers
│   └── .gitkeep                 # Keep empty directory in git
└── docs/                        # Documentation
    ├── comprehensive_research.md
    └── design.md                # This file
```

### 4.2 Docker Compose Configuration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  # Web-based terminal for browser access
  claudebox-web:
    image: koogle/claudebox:latest
    container_name: claudebox-web
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?}
      - BASIC_AUTH_USER=${BASIC_AUTH_USER:-}
      - BASIC_AUTH_PASS=${BASIC_AUTH_PASS:-}
      - PORT=3000
      - NODE_ENV=production
    volumes:
      - workspace:/workspace
      - claude-config:/root/.claude
    restart: unless-stopped
    networks:
      - claude-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Telegram bot for voice control
  telegram-bot:
    image: python:3.11-slim
    container_name: telegram-bot
    working_dir: /app
    volumes:
      - ./bot:/app                    # Bot source code
      - ./sessions:/app/sessions      # Bot session persistence
      - workspace:/workspace          # Access to project files
      - claude-config:/root/.claude   # Access to Claude config for session management
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN:?}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:?}
      - WEBHOOK_URL=${WEBHOOK_URL:?}
      - ALLOWED_USER_IDS=${ALLOWED_USER_IDS:-}
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8443/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  workspace:
    driver: local
  claude-config:
    driver: local

networks:
  claude-network:
    driver: bridge
```

**Important Coolify Notes:**
- ❌ **Do NOT use `ports:` section** - Coolify manages port mapping via Traefik
- ✅ **Do use environment variables with `:?`** - marks as required in Coolify UI
- ✅ **Do use healthchecks** - enables Coolify to monitor service status
- ✅ **Do use named volumes** - ensures data persistence across deployments

### 4.3 Environment Variables

**.env.example:**
```env
# Claude Code Authentication
# This project uses Claude Pro/Max subscription via 'claude login' (NOT API key)
# IMPORTANT: Do NOT set ANTHROPIC_API_KEY environment variable
# Setup: Run 'claude login' once on the server and authenticate with your Pro/Max account
# Verify with: Run 'claude' and use /status command to confirm subscription is active

# Telegram Bot Configuration (required)
TELEGRAM_TOKEN=1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}

# Deepgram API Key for transcription (required)
# Obtain from: https://console.deepgram.com/
DEEPGRAM_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Allowed Telegram User IDs (comma-separated, optional but recommended)
ALLOWED_USER_IDS=123456789,987654321

# Basic Auth for Web UI (optional)
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your-secure-password-here
```

**Security:**
- ⚠️ **Never commit `.env` to Git** - add to `.gitignore`
- ✅ **Use Coolify's environment variable UI** - encrypted at rest
- ✅ **Rotate credentials every 90 days**

**Obtaining API Keys:**

1. **Claude Pro/Max Subscription:**
   - Ensure you have Claude Pro or Max subscription
   - Run `claude login` on the server
   - Follow browser authentication flow
   - Verify with `claude` then `/status` command

2. **Telegram Bot Token:**
   - Open Telegram, search for @BotFather
   - Send `/newbot` command
   - Follow prompts to name your bot
   - Copy token (format: `1234567890:ABC-DEF...`)

3. **Deepgram API Key:**
   - Visit: https://console.deepgram.com/
   - Sign up or log in
   - Navigate to API Keys section
   - Create new key, copy immediately

### 4.4 Telegram Bot Implementation

**bot/bot.py:**
```python
#!/usr/bin/env python3
"""
Telegram bot for Claude Code voice control.
Handles voice messages, transcribes via Whisper API, executes Claude commands.
"""

import os
import subprocess
import json
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
    filters
)
from deepgram import DeepgramClient, PrerecordedOptions

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']
WEBHOOK_URL = os.environ['WEBHOOK_URL']
ALLOWED_USER_IDS = [
    int(uid.strip())
    for uid in os.environ.get('ALLOWED_USER_IDS', '').split(',')
    if uid.strip()
]

# Initialize Deepgram client
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

# Workspace directory (mounted volume)
WORKSPACE_DIR = Path('/workspace')

# Session persistence
persistence = PicklePersistence(filepath='sessions/bot_data.pkl')
app = Application.builder() \
    .token(TELEGRAM_TOKEN) \
    .persistence(persistence) \
    .build()


def check_authorization(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    if not ALLOWED_USER_IDS:
        return True  # No restrictions if not configured
    return user_id in ALLOWED_USER_IDS


async def handle_start(update: Update, context):
    """Handle /start command."""
    user = update.effective_user

    if not check_authorization(user.id):
        await update.message.reply_text(
            "⛔ You are not authorized to use this bot."
        )
        return

    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "I'm your Claude Code voice assistant.\n\n"
        "📱 Send me a voice message with your coding task\n"
        "💬 Or send a text message with your request\n"
        "📝 I'll execute it and show you the results\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/status - Check current session\n"
        "/clear - Clear conversation history"
    )


async def handle_voice(update: Update, context):
    """Handle voice messages."""
    user_id = update.effective_user.id

    # Authorization check
    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    logger.info(f"Voice message from user {user_id}")

    # 1. Download voice message
    voice = await context.bot.get_file(update.message.voice.file_id)
    voice_file = f'sessions/voice_{user_id}_{datetime.now().timestamp()}.ogg'
    wav_file = voice_file.replace('.ogg', '.wav')

    await voice.download_to_drive(voice_file)
    logger.info(f"Downloaded voice file: {voice_file}")

    # 2. Convert OGG to WAV using ffmpeg
    conversion_result = subprocess.run(
        ['ffmpeg', '-y', '-i', voice_file, '-ar', '16000', '-ac', '1', wav_file],
        capture_output=True,
        text=True
    )

    if conversion_result.returncode != 0:
        logger.error(f"ffmpeg error: {conversion_result.stderr}")
        await update.message.reply_text("❌ Failed to process voice message")
        return

    # 3. Transcribe with Whisper API
    try:
        with open(wav_file, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language="en"  # Adjust as needed
            )

        transcribed_text = transcript['text']
        logger.info(f"Transcribed: {transcribed_text}")

        # Send transcription confirmation
        await update.message.reply_text(f"🎤 Heard: {transcribed_text}")

    except Exception as e:
        logger.error(f"Whisper API error: {e}")
        await update.message.reply_text("❌ Transcription failed")
        return
    finally:
        # Cleanup audio files
        Path(voice_file).unlink(missing_ok=True)
        Path(wav_file).unlink(missing_ok=True)

    # 4. Execute Claude command
    await execute_claude_command(update, context, transcribed_text)


async def handle_text(update: Update, context):
    """Handle text messages."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    text = update.message.text
    logger.info(f"Text message from user {user_id}: {text}")

    await execute_claude_command(update, context, text)


async def execute_claude_command(update: Update, context, prompt: str):
    """Execute Claude Code command and handle response."""
    user_id = update.effective_user.id

    # Get or create session ID
    session_id = context.user_data.get('claude_session_id')

    # Build Claude command
    claude_cmd = [
        'claude',
        '-p', prompt,
        '--output-format', 'stream-json',
        '--max-turns', '10'
    ]

    if session_id:
        claude_cmd.extend(['--resume', session_id])
        logger.info(f"Resuming session: {session_id}")

    # Send "working" message
    status_msg = await update.message.reply_text("⏳ Claude is working on this...")

    # Execute Claude Code
    try:
        result = subprocess.run(
            claude_cmd,
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR),
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            logger.error(f"Claude error: {error_msg}")
            await status_msg.edit_text(
                f"❌ Claude encountered an error:\n```\n{error_msg[:3000]}\n```",
                parse_mode='Markdown'
            )
            return

        # Parse output
        output = result.stdout.strip()

        # Try to extract session ID from output
        # (In real implementation, parse stream-json format properly)
        # For simplicity, store a placeholder
        if not session_id:
            context.user_data['claude_session_id'] = f"session_{user_id}_{datetime.now().timestamp()}"

        # Increment turn count for auto-compact
        turn_count = context.user_data.get('turn_count', 0) + 1
        context.user_data['turn_count'] = turn_count

        # Auto-compact every 20 turns
        if turn_count >= 20:
            logger.info("Auto-compacting session")
            subprocess.run(
                ['claude', '-p', '/compact', '--resume', context.user_data['claude_session_id']],
                cwd=str(WORKSPACE_DIR)
            )
            context.user_data['turn_count'] = 0

        # Create response with approval keyboard
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

        # Send response (truncate if too long)
        response_text = output[:3800] if len(output) > 3800 else output
        if len(output) > 3800:
            response_text += "\n\n...(truncated)"

        await status_msg.edit_text(
            f"🤖 Claude:\n{response_text}",
            reply_markup=reply_markup
        )

    except subprocess.TimeoutExpired:
        logger.error("Claude command timeout")
        await status_msg.edit_text(
            "⏱️ Claude took too long (>2 min). Task may still be running."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        await status_msg.edit_text(f"💥 Unexpected error: {str(e)}")


async def handle_callback(update: Update, context):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == 'approve':
        await query.edit_message_text("✅ Changes approved and applied!")
        # In real implementation, you might run additional git commands here

    elif action == 'reject':
        await query.edit_message_text("❌ Changes rejected")
        # In real implementation, you might run git reset or similar

    elif action == 'diff':
        # Show git diff
        diff_result = subprocess.run(
            ['git', 'diff'],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR)
        )
        diff_output = diff_result.stdout or "(No changes)"
        await query.message.reply_text(
            f"```diff\n{diff_output[:3800]}\n```",
            parse_mode='Markdown'
        )

    elif action == 'gitstatus':
        # Show git status
        status_result = subprocess.run(
            ['git', 'status'],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR)
        )
        status_output = status_result.stdout or "(No git repository)"
        await query.message.reply_text(
            f"```\n{status_output[:3800]}\n```",
            parse_mode='Markdown'
        )


async def handle_status(update: Update, context):
    """Handle /status command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    session_id = context.user_data.get('claude_session_id', 'No active session')
    turn_count = context.user_data.get('turn_count', 0)

    await update.message.reply_text(
        f"📊 Status:\n"
        f"Session ID: {session_id}\n"
        f"Turn count: {turn_count}\n"
        f"Workspace: {WORKSPACE_DIR}"
    )


async def handle_clear(update: Update, context):
    """Handle /clear command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Clear session data
    context.user_data['claude_session_id'] = None
    context.user_data['turn_count'] = 0

    await update.message.reply_text("🗑️ Conversation history cleared. Starting fresh!")


async def health_check(update: Update, context):
    """Health check endpoint for Docker healthcheck."""
    return {"status": "ok"}


def main():
    """Start the bot."""
    # Register handlers
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("status", handle_status))
    app.add_handler(CommandHandler("clear", handle_clear))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Create sessions directory
    Path('sessions').mkdir(exist_ok=True)

    logger.info(f"Starting bot with webhook: {WEBHOOK_URL}")

    # Run with webhook (for production on Coolify)
    app.run_webhook(
        listen="0.0.0.0",
        port=8443,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == '__main__':
    main()
```

**bot/requirements.txt:**
```txt
python-telegram-bot==21.9
deepgram-sdk==3.0.0
```

### 4.5 Deploying to Coolify

**Step-by-Step Instructions:**

1. **Create Git Repository:**
   ```bash
   cd claude-remote-runner
   git init
   git add .
   git commit -m "Initial commit"

   # Push to GitHub/GitLab/Gitea
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Add to Coolify:**
   - Log into Coolify web UI
   - Navigate to your project
   - Click "+ New Resource"
   - Select "Docker Compose"
   - **Source:** Choose "Git Repository"
   - **Repository URL:** `<your-repo-url>`
   - **Branch:** `main`
   - **Docker Compose Location:** `/docker-compose.yml` (root)
   - Click "Continue"

3. **Configure Environment Variables:**
   - In Coolify UI, go to "Environment Variables" section
   - Add each variable from `.env.example`:
     - `TELEGRAM_TOKEN` (mark as "Secret")
     - `DEEPGRAM_API_KEY` (mark as "Secret")
     - `WEBHOOK_URL` (value: `https://claude.yourdomain.com/${TELEGRAM_TOKEN}`)
     - `ALLOWED_USER_IDS` (optional, your Telegram user ID)
     - `BASIC_AUTH_USER` (optional)
     - `BASIC_AUTH_PASS` (optional, mark as "Secret")

4. **Configure Domains:**
   - In "Domains" section, add: `https://claude.yourdomain.com`
   - Coolify will automatically provision SSL certificate

5. **Configure Ports:**
   - In "Ports" section, set "Ports Exposed": `3000`
   - This exposes the claudebox-web service

6. **Deploy:**
   - Click "Deploy" button
   - Monitor deployment logs in real-time
   - Wait for "Application started successfully"
   - Verify services are healthy (green checkmark)

7. **Set Telegram Webhook:**
   ```bash
   # Replace <TOKEN> with your actual Telegram bot token
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
     -d "url=https://claude.yourdomain.com/<TOKEN>" \
     -d "allowed_updates=[\"message\",\"callback_query\"]"
   ```

8. **Verify Webhook:**
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
   ```

   Should return:
   ```json
   {
     "ok": true,
     "result": {
       "url": "https://claude.yourdomain.com/<TOKEN>",
       "has_custom_certificate": false,
       "pending_update_count": 0
     }
   }
   ```

9. **Test System:**
   - **Web UI:** Open `https://claude.yourdomain.com` in browser
   - **Telegram Bot:**
     - Open Telegram, find your bot
     - Send `/start` command
     - Send a voice message: "Check if the workspace directory is empty"
     - Verify bot responds with transcription and Claude's output

---

## 5. Usage Guide

### 5.1 Web UI Access

**Accessing the Terminal:**
1. Navigate to `https://claude.yourdomain.com`
2. Enter credentials if basic auth is enabled
3. Terminal interface loads automatically
4. Type Claude commands directly:
   ```bash
   claude -p "Create a Python hello world script"
   ```

**Features:**
- ✅ Full terminal emulation (xterm.js)
- ✅ Copy/paste support
- ✅ Command history (up/down arrows)
- ✅ Tab completion
- ✅ Works on mobile browsers

### 5.2 Voice Control via Telegram

**Basic Workflow:**

1. **Start Conversation:**
   - Open Telegram bot
   - Send `/start` to initialize

2. **Send Voice Command:**
   - Tap microphone icon
   - Speak your request clearly:
     - "Create a new Express server with authentication"
     - "Add unit tests for the user controller"
     - "Refactor the database connection logic"
   - Release to send

3. **Review Transcription:**
   - Bot replies with: "🎤 Heard: [your transcribed text]"
   - Verify accuracy

4. **Wait for Claude:**
   - Bot shows: "⏳ Claude is working on this..."
   - Typically 10-30 seconds

5. **Review Output:**
   - Bot shows Claude's response
   - Inline keyboard appears with options:
     - ✅ Approve - Apply changes
     - ❌ Reject - Discard changes
     - 📝 Show Diff - View git diff
     - 📊 Git Status - Check working tree status

6. **Approve or Reject:**
   - Tap ✅ to apply changes
   - Tap ❌ to reject
   - Tap 📝 to review changes before deciding

**Text Commands:**
You can also send text messages instead of voice:
```
Create a README.md file
```

**Session Management:**
- Sessions persist across messages
- Bot remembers conversation context
- Use `/clear` to start fresh session
- Use `/status` to check current session info

**Tips for Best Results:**
- Speak clearly and at moderate pace
- Minimize background noise
- Use specific, actionable requests
- Review transcription before approving
- Use `/clear` if Claude seems confused

### 5.3 Git Workflow Integration

**Committing Changes:**
After Claude makes changes and you approve:

1. **Check Status:**
   - Tap "📊 Git Status" button
   - Or use web terminal: `git status`

2. **Review Changes:**
   - Tap "📝 Show Diff" button
   - Or use web terminal: `git diff`

3. **Commit:**
   - Via voice: "Commit these changes with message 'Add authentication'"
   - Via web terminal:
     ```bash
     git add .
     git commit -m "Add authentication"
     ```

4. **Push (if configured):**
   - Via voice: "Push to origin main"
   - Via web terminal: `git push origin main`

**Setting Up Git Repository:**
```bash
# In web terminal (https://claude.yourdomain.com)
cd /workspace
git init
git remote add origin <your-repo-url>
git config user.name "Your Name"
git config user.email "your@email.com"
```

---

## 6. Monitoring & Maintenance

### 6.1 Coolify Built-in Monitoring

**Access Metrics:**
- Navigate to Coolify UI
- Select your application
- Click "Metrics" tab

**Available Metrics:**
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB)
- Disk usage (GB)
- Container restart count

**Logs:**
- Real-time container logs
- Filter by service (claudebox-web, telegram-bot)
- Download logs for offline analysis
- Retention: Last 1000 lines (configurable)

### 6.2 Cost Monitoring

**Monthly Cost Tracking:**
| Component | Provider | Estimated | Actual | Notes |
|-----------|----------|-----------|--------|-------|
| VPS | Hetzner | €9 | ___ | CPX21 plan |
| STT | Deepgram | $25.80 (100hrs) | ___ | Check Deepgram console |
| Claude | Anthropic | $20 | ___ | Pro subscription (fixed) |
| Domain | Registrar | $1 | ___ | Annual ÷ 12 |
| **Total** | | **~$36.30** | ___ | |

**Usage Tracking:**
- **Deepgram Console:** https://console.deepgram.com/
  - View transcription usage by day
  - Monitor credits and spending

- **Claude Code:** Use subscription (included in Pro/Max)
  - No additional API costs
  - Unlimited usage within fair use policy

**Cost Optimization Tips:**
1. Deepgram offers 28% savings vs Whisper ($25.80 vs $36 for 100hrs)
2. Implement voice message length limits
3. Use shorter voice messages when possible
4. Use `/compact` regularly to manage Claude session size

### 6.3 Backup Strategy

**Automated Backups:**

**Option A: Built-in Volume Backup (Recommended)**

Add backup service to `docker-compose.yml`:
```yaml
services:
  backup:
    image: offen/docker-volume-backup:latest
    container_name: claude-backup
    environment:
      - BACKUP_CRON_EXPRESSION=0 2 * * *  # Daily at 2 AM UTC
      - BACKUP_FILENAME=claude-backup-%Y%m%d.tar.gz
      - BACKUP_PRUNING_PREFIX=claude-backup-
      - BACKUP_RETENTION_DAYS=7
      - BACKUP_ARCHIVE=/archive
    volumes:
      - workspace:/backup/workspace:ro
      - claude-config:/backup/claude-config:ro
      - ./backups:/archive
    restart: unless-stopped
```

**Option B: Hetzner Volume Snapshots**
- Create Hetzner Volume
- Attach to server
- Mount at `/mnt/backups`
- Use as backup destination
- Schedule snapshots via Hetzner Cloud Console

**Manual Backup:**
```bash
# SSH into server
ssh root@<server-ip>

# Backup volumes
docker run --rm \
  -v claude-remote-runner_workspace:/source/workspace:ro \
  -v claude-remote-runner_claude-config:/source/config:ro \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/claude-backup-$(date +%Y%m%d).tar.gz /source

# Download backup
scp root@<server-ip>:~/claude-backup-*.tar.gz ./
```

**Restore from Backup:**
```bash
# Stop containers
docker compose down

# Restore volumes
docker run --rm \
  -v claude-remote-runner_workspace:/target/workspace \
  -v claude-remote-runner_claude-config:/target/config \
  -v $(pwd):/backup \
  alpine \
  tar xzf /backup/claude-backup-20260204.tar.gz -C /

# Restart containers
docker compose up -d
```

### 6.4 Troubleshooting

**Common Issues:**

**Issue 1: Telegram bot not responding**

Symptoms:
- Voice messages sent, no response
- /start command doesn't work

Diagnosis:
```bash
# Check bot container logs
docker logs telegram-bot

# Verify webhook is set
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Solutions:
- Verify `TELEGRAM_TOKEN` is correct in Coolify env vars
- Re-set webhook with correct URL
- Check firewall allows HTTPS traffic
- Verify container is running: `docker ps | grep telegram-bot`

**Issue 2: Voice transcription failing**

Symptoms:
- Bot acknowledges voice message but says "Transcription failed"

Diagnosis:
```bash
# Check bot logs for Deepgram API errors
docker logs telegram-bot | grep -i deepgram
```

Solutions:
- Verify `DEEPGRAM_API_KEY` is correct
- Check Deepgram account has sufficient credits
- Verify ffmpeg is installed: `docker exec telegram-bot ffmpeg -version`
- Test with shorter voice message (<10 seconds)

**Issue 3: Claude Code errors**

Symptoms:
- Bot says "Claude encountered an error"

Diagnosis:
```bash
# Check bot logs
docker logs telegram-bot | grep -i claude

# Test Claude directly in web terminal
# https://claude.yourdomain.com
claude --version
claude -p "Hello Claude"
```

Solutions:
- Verify Claude Pro/Max subscription is active
- Check that `claude login` was run on the server
- Verify ~/.claude/ directory is mounted correctly
- Check workspace directory is writable: `ls -la /workspace`
- Check Claude Code installation: `which claude`

**Issue 4: Web UI not accessible**

Symptoms:
- https://claude.yourdomain.com times out or shows 502 error

Diagnosis:
```bash
# Check claudebox-web container
docker ps | grep claudebox-web
docker logs claudebox-web

# Check Traefik routing
docker logs coolify-proxy
```

Solutions:
- Verify container is running: `docker restart claudebox-web`
- Check Coolify domain configuration (ensure `https://` prefix)
- Verify DNS A record points to server IP
- Wait for SSL certificate provisioning (can take 5-10 minutes)
- Check port 3000 is exposed in Coolify settings

**Issue 5: Session not persisting**

Symptoms:
- Claude doesn't remember previous commands
- Each message starts fresh conversation

Diagnosis:
```bash
# Check Claude config volume
docker volume inspect claude-remote-runner_claude-config

# Check session files
docker exec telegram-bot ls -la /root/.claude/projects/
```

Solutions:
- Verify `claude-config` volume is mounted correctly
- Check session ID is being stored: `/status` command in Telegram
- Ensure `--resume` flag is being used in bot code
- Check write permissions on volume

**Issue 6: High costs**

Symptoms:
- Deepgram bill higher than expected

Diagnosis:
```bash
# Check Deepgram usage: https://console.deepgram.com/
# Review bot logs for usage patterns
docker logs telegram-bot | grep -i transcribe | wc -l
```

Solutions:
- Implement rate limiting in bot (max N messages per day per user)
- Use shorter voice messages
- Implement voice message length limits (e.g., max 60 seconds)
- Monitor usage in Deepgram console regularly
- Set up billing alerts in Deepgram console

---

## 7. Security Considerations

### 7.1 Access Control

**Telegram Bot Authorization:**
- ✅ **Implement:** `ALLOWED_USER_IDS` environment variable
- ✅ **Best Practice:** Whitelist specific Telegram user IDs
- ❌ **Never:** Leave bot publicly accessible without auth

**Getting Your Telegram User ID:**
```bash
# Message @userinfobot on Telegram
# Or use this in your bot temporarily:
logger.info(f"User ID: {update.effective_user.id}")
```

**Web UI Authentication:**
- ✅ **Implement:** Basic auth via `BASIC_AUTH_USER` and `BASIC_AUTH_PASS`
- ✅ **Alternative:** Use Cloudflare Access or Authelia for more robust auth
- ⚠️ **Note:** Basic auth is sufficient for personal use, not for teams

### 7.2 API Key Security

**Best Practices:**
- ✅ Store in Coolify environment variables (encrypted at rest)
- ✅ Mark as "Secret" in Coolify UI (hidden in logs)
- ✅ Never commit to Git
- ✅ Rotate every 90 days
- ✅ Use separate keys for dev/prod environments

**Key Rotation Process:**
1. Generate new API key in provider console
2. Update Coolify environment variable
3. Restart application via Coolify UI
4. Verify new key works
5. Revoke old key in provider console

### 7.3 Network Security

**Firewall Configuration:**
```bash
# UFW rules (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

**Coolify Internal Network:**
- Services communicate via Docker network (isolated)
- Only exposed ports are accessible from internet
- Traefik handles all external traffic

**SSL/TLS:**
- Automatic via Let's Encrypt
- Certificates renew automatically
- HTTPS enforced for all traffic
- HSTS header enabled by Traefik

### 7.4 Rate Limiting

**Implement in Bot:**
```python
from datetime import datetime, timedelta
from collections import defaultdict

# Rate limiter: max 10 messages per minute per user
rate_limits = defaultdict(list)

async def check_rate_limit(user_id: int) -> bool:
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)

    # Remove old entries
    rate_limits[user_id] = [
        timestamp for timestamp in rate_limits[user_id]
        if timestamp > minute_ago
    ]

    # Check limit
    if len(rate_limits[user_id]) >= 10:
        return False

    # Add new entry
    rate_limits[user_id].append(now)
    return True

# In handler:
if not await check_rate_limit(user_id):
    await update.message.reply_text("⏱️ Too many requests. Please wait a minute.")
    return
```

### 7.5 Data Privacy

**Voice Data:**
- Voice files stored temporarily in `sessions/` directory
- Deleted immediately after transcription
- Not persisted to disk beyond processing

**Conversation History:**
- Stored in Claude's session files (`~/.claude/projects/`)
- Only accessible to authenticated users
- Can be cleared with `/clear` command

**Logs:**
- Coolify logs may contain user messages
- Rotate logs regularly
- Consider log sanitization for sensitive data

---

## 8. Scaling & Performance

### 8.1 Vertical Scaling

**When to Upgrade VPS:**
- CPU usage consistently >70%
- Memory usage >85%
- Response times >5 seconds
- Multiple concurrent users

**Upgrade Path:**
| Current | Upgrade To | Cost Increase | Capacity Increase |
|---------|-----------|---------------|-------------------|
| CPX21 (3 vCPU, 8GB) | CPX31 (4 vCPU, 8GB) | +€4/mo | +33% CPU |
| CPX21 (3 vCPU, 8GB) | CPX41 (8 vCPU, 16GB) | +€16/mo | +167% CPU, +100% RAM |

**How to Upgrade:**
1. Create snapshot in Hetzner console (backup)
2. Resize server to larger plan
3. Wait for resize completion (5-10 minutes)
4. Verify all services restart correctly
5. Test functionality

### 8.2 Horizontal Scaling

**Multi-Instance Setup:**

For team usage, deploy multiple instances:

**Architecture:**
```
Hetzner Load Balancer
├── Instance 1: User A's sessions
├── Instance 2: User B's sessions
└── Instance 3: User C's sessions
```

**Implementation:**
1. Deploy multiple copies of the stack via Coolify
2. Configure Hetzner Load Balancer
3. Use sticky sessions (session affinity)
4. Share workspace via Hetzner Volume (mounted on all instances)

**Session Affinity:**
- Route user to same instance based on Telegram user ID
- Prevents session conflicts
- Configure in Hetzner Load Balancer settings

### 8.3 Performance Optimization

**Claude Code:**
- Use `--max-turns` to limit context growth
- Implement `/compact` every 20 turns
- Use shorter, more specific prompts

**Deepgram API:**
- Use Nova-3 model for best accuracy and speed
- Implement max voice message length (e.g., 60 seconds)
- Monitor usage to stay within budget

**Docker:**
- Use multi-stage builds to reduce image sizes
- Enable BuildKit for faster builds
- Prune unused images/volumes regularly:
  ```bash
  docker system prune -a --volumes
  ```

---

## 9. Future Enhancements

### 9.1 Roadmap

**Phase 1: Core Functionality (Week 1-2)** ✅
- [x] Basic infrastructure setup
- [x] Telegram bot with voice support
- [x] Claude Code integration
- [x] Session persistence

**Phase 2: Enhanced UX (Week 3-4)**
- [ ] Add CloudCLI web UI (file explorer, git UI)
- [ ] Implement rich inline keyboards
- [ ] Add voice message length indicator
- [ ] Implement typing indicators during processing

**Phase 3: Advanced Features (Month 2)**
- [ ] Multi-project support
- [ ] Scheduled tasks (cron-like via Telegram)
- [ ] Code review workflow
- [ ] PR creation from voice commands

**Phase 4: Team Features (Month 3)**
- [ ] Multi-user support
- [ ] Role-based access control
- [ ] Usage analytics dashboard
- [ ] Cost allocation per user

### 9.2 Potential Integrations

**CI/CD Pipelines:**
- Trigger builds via voice command
- Receive build status notifications in Telegram
- Integration with GitHub Actions, GitLab CI

**Project Management:**
- Create Jira/Linear issues from voice
- Update task status
- Query project status

**Code Quality:**
- Run linters/formatters via voice
- Automated code reviews
- Security scanning integration

**Notifications:**
- Deployment completion alerts
- Error monitoring (Sentry integration)
- Uptime monitoring (UptimeRobot webhook)

### 9.3 Alternative Implementations

**MCP Server Approach:**
- Implement Claude Code as MCP server
- Expose tools via Model Context Protocol
- Allows integration with other AI clients

**API-First Design:**
- Expose REST API for Claude Code operations
- Build multiple clients (Telegram, Discord, Slack, web UI)
- Centralized session management

**Desktop App:**
- Electron wrapper around web UI
- Native notifications
- System tray integration
- Offline mode with local Whisper

---

## 10. Conclusion

This deployment design provides a complete, production-ready solution for running Claude Code remotely with voice control. The architecture leverages mature, well-supported technologies:

- ✅ **Coolify** simplifies deployment and SSL management
- ✅ **Telegram** provides excellent mobile UX for voice interaction
- ✅ **Deepgram API** offers accurate and cost-effective transcription
- ✅ **Docker Compose** ensures reproducible deployments
- ✅ **Hetzner** provides cost-effective infrastructure

**Total Investment:**
- Setup Time: 8-10 hours
- Monthly Cost: €9 + $25.80 + $20 = $36.30/month
- Maintenance: <2 hours/month

**Key Benefits:**
- 🎤 Voice control from anywhere (mobile-first)
- 💻 Web terminal for advanced operations
- 📱 Mobile-friendly responsive design
- 🔒 Secure by default (HTTPS, auth, firewall)
- 💾 Persistent sessions and context
- 📊 Built-in monitoring and logging
- 🔄 Easy backups and disaster recovery

**Next Steps:**
1. Provision Hetzner VPS
2. Install Coolify
3. Clone this repository
4. Configure environment variables
5. Deploy to Coolify
6. Set Telegram webhook
7. Test and iterate

**Support & Resources:**
- Comprehensive research: `docs/comprehensive_research.md`
- GitHub repository: `<your-repo-url>`
- Coolify docs: https://coolify.io/docs/
- Telegram Bot API: https://core.telegram.org/bots/api

---

**Document Version:** 1.0
**Last Updated:** February 4, 2026
**Status:** Ready for Implementation
