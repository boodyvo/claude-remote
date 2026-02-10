# Claude Remote Runner - Voice-Controlled Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

Remote Claude Code execution with voice control via Telegram bot, featuring persistent sessions, web UI access, and comprehensive approval workflows.

## 🎯 Features

- **🎤 Voice Control**: Send voice messages via Telegram, transcribed with Deepgram Nova-3
- **💬 Text Commands**: Full support for text-based interactions
- **🤖 Claude Code Integration**: Execute coding tasks via Claude Code headless mode
- **📱 Mobile-First**: Optimized for mobile Telegram app usage
- **💻 Web UI**: Browser-based file manager for workspace access
- **💾 Persistent Sessions**: Conversation history maintained across restarts
- **✅ Approval Workflow**: Review and approve/reject changes before applying
- **📝 Git Integration**: View diffs, check status, commit changes
- **📁 File Browser**: Web-based file management with syntax highlighting
- **🔒 Secure**: HTTPS via Let's Encrypt, user authorization, API key encryption

## 📋 Prerequisites

### Required Services
- **Hetzner VPS** (or similar) - CPX21 (3 vCPU, 8GB RAM) recommended
- **Coolify** - Self-hosted PaaS (installation instructions below)
- **Domain Name** - For HTTPS access (e.g., claude.yourdomain.com)

### Required API Keys
- **Anthropic API Key** - For Claude Code ([Get it here](https://console.anthropic.com/))
- **Deepgram API Key** - For voice transcription ([Get it here](https://deepgram.com/))
- **Telegram Bot Token** - Created via @BotFather ([Instructions](https://core.telegram.org/bots/tutorial))

### Costs
- Infrastructure: €9/month (Hetzner CPX21)
- Deepgram API: ~$25.80/month (100 hours transcription)
- Claude API: $20-50/month (varies with usage)
- **Total: ~$55-85/month**

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/claude-remote-runner.git
cd claude-remote-runner
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
nano .env  # Edit with your API keys
```

Required variables:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
TELEGRAM_TOKEN=1234567890:ABC...
DEEPGRAM_API_KEY=...
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}
ALLOWED_USER_IDS=123456789  # Your Telegram user ID
```

### 3. Local Testing (Optional)

```bash
# Test with Docker Compose locally
docker-compose up -d

# Check logs
docker-compose logs -f telegram-bot

# Access web UI
open http://localhost:3000
```

### 4. Deploy to Coolify

See [Deployment Guide](#-deployment-to-coolify) below for detailed instructions.

## 📖 Usage

### Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and instructions |
| `/help` | Display comprehensive help |
| `/status` | Show current session status with approval history |
| `/clear` | Clear conversation history (with pending change warning) |
| `/info` | Show system diagnostics |
| `/compact` | Compress session context (save tokens) |
| `/workspace` | Show workspace file tree |
| `/gitinit` | Initialize git repository |
| `/gitstatus` | Show repository status |
| `/gitdiff` | Show diff of changes |
| `/commit [msg]` | Commit changes |
| `/gitlog` | Show commit history |
| `/sessions` | List all your sessions |
| `/sessioninfo` | Show active session details |
| `/newsession` | Start a new session |
| `/cleansessions` | Delete old sessions (>30 days) |

### Voice Workflow

1. **Send Voice Message** - Tap microphone, speak your request
2. **Review Transcription** - Bot shows what it heard
3. **Wait for Claude** - Processing typically takes 10-30 seconds
4. **Review Changes** - Claude's response with inline buttons
5. **Approve/Reject** - Use buttons to apply or discard changes

### Example Requests

**Voice:**
- "Create a Python script that reads CSV files"
- "Add unit tests for the authentication module"
- "Refactor the database connection to use connection pooling"

**Text:**
- `Fix the bug in login.py where passwords aren't hashed`
- `Create a REST API endpoint for user registration`
- `Add TypeScript types to the entire codebase`

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Coolify Platform                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Traefik Reverse Proxy                    │  │
│  │         (Auto SSL via Let's Encrypt)                  │  │
│  └─────────────┬──────────────────┬──────────────────────┘  │
│                │                  │                          │
│     ┌──────────▼────────┐  ┌──────▼──────────┐             │
│     │  claudebox-web    │  │  telegram-bot   │             │
│     │  (Web Terminal)   │  │  (Voice Control)│             │
│     └───────────────────┘  └─────────────────┘             │
│                                                              │
│     Volumes: workspace, claude-config, bot-sessions         │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Deployment to Coolify

### Prerequisites

#### 1. Provision Hetzner VPS

```bash
# Create CPX21 server via Hetzner Cloud Console
# - OS: Ubuntu 24.04 LTS
# - Location: Nuremberg (nbg1)
# - Add your SSH key
```

#### 2. Install Coolify

```bash
# SSH to your server
ssh root@your-server-ip

# Install Coolify
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash

# Access Coolify UI
open http://your-server-ip:8000
```

#### 3. Configure Domain

Add DNS A record:
```
Type: A
Name: claude (or your subdomain)
Value: your-server-ip
TTL: 300
```

Verify: `dig claude.yourdomain.com`

### Deployment Steps

#### 1. Add Project to Coolify

1. Log into Coolify web UI
2. Navigate to your project or create new one
3. Click "+ New Resource"
4. Select "Docker Compose"
5. Choose "Git Repository"

#### 2. Configure Repository

- **Repository URL**: `https://github.com/yourusername/claude-remote-runner.git`
- **Branch**: `main`
- **Docker Compose Location**: `/docker-compose.yml`
- Click "Continue"

#### 3. Set Environment Variables

In Coolify UI, add each variable (mark secrets as "Secret"):

```env
ANTHROPIC_API_KEY=sk-ant-api03-...        # Secret ✓
TELEGRAM_TOKEN=1234567890:ABC...          # Secret ✓
DEEPGRAM_API_KEY=...                      # Secret ✓
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}
ALLOWED_USER_IDS=123456789
BASIC_AUTH_USER=admin                     # Optional
BASIC_AUTH_PASS=securepassword            # Optional, Secret ✓
```

#### 4. Configure Domain

- Go to "Domains" section
- Add: `https://claude.yourdomain.com`
- Coolify will automatically provision SSL certificate

#### 5. Deploy

1. Click "Deploy" button
2. Monitor deployment logs
3. Wait for "Application started successfully"
4. Verify all services healthy (green checkmarks)

#### 6. Set Telegram Webhook

```bash
# Replace <TOKEN> with your actual Telegram bot token
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://claude.yourdomain.com/<TOKEN>" \
  -d "allowed_updates=[\"message\",\"callback_query\"]"

# Verify webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

#### 7. Test System

**Web UI:**
```bash
open https://claude.yourdomain.com
# Should show terminal interface
```

**Telegram Bot:**
1. Open Telegram, find your bot
2. Send `/start` command
3. Send voice message: "Check if workspace is empty"
4. Verify transcription and response

## 📁 Project Structure

```
claude-remote-runner/
├── docker-compose.yml          # Docker services configuration
├── .env                        # Environment variables (git-ignored)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── README.md                   # This file
├── LICENSE                     # MIT license
├── bot/
│   ├── bot.py                  # Main bot application
│   ├── callback_handlers.py   # Inline button handlers
│   ├── keyboards.py            # Keyboard layouts
│   ├── formatters.py           # Response formatting
│   ├── git_operations.py       # Git integration
│   ├── claude_executor.py      # Claude Code execution
│   ├── logging_config.py       # Logging setup
│   ├── error_handlers.py       # Error handling
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── test_*.py               # Test suites
│   └── Dockerfile              # Bot container image
├── workspace/                  # Claude Code workspace (volume mount)
│   └── .gitkeep
└── docs/
    ├── design.md               # Architecture design
    ├── implementation_plan.md  # Implementation roadmap
    └── implementation/         # Step-by-step guides
        ├── step_01_*.md
        └── ...
```

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check container logs
docker logs telegram-bot

# Verify webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Restart container
docker restart telegram-bot
```

### Voice Transcription Failing

- Verify Deepgram API key has credits
- Check ffmpeg installed: `docker exec telegram-bot ffmpeg -version`
- Review logs: `docker logs telegram-bot | grep -i deepgram`

### Web UI Not Accessible

- Verify DNS A record points to server
- Check SSL certificate: `curl -I https://claude.yourdomain.com`
- Review Traefik logs: `docker logs coolify-proxy`

### Session Not Persisting

- Check volume mounts: `docker inspect telegram-bot | grep Mounts`
- Verify sessions directory: `docker exec telegram-bot ls /app/sessions`
- Check disk space: `df -h`

## 🔒 Security

### Best Practices

- ✅ User authorization via `ALLOWED_USER_IDS`
- ✅ API keys stored as Coolify secrets (encrypted at rest)
- ✅ HTTPS enforced via Let's Encrypt
- ✅ Firewall configured (ports 22, 80, 443 only)
- ✅ Voice files deleted immediately after transcription
- ✅ No credentials committed to git

### Rotate API Keys

Rotate every 90 days:

1. Generate new key in provider console
2. Update in Coolify environment variables
3. Restart application
4. Verify functionality
5. Revoke old key

## 🚦 Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r bot/requirements.txt

# Run locally (polling mode)
cd bot
python bot.py
```

### Running Tests

```bash
# Run all tests
docker exec telegram-bot python3 /app/test_keyboards.py
docker exec telegram-bot python3 /app/test_approval_workflow.py
docker exec telegram-bot python3 /app/test_command_helpers.py
```

## 📝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [koogle/claudebox](https://github.com/koogle/claudebox) - Web terminal for Claude Code
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram bot framework
- [Coolify](https://coolify.io/) - Self-hosted PaaS platform
- [Deepgram](https://deepgram.com/) - Speech-to-text API
- [Anthropic Claude](https://www.anthropic.com/claude) - AI assistant

## 📞 Support

- **Documentation**: See `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/claude-remote-runner/issues)

## 🗺️ Roadmap

- [x] Basic voice transcription
- [x] Claude Code integration
- [x] Approval workflow
- [x] Git integration
- [x] Command helpers
- [ ] Production deployment
- [ ] Multi-user support
- [ ] Advanced analytics
- [ ] Cost tracking dashboard

---

**Version**: 1.0.0
**Last Updated**: February 6, 2026
**Status**: Ready for Production Deployment
