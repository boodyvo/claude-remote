#!/usr/bin/env python3
"""
Logging configuration for the Telegram bot.
Provides structured logging with different levels and formatters.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Log directory
LOG_DIR = Path('logs')
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
MAIN_LOG = LOG_DIR / 'bot.log'
ERROR_LOG = LOG_DIR / 'error.log'
ACCESS_LOG = LOG_DIR / 'access.log'

# Log format
DETAILED_FORMAT = (
    '%(asctime)s - %(name)s - %(levelname)s - '
    '[%(filename)s:%(lineno)d] - %(message)s'
)

SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'


def setup_logging(level=logging.INFO, log_to_file=True):
    """
    Configure logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files in addition to console
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(SIMPLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    if log_to_file:
        # Main log file (rotating, 10MB max, 5 backups)
        main_handler = RotatingFileHandler(
            MAIN_LOG,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_formatter = logging.Formatter(DETAILED_FORMAT)
        main_handler.setFormatter(main_formatter)
        root_logger.addHandler(main_handler)

        # Error log file (errors and above only)
        error_handler = RotatingFileHandler(
            ERROR_LOG,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(DETAILED_FORMAT)
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

    logging.info("Logging configured successfully")


def log_access(user_id: int, action: str, details: str = ""):
    """
    Log user access/actions to access log.

    Args:
        user_id: Telegram user ID
        action: Action performed (e.g., "voice_message", "text_command")
        details: Additional details
    """
    access_logger = logging.getLogger('access')

    # Ensure access log handler exists
    if not access_logger.handlers:
        access_handler = RotatingFileHandler(
            ACCESS_LOG,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        access_formatter = logging.Formatter(
            '%(asctime)s - User:%(user_id)s - %(action)s - %(details)s'
        )
        access_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False  # Don't propagate to root logger

    access_logger.info(
        "",
        extra={
            'user_id': user_id,
            'action': action,
            'details': details
        }
    )


class ContextLogger:
    """Logger with additional context."""

    def __init__(self, name: str, **context):
        self.logger = logging.getLogger(name)
        self.context = context

    def _format_message(self, message: str) -> str:
        """Add context to log message."""
        if self.context:
            ctx = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"[{ctx}] {message}"
        return message

    def debug(self, message: str, **kwargs):
        self.logger.debug(self._format_message(message), **kwargs)

    def info(self, message: str, **kwargs):
        self.logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(self._format_message(message), **kwargs)

    def critical(self, message: str, **kwargs):
        self.logger.critical(self._format_message(message), **kwargs)
