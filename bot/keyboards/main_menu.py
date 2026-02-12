"""Main menu keyboard."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [
            KeyboardButton(text="💸 Expenses"),
            KeyboardButton(text="📊 Statistics"),
        ],
        [
            KeyboardButton(text="📂 Categories"),
            KeyboardButton(text="👤 Profile"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Choose an option..."
    )
