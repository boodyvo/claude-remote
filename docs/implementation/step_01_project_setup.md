# Step 1: Project Setup & Repository Initialization

**Estimated Time:** 30 minutes
**Prerequisites:**
- Git installed
- Text editor or IDE
- Terminal access
**Deliverable:** Clean Git repository with proper structure, .gitignore, and initial documentation

## Overview

This step establishes the foundational structure for the claude-remote-runner project. We'll create a well-organized repository that follows best practices for Python projects, Docker deployments, and documentation. This structure will support all subsequent development steps and make the project maintainable and scalable.

The goal is to have a clean slate where you can commit changes incrementally, track progress, and easily rollback if needed. Proper organization from the start prevents technical debt and makes collaboration easier.

## Implementation Details

### What to Build

1. **Git Repository:** Initialize version control and configure proper .gitignore
2. **Directory Structure:** Create organized folders for code, docs, configs, and data
3. **Documentation:** Set up README and documentation structure
4. **Environment Template:** Create .env.example for configuration
5. **Initial Files:** Add LICENSE, .gitignore, README.md

### How to Implement

#### Step 1.1: Navigate to Project Directory

```bash
cd /Users/vlad/WebstormProjects/claude-remote-runner
```

You should already be in this directory since the design documents exist here.

#### Step 1.2: Initialize Git Repository (if not already done)

```bash
# Check if git is already initialized
git status

# If not initialized, run:
git init

# Configure git (if not already configured globally)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

#### Step 1.3: Create Directory Structure

```bash
# Create main directories
mkdir -p bot
mkdir -p workspace
mkdir -p sessions
mkdir -p backups
mkdir -p docs/implementation

# Verify structure
tree -L 2 -a
```

#### Step 1.4: Create .gitignore File

```bash
# Create .gitignore with comprehensive ignore patterns
cat > .gitignore << 'EOF'
# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
venv/
ENV/
env/
.venv

# PyCharm
.idea/

# VSCode
.vscode/

# Jupyter Notebook
.ipynb_checkpoints

# Sessions and data (runtime generated)
sessions/*.pkl
sessions/*.ogg
sessions/*.wav
sessions/*.mp3
sessions/voice_*

# Backups (large files)
backups/*.tar.gz
backups/*.zip

# Workspace (user projects, should not be in git)
workspace/*
!workspace/.gitkeep

# Docker
*.log
*.pid
*.seed
*.pid.lock

# OS
.DS_Store
Thumbs.db
*~

# Temporary files
tmp/
temp/
*.tmp
EOF
```

#### Step 1.5: Create .env.example Template

```bash
cat > .env.example << 'EOF'
# Anthropic API Key (required)
# Obtain from: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Telegram Bot Configuration (required)
# Create bot via @BotFather: https://t.me/botfather
TELEGRAM_TOKEN=1234567890:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Webhook URL (required for production)
# Format: https://your-domain.com/${TELEGRAM_TOKEN}
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}

# OpenAI API Key for Whisper transcription (required)
# Obtain from: https://platform.openai.com/api-keys
DEEPGRAM_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Allowed Telegram User IDs (comma-separated, optional but recommended)
# Get your ID from @userinfobot on Telegram
ALLOWED_USER_IDS=123456789,987654321

# Basic Auth for Web UI (optional)
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your-secure-password-here

# Port Configuration (optional, defaults shown)
WEB_PORT=3000
BOT_PORT=8443
EOF
```

#### Step 1.6: Create Keep Files for Empty Directories

```bash
# These ensure empty directories are tracked in git
touch workspace/.gitkeep
touch sessions/.gitkeep
touch backups/.gitkeep
```

#### Step 1.7: Create README.md

```bash
cat > README.md << 'EOF'
# Claude Remote Runner

Remote Claude Code execution with voice control via Telegram bot.

## Overview

This project enables you to run Claude Code remotely on a Coolify-hosted server with voice command capabilities through a Telegram bot. Speak your coding tasks, and Claude executes them on your server with full context preservation.

## Features

- 🎤 **Voice Control:** Send voice messages via Telegram, transcribed using Deepgram API
- 💻 **Web Terminal:** Access Claude Code via web browser (koogle/claudebox)
- 🔄 **Session Persistence:** Conversations maintain context across messages
- ✅ **Approval Workflow:** Review and approve changes before execution
- 🔍 **Git Integration:** View diffs, check status, approve commits
- 📱 **Mobile-First:** Optimized for mobile Telegram app
- 🔒 **Secure:** User authentication, HTTPS, secrets management

## Quick Start

### Prerequisites

- Hetzner VPS with Coolify installed
- Domain name with DNS configured
- Telegram account
- API keys (Anthropic, OpenAI, Telegram)

### Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd claude-remote-runner
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your API keys

4. Deploy to Coolify (see [Deployment Guide](docs/deployment.md))

## Architecture

- **Platform:** Coolify (self-hosted PaaS)
- **Infrastructure:** Hetzner CPX21 (3 vCPU, 8GB RAM)
- **Container:** koogle/claudebox for web access
- **Bot:** Python + python-telegram-bot framework
- **STT:** Deepgram API
- **Cost:** ~$36.30/month (VPS + APIs)

## Documentation

- [Design Document](docs/design.md) - Complete system architecture
- [Research](docs/comprehensive_research.md) - Technology evaluation
- [Implementation Plan](docs/implementation_plan.md) - Step-by-step guide
- [Implementation Steps](docs/implementation/) - Detailed step docs

## Usage

### Via Telegram Bot

1. Start conversation: `/start`
2. Send voice message with your request
3. Bot transcribes and executes via Claude
4. Review output and approve/reject changes
5. Use inline buttons for git operations

### Via Web UI

1. Navigate to `https://claude.yourdomain.com`
2. Log in (if basic auth enabled)
3. Use terminal to run Claude commands directly

## Commands

- `/start` - Initialize bot and show welcome
- `/status` - Check current session info
- `/clear` - Clear conversation history
- `/help` - Show available commands

## Development

See [Implementation Plan](docs/implementation_plan.md) for detailed development steps.

### Local Testing

```bash
# Install dependencies
cd bot
pip install -r requirements.txt

# Run bot locally (polling mode)
python bot.py
```

## Contributing

This is a personal project. Feel free to fork and adapt to your needs.

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- Check [Troubleshooting Guide](docs/troubleshooting.md)
- Review [Implementation Steps](docs/implementation/)
- Consult [Coolify Docs](https://coolify.io/docs/)

## Cost Breakdown

| Component | Cost |
|-----------|------|
| Hetzner CPX21 VPS | €9/month |
| Deepgram API | $25.80/100hrs |
| Claude API | $20-50/month (estimated) |
| Domain | ~$1/month |
| **Total** | **$36.30/month** |

## Acknowledgments

- [Coolify](https://coolify.io/) - Self-hosted PaaS
- [koogle/claudebox](https://github.com/koogle/claudebox) - Web terminal
- [python-telegram-bot](https://docs.python-telegram-bot.org/) - Bot framework
- [Deepgram](https://platform.openai.com/docs/guides/speech-to-text) - Speech-to-text

---

**Status:** In Development
**Version:** 1.0.0
**Last Updated:** February 4, 2026
EOF
```

#### Step 1.8: Create LICENSE File

```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 claude-remote-runner

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

#### Step 1.9: Create Initial Git Commit

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "Initial project setup

- Add directory structure (bot/, docs/, workspace/, sessions/, backups/)
- Add .gitignore for Python, Docker, OS files
- Add .env.example with all required variables
- Add README.md with project overview
- Add MIT LICENSE
- Add .gitkeep files for empty directories

This establishes the foundation for the claude-remote-runner project."

# Verify commit
git log --oneline
git status
```

### Code Examples

No code examples needed for this step - all commands are shown above.

### Project Structure

After completing this step, your directory structure should look like:

```
claude-remote-runner/
├── .git/                           # Git repository metadata
├── .gitignore                      # Git ignore rules
├── .env.example                    # Environment variable template
├── LICENSE                         # MIT license
├── README.md                       # Project documentation
├── bot/                            # Telegram bot code (empty for now)
├── workspace/                      # Project files workspace
│   └── .gitkeep                    # Keep empty dir in git
├── sessions/                       # Bot session data (runtime)
│   └── .gitkeep
├── backups/                        # Backup storage (runtime)
│   └── .gitkeep
└── docs/                           # Documentation
    ├── design.md                   # System architecture
    ├── comprehensive_research.md   # Technology research
    ├── implementation_plan.md      # High-level plan
    └── implementation/             # Detailed step docs
        ├── step_01_project_setup.md (this file)
        └── ... (steps 2-28)
```

## Testing & Validation

### Test Cases

**Test 1: Git Repository Initialized**
```bash
git status
# Expected: On branch main (or master), nothing to commit, working tree clean
```

**Test 2: Directory Structure Created**
```bash
ls -la
# Expected: All directories present (bot, workspace, sessions, backups, docs)
```

**Test 3: .gitignore Working**
```bash
# Create test file that should be ignored
echo "test" > .env
git status
# Expected: .env should NOT appear in untracked files

# Clean up
rm .env
```

**Test 4: README Renders Correctly**
```bash
# View in terminal
cat README.md

# Or preview in IDE/GitHub
```

**Test 5: .env.example Is Valid**
```bash
cat .env.example
# Expected: All required variables present with placeholder values
```

### Acceptance Criteria

- [ ] Git repository initialized (`.git/` directory exists)
- [ ] All required directories created (`bot/`, `workspace/`, `sessions/`, `backups/`, `docs/`)
- [ ] `.gitignore` file prevents committing sensitive files (`.env`, `__pycache__`, etc.)
- [ ] `.env.example` contains all required environment variables with descriptions
- [ ] README.md provides clear project overview and quick start instructions
- [ ] LICENSE file exists (MIT)
- [ ] `.gitkeep` files in empty directories
- [ ] Initial commit created with meaningful message
- [ ] `git status` shows clean working tree
- [ ] Directory structure matches specification

### How to Test

Run this validation script:

```bash
#!/bin/bash
# validate_step1.sh

echo "Validating Step 1: Project Setup..."

# Check git initialized
if [ -d .git ]; then
    echo "✓ Git repository initialized"
else
    echo "✗ Git repository NOT initialized"
    exit 1
fi

# Check directories exist
for dir in bot workspace sessions backups docs/implementation; do
    if [ -d "$dir" ]; then
        echo "✓ Directory exists: $dir"
    else
        echo "✗ Directory missing: $dir"
        exit 1
    fi
done

# Check files exist
for file in .gitignore .env.example README.md LICENSE; do
    if [ -f "$file" ]; then
        echo "✓ File exists: $file"
    else
        echo "✗ File missing: $file"
        exit 1
    fi
done

# Check .gitignore has key entries
if grep -q "\.env" .gitignore && grep -q "__pycache__" .gitignore; then
    echo "✓ .gitignore contains key patterns"
else
    echo "✗ .gitignore missing key patterns"
    exit 1
fi

# Check .env.example has required vars
required_vars=("ANTHROPIC_API_KEY" "TELEGRAM_TOKEN" "DEEPGRAM_API_KEY")
for var in "${required_vars[@]}"; do
    if grep -q "$var" .env.example; then
        echo "✓ .env.example contains: $var"
    else
        echo "✗ .env.example missing: $var"
        exit 1
    fi
done

# Check git has commits
if [ $(git rev-list --count HEAD 2>/dev/null || echo 0) -gt 0 ]; then
    echo "✓ Initial commit created"
else
    echo "✗ No commits found"
    exit 1
fi

# Check working tree is clean
if [ -z "$(git status --porcelain)" ]; then
    echo "✓ Working tree is clean"
else
    echo "✗ Working tree has uncommitted changes"
    git status --short
fi

echo ""
echo "✓ Step 1 validation PASSED"
echo "Ready to proceed to Step 2: Obtain API Keys & Credentials"
```

Run with:
```bash
chmod +x validate_step1.sh
./validate_step1.sh
```

Expected output:
```
Validating Step 1: Project Setup...
✓ Git repository initialized
✓ Directory exists: bot
✓ Directory exists: workspace
✓ Directory exists: sessions
✓ Directory exists: backups
✓ Directory exists: docs/implementation
✓ File exists: .gitignore
✓ File exists: .env.example
✓ File exists: README.md
✓ File exists: LICENSE
✓ .gitignore contains key patterns
✓ .env.example contains: ANTHROPIC_API_KEY
✓ .env.example contains: TELEGRAM_TOKEN
✓ .env.example contains: DEEPGRAM_API_KEY
✓ Initial commit created
✓ Working tree is clean

✓ Step 1 validation PASSED
Ready to proceed to Step 2: Obtain API Keys & Credentials
```

## Troubleshooting

### Issue 1: Git Not Installed

**Symptoms:**
```
bash: git: command not found
```

**Solution:**
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install git

# Verify installation
git --version
```

### Issue 2: Permission Denied When Creating Directories

**Symptoms:**
```
mkdir: cannot create directory 'bot': Permission denied
```

**Solution:**
```bash
# Check current directory permissions
ls -la

# Ensure you're in the right directory
pwd

# If in system directory, navigate to home or workspace
cd /Users/vlad/WebstormProjects/claude-remote-runner

# Or use sudo (not recommended for project files)
```

### Issue 3: Git Username/Email Not Configured

**Symptoms:**
```
*** Please tell me who you are.

Run

  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
```

**Solution:**
```bash
git config --global user.email "your.email@example.com"
git config --global user.name "Your Name"

# Verify
git config --global --list
```

### Issue 4: .env File Accidentally Committed

**Symptoms:**
```
git status shows .env in staged or committed files
```

**Solution:**
```bash
# If staged but not committed
git reset HEAD .env

# If already committed
git rm --cached .env
git commit -m "Remove .env from git tracking"

# Ensure .gitignore has .env entry
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Update .gitignore to exclude .env"
```

### Issue 5: Directory Structure Incorrect

**Symptoms:**
```
Validation script fails with "Directory missing" errors
```

**Solution:**
```bash
# Re-run directory creation
mkdir -p bot workspace sessions backups docs/implementation

# Add .gitkeep files
touch workspace/.gitkeep sessions/.gitkeep backups/.gitkeep

# Stage and commit
git add .
git commit -m "Fix directory structure"
```

## Rollback Procedure

If you need to start over:

### Option 1: Reset to Clean State (No Git History Loss)

```bash
# Remove all uncommitted changes
git reset --hard HEAD

# Clean untracked files (CAREFUL: this deletes files)
git clean -fd

# Verify clean state
git status
```

### Option 2: Complete Restart (Delete Everything)

```bash
# Go up one directory
cd ..

# Remove project directory
rm -rf claude-remote-runner

# Re-create and start Step 1 again
mkdir claude-remote-runner
cd claude-remote-runner
# ... follow Step 1 instructions from beginning
```

### Option 3: Revert Specific Files

```bash
# Revert specific file to last commit
git checkout HEAD -- README.md

# Revert all files in a directory
git checkout HEAD -- bot/

# Verify changes
git status
```

## Next Step

Once all acceptance criteria are met and validation passes, proceed to:

**Step 2: Obtain API Keys & Credentials**
- File: `docs/implementation/step_02_credentials.md`
- Duration: 30 minutes
- Goal: Obtain and configure all required API keys (Telegram, Anthropic, OpenAI)

Before proceeding, ensure:
1. `git status` shows clean working tree
2. All directories exist and are properly structured
3. `.env.example` is complete with all required variables
4. README.md is clear and comprehensive
5. Validation script passes all checks

**Checkpoint:** You should now have a clean, well-organized repository ready for development. All subsequent steps will build on this foundation.
