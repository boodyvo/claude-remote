# ==============================================
# Claude Remote Runner - Telegram Bot Image
# ==============================================
# Production-ready image for voice-controlled Claude Code bot
#
# Base: Python 3.11 slim (Debian-based)
# Features:
# - ffmpeg for audio processing
# - Claude Code CLI
# - Git for repository operations
# - All Python dependencies
# ==============================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="claude-remote-runner"
LABEL description="Telegram bot for voice-controlled Claude Code execution"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_VERSION=20

# Set working directory
WORKDIR /app

# Install system dependencies
# - ffmpeg: Audio file processing for voice messages
# - curl: Health checks and API calls
# - git: Repository operations
# - nodejs/npm: Required for Claude Code CLI
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        ffmpeg \
        curl \
        git \
        ca-certificates \
        gnupg && \
    # Install Node.js from NodeSource
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_VERSION}.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends nodejs && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code --silent

# Copy requirements first (better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for Claude Code (--dangerously-skip-permissions blocked for root)
RUN useradd -m -u 1000 -s /bin/bash botuser && \
    mkdir -p /app/sessions /workspace && \
    chown -R botuser:botuser /app /workspace

# Startup script: fixes volume mount permissions then drops to botuser
RUN printf '#!/bin/bash\n\
# Fix home dir permissions (volume mount may be root-owned)\n\
chown -R botuser:botuser /home/botuser 2>/dev/null || true\n\
# Drop to botuser and run bot\n\
exec gosu botuser python /app/bot.py\n' > /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

# Install gosu for clean privilege dropping
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends gosu && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Runs as root to fix permissions, then drops to botuser
CMD ["/usr/local/bin/start.sh"]
