"""Expense inline keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot_settings


def get_add_expense_menu() -> InlineKeyboardMarkup:
    """Get menu for adding or viewing expenses."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Create New Expense", callback_data="expense_create")],
        [InlineKeyboardButton(text="📝 View My Expenses", callback_data="expense_view")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_for_expense(categories: list, page: int = 1, per_page: int = None) -> InlineKeyboardMarkup:
    """Get inline buttons for category selection with pagination."""
    if per_page is None:
        per_page = bot_settings.CATEGORIES_PER_PAGE
        
    keyboard = []
    
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                text=category['title'],
                callback_data=f"exp_cat:{category['id']}"
            )
        ])
    
    # Pagination buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"exp_cat_page:{page-1}"))
    if len(categories) >= per_page:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"exp_cat_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="expense_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_expenses_list(expenses: list, categories_dict: dict, page: int = 1, per_page: int = None) -> InlineKeyboardMarkup:
    """Get list of expenses with pagination."""
    if per_page is None:
        per_page = bot_settings.EXPENSES_PER_PAGE
        
    keyboard = []
    
    for expense in expenses:
        category_name = categories_dict.get(expense['category_id'], 'Unknown')
        description = f" - {expense['description']}" if expense.get('description') else ""
        text = f"💰 ${expense['amount']:.2f} - {category_name}{description}"
        
        keyboard.append([
            InlineKeyboardButton(
                text=text[:60] + "..." if len(text) > 60 else text,
                callback_data=f"exp_select:{expense['id']}"
            )
        ])
    
    # Pagination buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"exp_page:{page-1}"))
    if len(expenses) >= per_page:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"exp_page:{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="expense_back")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_expense_actions(expense_id: int) -> InlineKeyboardMarkup:
    """Get action buttons for selected expense."""
    keyboard = [
        [InlineKeyboardButton(text="✏️ Edit Amount", callback_data=f"exp_edit_amount:{expense_id}")],
        [InlineKeyboardButton(text="📝 Edit Description", callback_data=f"exp_edit_desc:{expense_id}")],
        [InlineKeyboardButton(text="🗑 Delete Expense", callback_data=f"exp_delete:{expense_id}")],
        [InlineKeyboardButton(text="🔙 Back to List", callback_data="expense_view")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_no_categories_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard when user has no categories."""
    keyboard = [
        [InlineKeyboardButton(text="➕ Create Category", callback_data="category_add")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_no_expenses_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard when user has no expenses."""
    keyboard = [
        [InlineKeyboardButton(text="💸 Expenses", callback_data="expense_create")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
