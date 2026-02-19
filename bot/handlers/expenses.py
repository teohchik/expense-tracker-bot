"""Expenses handler."""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.expenses import (
    get_add_expense_menu,
    get_categories_for_expense,
    get_expenses_list,
    get_expense_actions,
    get_no_categories_keyboard,
    get_no_expenses_keyboard,
)
from bot.states.expense import AddExpenseStates, EditExpenseStates
from api.client import api_client
from config import bot_settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "💸 Expenses")
async def show_expense_menu(message: Message):
    """Show expense management menu."""
    telegram_id = message.from_user.id
    
    # Check if user has categories first
    response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=1)
    
    if response.status_code == 200:
        categories = response.json()
    elif response.status_code == 404:
        categories = []  # No categories yet
    else:
        logger.error(f"Failed to get categories: status={response.status_code}, telegram_id={telegram_id}")
        await message.answer("❌ Error loading data. Please try again later.")
        return
    
    if categories:
        # User has categories - show expense menu
        await message.answer(
            "💰 Expense Management\n\nChoose an action:",
            reply_markup=get_add_expense_menu()
        )
    else:
        # No categories - must create them first
        await message.answer(
            "💰 Expense Tracker\n\n"
            "To track expenses, you need to create categories first!\n\n"
            "Categories help organize your spending by type.\n\n"
            "Create your first category to get started.",
            reply_markup=get_no_categories_keyboard()
        )
        reply_markup=get_add_expense_menu()



@router.callback_query(F.data == "expense_create")
async def start_add_expense(callback: CallbackQuery, state: FSMContext):
    """Start adding a new expense."""
    await callback.message.answer("💵 Enter expense amount:")
    await state.set_state(AddExpenseStates.waiting_for_amount)
    await callback.answer()


@router.message(AddExpenseStates.waiting_for_amount)
async def process_expense_amount(message: Message, state: FSMContext):
    """Process expense amount input."""
    try:
        # Replace comma with dot for decimal separator
        amount = float(message.text.strip().replace(',', '.'))
        
        if amount <= 0:
            await message.answer("❌ Amount must be greater than 0. Please try again:")
            return
        
        if amount > 1_000_000:
            await message.answer("❌ Amount is too large (max 1,000,000). Please try again:")
            return
        
        # Save amount and fetch categories
        await state.update_data(amount=amount)
        telegram_id = message.from_user.id
        per_page = bot_settings.CATEGORIES_PER_PAGE
        
        response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=per_page)
        
        if response.status_code == 200:
            categories = response.json()
        elif response.status_code == 404:
            categories = []  # No categories yet
        else:
            logger.error(f"Failed to get categories: status={response.status_code}")
            await message.answer("❌ Error loading categories. Please try again later.")
            await state.clear()
            return
        
        if categories:
            await message.answer(
                "📂 Select a category:",
                reply_markup=get_categories_for_expense(categories, page=1, per_page=per_page)
            )
            await state.set_state(AddExpenseStates.waiting_for_category)
        else:
            await message.answer(
                "📂 You need categories first!\n\n"
                "Categories help organize your expenses.\n"
                "Let's create your first category!",
                reply_markup=get_no_categories_keyboard()
            )
            await state.clear()
            
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number:")


@router.callback_query(F.data.startswith("exp_cat:"), AddExpenseStates.waiting_for_category)
async def process_expense_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection."""
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    
    await callback.message.answer(
        "📝 Enter description (optional):\n\nSend /skip to skip description."
    )
    await state.set_state(AddExpenseStates.waiting_for_description)
    await callback.answer()


@router.callback_query(F.data.startswith("exp_cat_page:"), AddExpenseStates.waiting_for_category)
async def paginate_expense_categories(callback: CallbackQuery, state: FSMContext):
    """Handle category pagination during expense creation."""
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    per_page = bot_settings.CATEGORIES_PER_PAGE
    
    response = await api_client.get_categories(telegram_id=telegram_id, page=page, per_page=per_page)
    
    if response.status_code == 200:
        categories = response.json()
    elif response.status_code == 404:
        categories = []
    else:
        logger.error(f"Failed to get categories: status={response.status_code}, telegram_id={telegram_id}")
        await callback.answer("❌ Error loading categories", show_alert=True)
        return
    
    if categories:
        await callback.message.edit_reply_markup(
            reply_markup=get_categories_for_expense(categories, page=page, per_page=per_page)
        )
    else:
        await callback.answer("No more categories", show_alert=True)
    
    await callback.answer()


@router.message(AddExpenseStates.waiting_for_description, F.text == "/skip")
async def skip_expense_description(message: Message, state: FSMContext):
    """Skip description and create expense."""
    await create_expense_from_state(message, state, description=None)


@router.message(AddExpenseStates.waiting_for_description)
async def process_expense_description(message: Message, state: FSMContext):
    """Process expense description."""
    description = message.text.strip()
    
    if len(description) > 500:
        await message.answer("❌ Description is too long (max 500 characters). Please try again:")
        return
    
    await create_expense_from_state(message, state, description=description)


async def create_expense_from_state(message: Message, state: FSMContext, description: str = None):
    """Create expense from FSM state data."""
    data = await state.get_data()
    amount = data.get("amount")
    category_id = data.get("category_id")
    telegram_id = message.from_user.id
    
    logger.info(f"Creating expense: telegram_id={telegram_id}, amount={amount}, category_id={category_id}")
    
    # Get user currency
    user_response = await api_client.get_user(telegram_id)
    currency = "€"  # Default currency
    if user_response.status_code == 200:
        user_data = user_response.json()
        currency = user_data.get("currency", "€")
    
    response = await api_client.create_expense(
        telegram_id=telegram_id,
        category_id=category_id,
        amount=amount,
        description=description
    )
    
    if response.status_code == 201:
        expense_data = response.json()
        logger.info(f"Expense created successfully: id={expense_data.get('id')}")
        await message.answer(f"✅ Expense created!\n\n💰 Amount: {currency}{amount:.2f}")
        await state.clear()
    else:
        logger.error(f"Failed to create expense: status={response.status_code}")
        await message.answer("❌ An error occurred. Please try again later.")
        await state.clear()


@router.callback_query(F.data == "expense_cancel")
async def cancel_expense(callback: CallbackQuery, state: FSMContext):
    """Cancel expense creation."""
    await state.clear()
    await callback.message.answer("❌ Expense creation cancelled.")
    await callback.answer()


@router.callback_query(F.data == "expense_view")
async def view_expenses(callback: CallbackQuery):
    """Show current month expenses."""
    telegram_id = callback.from_user.id
    now = datetime.now()
    year = now.year
    month = now.month
    per_page = bot_settings.EXPENSES_PER_PAGE
    
    # Get user currency
    user_response = await api_client.get_user(telegram_id)
    currency = "€"  # Default currency
    if user_response.status_code == 200:
        user_data = user_response.json()
        currency = user_data.get("currency", "€")
    
    # Fetch categories first for display
    categories_response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=100)
    
    if categories_response.status_code == 200:
        categories = categories_response.json()
    elif categories_response.status_code == 404:
        categories = []  # No categories yet
    else:
        await callback.answer("❌ Error loading categories", show_alert=True)
        return
    
    categories_dict = {cat['id']: cat['title'] for cat in categories}
    
    # Fetch expenses
    response = await api_client.get_expenses_for_month(
        telegram_id=telegram_id,
        year=year,
        month=month,
        page=1,
        per_page=per_page
    )
    
    if response.status_code == 200:
        expenses = response.json()
        if expenses:
            await callback.message.edit_text(
                f"📊 Expenses for {month}/{year}\n\nSelect an expense to edit:",
                reply_markup=get_expenses_list(expenses, categories_dict, page=1, per_page=per_page, currency=currency)
            )
        else:
            await callback.message.edit_text(
                f"📊 No expenses for {month}/{year}\n\n"
                "💡 Start tracking your spending!\n"
                "Add your first expense to see it here.",
                reply_markup=get_no_expenses_keyboard()
            )
    else:
        logger.error(f"Failed to get expenses: status={response.status_code}")
        await callback.answer("❌ Error loading expenses", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("exp_page:"))
async def paginate_expenses(callback: CallbackQuery):
    """Handle expense pagination."""
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    now = datetime.now()
    year = now.year
    month = now.month
    per_page = bot_settings.EXPENSES_PER_PAGE
    
    # Get user currency
    user_response = await api_client.get_user(telegram_id)
    currency = "€"  # Default currency
    if user_response.status_code == 200:
        user_data = user_response.json()
        currency = user_data.get("currency", "€")
    
    # Fetch categories
    categories_response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=100)
    
    if categories_response.status_code == 200:
        categories = categories_response.json()
    elif categories_response.status_code == 404:
        categories = []  # No categories yet
    else:
        await callback.answer("❌ Error loading categories", show_alert=True)
        return
    
    categories_dict = {cat['id']: cat['title'] for cat in categories}
    
    # Fetch expenses
    response = await api_client.get_expenses_for_month(
        telegram_id=telegram_id,
        year=year,
        month=month,
        page=page,
        per_page=per_page
    )
    
    if response.status_code == 200:
        expenses = response.json()
        await callback.message.edit_reply_markup(
            reply_markup=get_expenses_list(expenses, categories_dict, page=page, per_page=per_page, currency=currency)
        )
    else:
        logger.error(f"Failed to get expenses: status={response.status_code}")
        await callback.answer("❌ Error loading expenses", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("exp_select:"))
async def select_expense(callback: CallbackQuery):
    """Show actions for selected expense."""
    expense_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        "🔧 Expense Actions\n\nWhat would you like to do?",
        reply_markup=get_expense_actions(expense_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exp_edit_amount:"))
async def start_edit_amount(callback: CallbackQuery, state: FSMContext):
    """Start editing expense amount."""
    expense_id = int(callback.data.split(":")[1])
    await state.update_data(expense_id=expense_id)
    await state.set_state(EditExpenseStates.waiting_for_new_amount)
    await callback.message.answer("💵 Enter new amount:")
    await callback.answer()


@router.message(EditExpenseStates.waiting_for_new_amount)
async def process_new_amount(message: Message, state: FSMContext):
    """Process new expense amount."""
    try:
        # Replace comma with dot for decimal separator
        amount = float(message.text.strip().replace(',', '.'))
        
        if amount <= 0:
            await message.answer("❌ Amount must be greater than 0. Please try again:")
            return
        
        if amount > 1_000_000:
            await message.answer("❌ Amount is too large (max 1,000,000). Please try again:")
            return
        
        data = await state.get_data()
        expense_id = data.get("expense_id")
        telegram_id = message.from_user.id
        
        # Get user currency
        user_response = await api_client.get_user(telegram_id)
        currency = "€"  # Default currency
        if user_response.status_code == 200:
            user_data = user_response.json()
            currency = user_data.get("currency", "€")
        
        logger.info(f"Updating expense amount: expense_id={expense_id}, new_amount={amount}")
        
        response = await api_client.update_expense(expense_id=expense_id, amount=amount)
        
        if response.status_code == 200:
            expense_data = response.json()
            logger.info(f"Expense amount updated successfully: expense_id={expense_id}")
            
            # Show updated expense data
            description = expense_data.get('description', '')
            updated_amount = expense_data.get('amount', amount)
            
            message_text = f"✅ Expense updated!\n\n"
            message_text += f"💰 Amount: {currency}{updated_amount:.2f}\n"
            
            # Only show category if available
            if 'category_title' in expense_data and expense_data['category_title']:
                message_text += f"📂 Category: {expense_data['category_title']}\n"
            
            if description:
                message_text += f"📝 Description: {description}"
            
            await message.answer(message_text)
            await state.clear()
        else:
            logger.error(f"Failed to update expense: status={response.status_code}")
            await message.answer("❌ An error occurred. Please try again later.")
            await state.clear()
            
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number:")


@router.callback_query(F.data.startswith("exp_edit_desc:"))
async def start_edit_description(callback: CallbackQuery, state: FSMContext):
    """Start editing expense description."""
    expense_id = int(callback.data.split(":")[1])
    await state.update_data(expense_id=expense_id)
    await state.set_state(EditExpenseStates.waiting_for_new_description)
    await callback.message.answer("📝 Enter new description:")
    await callback.answer()


@router.message(EditExpenseStates.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext):
    """Process new expense description."""
    description = message.text.strip()
    
    if len(description) > 500:
        await message.answer("❌ Description is too long (max 500 characters). Please try again:")
        return
    
    data = await state.get_data()
    expense_id = data.get("expense_id")
    telegram_id = message.from_user.id
    
    # Get user currency
    user_response = await api_client.get_user(telegram_id)
    currency = "€"  # Default currency
    if user_response.status_code == 200:
        user_data = user_response.json()
        currency = user_data.get("currency", "€")
    
    logger.info(f"Updating expense description: expense_id={expense_id}")
    
    response = await api_client.update_expense(expense_id=expense_id, description=description)
    
    if response.status_code == 200:
        expense_data = response.json()
        logger.info(f"Expense description updated successfully: expense_id={expense_id}")
        
        # Show updated expense data
        updated_description = expense_data.get('description', description)
        amount = expense_data.get('amount', 0)
        
        message_text = f"✅ Expense updated!\n\n"
        message_text += f"💰 Amount: {currency}{amount:.2f}\n"
        
        # Only show category if available
        if 'category_title' in expense_data and expense_data['category_title']:
            message_text += f"📂 Category: {expense_data['category_title']}\n"
        
        message_text += f"📝 Description: {updated_description}"
        
        await message.answer(message_text)
        await state.clear()
    else:
        logger.error(f"Failed to update expense: status={response.status_code}")
        await message.answer("❌ An error occurred. Please try again later.")
        await state.clear()


@router.callback_query(F.data.startswith("exp_delete:"))
async def delete_expense(callback: CallbackQuery):
    """Delete expense."""
    expense_id = int(callback.data.split(":")[1])
    
    logger.info(f"Deleting expense: expense_id={expense_id}")
    
    response = await api_client.delete_expense(expense_id=expense_id)
    
    if response.status_code == 204:
        logger.info(f"Expense deleted: expense_id={expense_id}")
        await callback.answer("✅ Expense deleted!", show_alert=True)
        await callback.message.edit_text("✅ Expense deleted!")
    else:
        logger.error(f"Failed to delete expense: status={response.status_code}")
        await callback.answer("❌ An error occurred", show_alert=True)


@router.callback_query(F.data == "expense_back")
async def back_to_expense_menu(callback: CallbackQuery):
    """Return to expense menu."""
    await callback.message.edit_text(
        "💰 Expense Management\n\nChoose an action:",
        reply_markup=get_add_expense_menu()
    )
    await callback.answer()


@router.message(StateFilter(None), F.text.regexp(r'^\d+([.,]\d+)?$'))
async def quick_add_expense(message: Message, state: FSMContext):
    """Handle plain number input and jump straight to category selection."""
    try:
        amount = float(message.text.strip().replace(',', '.'))
    except ValueError:
        return

    if amount <= 0 or amount > 1_000_000:
        return

    await state.update_data(amount=amount)
    telegram_id = message.from_user.id
    per_page = bot_settings.CATEGORIES_PER_PAGE

    response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=per_page)

    if response.status_code == 200:
        categories = response.json()
    elif response.status_code == 404:
        categories = []
    else:
        logger.error(f"Quick add: failed to get categories: status={response.status_code}")
        await message.answer("❌ Error loading categories. Please try again later.")
        await state.clear()
        return

    if categories:
        await message.answer(
            f"💵 Amount: {amount:.2f}\n\n📂 Select a category:",
            reply_markup=get_categories_for_expense(categories, page=1, per_page=per_page)
        )
        await state.set_state(AddExpenseStates.waiting_for_category)
    else:
        await message.answer(
            "📂 You need categories first!\n\n"
            "Create your first category to start tracking expenses.",
            reply_markup=get_no_categories_keyboard()
        )
