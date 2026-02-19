"""Salary inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot_settings


def get_salary_menu() -> InlineKeyboardMarkup:
    """Get menu for adding or viewing salaries."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Add Salary", callback_data="salary_create")],
        [InlineKeyboardButton(text="📝 View My Salaries", callback_data="salary_view")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_salaries_list(salaries: list, page: int = 1, per_page: int = None, currency: str = "€") -> InlineKeyboardMarkup:
    """Get paginated list of salary entries."""
    if per_page is None:
        per_page = bot_settings.EXPENSES_PER_PAGE

    keyboard = []

    for salary in salaries:
        description = f" - {salary['description']}" if salary.get('description') else ""
        text = f"💰 {currency}{salary['amount']:.2f}{description}"
        keyboard.append([
            InlineKeyboardButton(
                text=text[:60] + "..." if len(text) > 60 else text,
                callback_data=f"sal_select:{salary['id']}"
            )
        ])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"sal_page:{page-1}"))
    if len(salaries) >= per_page:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"sal_page:{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="salary_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_salary_actions(salary_id: int) -> InlineKeyboardMarkup:
    """Get action buttons for a selected salary entry."""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Edit Amount", callback_data=f"sal_edit_amount:{salary_id}")],
        [InlineKeyboardButton(text="📝 Edit Description", callback_data=f"sal_edit_desc:{salary_id}")],
        [InlineKeyboardButton(text="🗑 Delete", callback_data=f"sal_delete:{salary_id}")],
        [InlineKeyboardButton(text="🔙 Back to List", callback_data="salary_view")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_no_salaries_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard when user has no salary entries."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Add Salary", callback_data="salary_create")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
