"""Profile keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get profile keyboard with change currency button."""
    keyboard = [
        [InlineKeyboardButton(text="💱 Change Currency", callback_data="profile_change_currency")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_currency_selection_keyboard() -> InlineKeyboardMarkup:
    """Get currency selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="€", callback_data="currency_EUR"),
            InlineKeyboardButton(text="₴", callback_data="currency_UAH"),
            InlineKeyboardButton(text="$", callback_data="currency_USD"),
        ],
        [
            InlineKeyboardButton(text="✏️ Custom", callback_data="currency_custom"),
        ],
        [
            InlineKeyboardButton(text="« Back", callback_data="profile_back"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_custom_currency_back_keyboard() -> InlineKeyboardMarkup:
    """Get back button for custom currency input."""
    keyboard = [
        [InlineKeyboardButton(text="« Back", callback_data="profile_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
