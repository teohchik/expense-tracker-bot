"""Categories inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot_settings


def get_categories_menu() -> InlineKeyboardMarkup:
    """Get categories menu with inline buttons."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Add Category", callback_data="category_add")],
        [InlineKeyboardButton(text="✏️ Edit Categories", callback_data="category_edit")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_list(categories: list, page: int = 1, per_page: int = None) -> InlineKeyboardMarkup:
    """Get list of categories with pagination."""
    if per_page is None:
        per_page = bot_settings.CATEGORIES_PER_PAGE
        
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category['title'],
                callback_data=f"cat_select:{category['id']}"
            )
        ])
    
    # Pagination buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"cat_page:{page-1}"))
    if len(categories) >= per_page:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"cat_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="cat_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_category_actions(category_id: int) -> InlineKeyboardMarkup:
    """Get action buttons for selected category."""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Rename", callback_data=f"cat_rename:{category_id}")],
        [InlineKeyboardButton(text="🗑 Delete Category", callback_data=f"cat_toggle:{category_id}")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="category_edit")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_empty_categories_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard when user has no categories."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Add First Category", callback_data="category_add")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
