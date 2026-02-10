# Project Structure

## Overview
```
claude-remote-runner/
├── bot/                          # Telegram bot application
├── docs/                         # Documentation
├── Configuration files           # Docker, environment, etc.
└── Documentation files           # README, guides
```

## Detailed Structure

### Bot Application (`/bot`)
```
bot/
├── bot.py                        # Main bot (1500+ lines)
├── callback_handlers.py          # Button click handlers (600+ lines)
├── claude_executor.py            # Claude Code execution (400+ lines)
├── config.py                     # Configuration management
├── error_handlers.py             # Error handling utilities
├── formatters.py                 # Response formatting
├── git_operations.py             # Git integration (400+ lines)
├── keyboards.py                  # Inline keyboard layouts
├── logging_config.py             # Logging setup
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Production image definition
├── test_*.py                     # Test suites (10 files)
└── logs/                         # Log files (auto-created)
```

### Documentation (`/docs`)
```
docs/
├── design.md                     # System architecture
├── implementation_plan.md        # 28-step roadmap
├── comprehensive_research.md     # Technology research
└── implementation/               # Step-by-step guides (28 files)
    ├── step_08_session_state.md
    ├── step_09_claude_execution.md
    ├── ...
    └── step_28_final_testing.md
```

### Configuration Files
```
├── docker-compose.yml            # Service orchestration
├── .env.example                  # Environment template
├── .gitignore                    # Git exclusions
├── .dockerignore                 # Docker build exclusions
```

### Documentation Files
```
├── README.md                     # Main project documentation
├── CONTRIBUTING.md               # Contribution guidelines
├── COOLIFY_DEPLOY.md            # Deployment guide
├── LICENSE                       # MIT license
└── PROJECT_STRUCTURE.md         # This file
```

## Key Files Explained

### Core Bot Files

**bot.py** (1500+ lines)
- Main application entry point
- Command handlers: /start, /help, /status, /clear, etc.
- Voice message handling with Deepgram transcription
- Text message handling
- Session management
- Bot initialization and configuration

**callback_handlers.py** (600+ lines)
- Handles inline button clicks
- Approval workflow (approve/reject)
- Git operations (diff, status, log)
- Session management callbacks
- Clear confirmation dialogs

**claude_executor.py** (400+ lines)
- Executes Claude Code in headless mode
- Session management
- Output parsing
- Error handling
- Cost tracking

**git_operations.py** (400+ lines)
- Git repository initialization
- Status checking
- Diff generation
- Commit creation
- Branch management
- Log retrieval

### Supporting Modules

**keyboards.py**
- Inline keyboard layouts
- Main actions (Approve/Reject/Retry)
- Git actions (Diff/Status/Log)
- Session management buttons
- Pagination controls

**formatters.py**
- Message formatting for Telegram
- Code block handling
- Length-based splitting
- Markdown formatting

**error_handlers.py**
- Exception handling
- Error logging
- User-friendly error messages

**logging_config.py**
- Structured logging setup
- File rotation
- Context logging (user_id, handler)
- Access logging

### Test Files (10 files)
- test_keyboards.py - Keyboard layout tests
- test_approval_workflow.py - Approval flow tests
- test_command_helpers.py - Command tests
- test_formatters.py - Formatting tests
- test_logging_config.py - Logging tests
- test_error_handlers.py - Error handling tests
- test_claude_executor.py - Claude execution tests
- test_session_management.py - Session tests
- test_integration.py - Integration tests
- test_e2e.py - End-to-end tests

## Docker Services

### telegram-bot
- Python 3.11 slim base
- Bot application
- Claude Code CLI
- Voice processing (ffmpeg)
- Git operations

### claudebox-web
- Web terminal UI
- Port 3000
- Shared workspace with bot
- Basic authentication

## Volumes

### workspace
- Shared coding workspace
- Persistent across restarts
- Accessible from both services

### claude-config
- Claude Code configuration
- API keys and settings
- Shared between services

### sessions
- Bot session data
- User conversations
- PicklePersistence storage

## Environment Variables

### Required
- ANTHROPIC_API_KEY - Claude API access
- TELEGRAM_TOKEN - Bot authentication
- DEEPGRAM_API_KEY - Voice transcription

### Optional
- WEBHOOK_URL - Production webhook
- ALLOWED_USER_IDS - Access control
- BASIC_AUTH_USER/PASS - Web UI auth
- BOT_MODE - polling/webhook

## File Counts

- Python source: 10 files (~4000 lines)
- Tests: 10 files (~1500 lines)
- Documentation: 30+ files
- Total project: ~6000 lines of code

## Implementation Status

### ✅ Completed (Steps 8-18)
- Core bot functionality
- Voice transcription
- Claude Code integration
- Approval workflow
- Git operations
- Command system
- Deployment configuration

### ⏸️ Postponed
- Step 21: Monitoring
- Step 22: Backups

### 📋 Remaining Optional
- Step 19: Production deploy
- Step 20: Webhook setup
- Step 23: Performance optimization
- Step 24: Security hardening
- Steps 25-28: Documentation/testing

---

**Last Updated:** February 7, 2026
**Version:** 1.0.0
**Status:** Production-ready, deployment-ready
