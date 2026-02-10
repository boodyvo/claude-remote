#!/usr/bin/env python3
"""
Error handling utilities and custom exceptions.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes for categorization."""
    # API errors
    TELEGRAM_API_ERROR = "telegram_api_error"
    DEEPGRAM_API_ERROR = "deepgram_api_error"
    CLAUDE_API_ERROR = "claude_api_error"

    # Authentication/Authorization
    UNAUTHORIZED = "unauthorized"
    INVALID_API_KEY = "invalid_api_key"

    # Execution errors
    CLAUDE_EXECUTION_ERROR = "claude_execution_error"
    TIMEOUT = "timeout"
    SUBPROCESS_ERROR = "subprocess_error"

    # File system errors
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DISK_FULL = "disk_full"

    # Input errors
    INVALID_INPUT = "invalid_input"
    MESSAGE_TOO_LONG = "message_too_long"
    EMPTY_TRANSCRIPTION = "empty_transcription"

    # Rate limiting
    RATE_LIMITED = "rate_limited"

    # System errors
    OUT_OF_MEMORY = "out_of_memory"
    UNKNOWN_ERROR = "unknown_error"


class BotError(Exception):
    """Base exception for bot errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.user_message = user_message or message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            'error_code': self.error_code.value,
            'error_message': str(self),
            'user_facing_message': self.user_message,
            'error_details': self.details
        }


class APIError(BotError):
    """API-related errors."""
    pass


class ExecutionError(BotError):
    """Execution-related errors."""
    pass


class InputError(BotError):
    """User input errors."""
    pass


def handle_error(
    error: Exception,
    context: str = "",
    user_id: Optional[int] = None
) -> str:
    """
    Handle an error and return user-friendly message.

    Args:
        error: The exception that occurred
        context: Context where error occurred
        user_id: User ID if available

    Returns:
        User-friendly error message
    """
    # Log the error
    log_message = f"Error in {context}: {str(error)}"
    if user_id:
        log_message = f"[User {user_id}] {log_message}"

    # Determine severity and user message
    if isinstance(error, BotError):
        logger.error(log_message, extra=error.to_dict())
        return error.user_message

    # Handle known exception types
    error_str = str(error).lower()

    if isinstance(error, TimeoutError) or "timeout" in error_str:
        logger.error(f"{log_message} - TIMEOUT")
        return (
            "⏱️ Operation timed out. The task may still be running.\n\n"
            "Try a simpler request or check back later."
        )

    elif isinstance(error, PermissionError):
        logger.error(f"{log_message} - PERMISSION_DENIED")
        return (
            "🔒 Permission denied. Unable to access required resource.\n\n"
            "Please contact the administrator."
        )

    elif isinstance(error, FileNotFoundError):
        logger.error(f"{log_message} - FILE_NOT_FOUND")
        return (
            "📁 Required file not found.\n\n"
            "The system may need to be reconfigured."
        )

    elif "rate limit" in error_str:
        logger.warning(f"{log_message} - RATE_LIMITED")
        return (
            "⏱️ Rate limit exceeded. Please wait a moment and try again.\n\n"
            "Tip: Reduce the frequency of requests."
        )

    elif "api key" in error_str or "unauthorized" in error_str or "authentication" in error_str:
        logger.error(f"{log_message} - AUTH_ERROR")
        return (
            "🔑 Authentication error. The API key may be invalid or expired.\n\n"
            "Please contact the administrator."
        )

    elif "out of memory" in error_str:
        logger.critical(f"{log_message} - OUT_OF_MEMORY")
        return (
            "💾 System out of memory. Please try again later.\n\n"
            "If this persists, contact the administrator."
        )

    elif "connection" in error_str or "network" in error_str:
        logger.error(f"{log_message} - NETWORK_ERROR")
        return (
            "🌐 Network connection error. Please check your connection and try again.\n\n"
            "If this persists, the service may be temporarily unavailable."
        )

    else:
        # Unknown error
        logger.error(f"{log_message} - UNKNOWN", exc_info=True)
        return (
            "💥 An unexpected error occurred.\n\n"
            "The error has been logged. Please try again or contact support."
        )


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Tuple of (success: bool, result: Any, error: Optional[str])
    """
    try:
        result = func(*args, **kwargs)
        return (True, result, None)
    except Exception as e:
        error_msg = handle_error(e, context=func.__name__)
        return (False, None, error_msg)
