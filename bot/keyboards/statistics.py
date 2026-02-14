"""Statistics inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_statistics_menu() -> InlineKeyboardMarkup:
    """Get menu for statistics period selection."""
    keyboard = [
        [InlineKeyboardButton(text="📅 Current Month", callback_data="stats_current_month")],
        [InlineKeyboardButton(text="📆 Previous Month", callback_data="stats_previous_month")],
        [InlineKeyboardButton(text="🗓 Custom Period", callback_data="stats_custom")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_custom_stats_back_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with back button for custom stats flow."""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Back to Statistics", callback_data="stats_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
