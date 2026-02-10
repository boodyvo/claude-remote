#!/usr/bin/env python3
"""
Inline keyboard layouts for Telegram bot.
Provides reusable button configurations.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional


class KeyboardBuilder:
    """Build inline keyboards for various bot responses."""

    @staticmethod
    def main_actions(
        has_changes: bool = True,
        session_active: bool = True
    ) -> InlineKeyboardMarkup:
        """
        Main action buttons for Claude responses.

        Args:
            has_changes: Whether there are changes to approve/reject
            session_active: Whether there's an active session

        Returns:
            InlineKeyboardMarkup with action buttons
        """
        buttons = []

        if has_changes:
            # First row: Approve/Reject
            buttons.append([
                InlineKeyboardButton("✅ Approve", callback_data='action:approve'),
                InlineKeyboardButton("❌ Reject", callback_data='action:reject')
            ])

        # Second row: Info buttons
        buttons.append([
            InlineKeyboardButton("📝 Show Diff", callback_data='git:diff'),
            InlineKeyboardButton("📊 Git Status", callback_data='git:status')
        ])

        # Third row: Additional actions
        row = [
            InlineKeyboardButton("🔄 Retry", callback_data='action:retry')
        ]

        if session_active:
            row.append(
                InlineKeyboardButton("📋 Session Info", callback_data='info:session')
            )

        buttons.append(row)

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def confirmation(action: str) -> InlineKeyboardMarkup:
        """
        Confirmation keyboard for destructive actions.

        Args:
            action: Action to confirm (e.g., 'clear', 'delete')

        Returns:
            InlineKeyboardMarkup with confirm/cancel buttons
        """
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data=f'confirm:{action}'
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data=f'cancel:{action}'
                )
            ]
        ])

    @staticmethod
    def session_management() -> InlineKeyboardMarkup:
        """Keyboard for session management."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🆕 New Session",
                    callback_data='session:new'
                ),
                InlineKeyboardButton(
                    "📚 List Sessions",
                    callback_data='session:list'
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Clean Old Sessions",
                    callback_data='session:clean'
                ),
                InlineKeyboardButton(
                    "📊 Session Info",
                    callback_data='session:info'
                )
            ]
        ])

    @staticmethod
    def git_actions() -> InlineKeyboardMarkup:
        """Keyboard for git-related actions."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Diff", callback_data='git:diff'),
                InlineKeyboardButton("📊 Status", callback_data='git:status')
            ],
            [
                InlineKeyboardButton("📜 Log", callback_data='git:log'),
                InlineKeyboardButton("🌿 Branches", callback_data='git:branches')
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data='action:back')
            ]
        ])

    @staticmethod
    def close_button() -> InlineKeyboardMarkup:
        """Simple close/dismiss button."""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ Dismiss", callback_data='action:dismiss')]
        ])

    @staticmethod
    def pagination(
        current_page: int,
        total_pages: int,
        data_type: str
    ) -> InlineKeyboardMarkup:
        """
        Pagination keyboard for lists.

        Args:
            current_page: Current page number (0-indexed)
            total_pages: Total number of pages
            data_type: Type of data being paginated (for callback)

        Returns:
            InlineKeyboardMarkup with pagination buttons
        """
        buttons = []

        nav_row = []
        if current_page > 0:
            nav_row.append(
                InlineKeyboardButton(
                    "◀️ Previous",
                    callback_data=f'page:{data_type}:{current_page-1}'
                )
            )

        nav_row.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data='page:noop'
            )
        )

        if current_page < total_pages - 1:
            nav_row.append(
                InlineKeyboardButton(
                    "Next ▶️",
                    callback_data=f'page:{data_type}:{current_page+1}'
                )
            )

        buttons.append(nav_row)
        buttons.append([
            InlineKeyboardButton("🗑️ Dismiss", callback_data='action:dismiss')
        ])

        return InlineKeyboardMarkup(buttons)
