"""
Configuration management for Telegram bot.
Loads and validates environment variables.
"""

import os
import sys
from typing import List
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_required_env(var_name: str) -> str:
    """Get required environment variable or exit."""
    value = os.getenv(var_name)
    if not value:
        print(f"ERROR: {var_name} environment variable is required but not set")
        sys.exit(1)
    return value

def get_optional_env(var_name: str, default: str = "") -> str:
    """Get optional environment variable with default."""
    return os.getenv(var_name, default)

# Required API keys
TELEGRAM_TOKEN = get_required_env('TELEGRAM_TOKEN')
DEEPGRAM_API_KEY = get_required_env('DEEPGRAM_API_KEY')

# Optional configuration
WEBHOOK_URL = get_optional_env('WEBHOOK_URL')
BOT_MODE = get_optional_env('BOT_MODE', 'polling')  # polling or webhook

# User authorization
ALLOWED_USER_IDS_STR = get_optional_env('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS: List[int] = []
if ALLOWED_USER_IDS_STR:
    try:
        ALLOWED_USER_IDS = [
            int(uid.strip())
            for uid in ALLOWED_USER_IDS_STR.split(',')
            if uid.strip()
        ]
    except ValueError as e:
        print(f"ERROR: Invalid ALLOWED_USER_IDS format: {e}")
        sys.exit(1)

# Paths
WORKSPACE_DIR = '/workspace'
SESSIONS_DIR = './sessions'

# Bot settings
MAX_MESSAGE_LENGTH = 4000  # Telegram limit is 4096, leave buffer
LOG_LEVEL = get_optional_env('LOG_LEVEL', 'INFO')

# Validate configuration
def validate_config():
    """Validate configuration and print summary."""
    print("=" * 50)
    print("Bot Configuration:")
    print("=" * 50)
    print(f"Telegram Token: {'✓ Set' if TELEGRAM_TOKEN else '✗ Missing'}")
    print(f"Deepgram API Key: {'✓ Set' if DEEPGRAM_API_KEY else '✗ Missing'}")
    print(f"Bot Mode: {BOT_MODE}")
    print(f"Webhook URL: {WEBHOOK_URL if WEBHOOK_URL else 'Not set (using polling)'}")
    print(f"Allowed User IDs: {ALLOWED_USER_IDS if ALLOWED_USER_IDS else 'All users allowed (NOT RECOMMENDED)'}")
    print(f"Workspace Directory: {WORKSPACE_DIR}")
    print(f"Sessions Directory: {SESSIONS_DIR}")
    print(f"Log Level: {LOG_LEVEL}")
    print("=" * 50)

if __name__ == '__main__':
    validate_config()
