"""Statistics handler."""
import logging
from datetime import datetime
from collections import defaultdict
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.statistics import get_statistics_menu, get_custom_stats_back_keyboard
from bot.states.statistics import StatisticsStates
from api.client import api_client

router = Router()
logger = logging.getLogger(__name__)


def calculate_statistics(expenses: list) -> dict:
    """Calculate statistics from expenses list.
    
    Args:
        expenses: List of expense dictionaries with 'amount' and 'category_id'
        
    Returns:
        Dictionary with total sum and category breakdown
    """
    if not expenses:
        return {"total": 0, "by_category": {}}
    
    total = sum(expense['amount'] for expense in expenses)
    
    # Group by category and sum amounts
    category_totals = defaultdict(float)
    for expense in expenses:
        category_id = expense['category_id']
        category_totals[category_id] += expense['amount']
    
    # Sort by amount descending
    sorted_categories = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    return {
        "total": total,
        "by_category": dict(sorted_categories),
        "count": len(expenses)
    }


def format_statistics_message(stats: dict, categories_dict: dict, month: int, year: int, currency: str = "€", salary_total: float = 0.0) -> str:
    """Format statistics into a beautiful message.
    
    Args:
        stats: Statistics dictionary from calculate_statistics()
        categories_dict: Dictionary mapping category_id to category name
        month: Month number (1-12)
        year: Year number
        currency: User's currency symbol
        salary_total: Total salary for the period
        
    Returns:
        Formatted message string
    """
    has_expenses = stats["total"] > 0
    has_salary = salary_total > 0

    if not has_expenses and not has_salary:
        return f"📊 Statistics for {month:02d}/{year}\n\n" \
               f"💭 No data found for this period.\n" \
               f"Start tracking your spending!"
    
    message = f"📊 Statistics for {month:02d}/{year}\n\n"

    if has_salary:
        message += f"💼 Salary: {currency}{salary_total:.2f}\n"

    if has_expenses:
        message += f"💸 Expenses: {currency}{stats['total']:.2f}\n"
        message += f"📝 Transactions: {stats['count']}\n"

    if has_salary or has_expenses:
        balance = salary_total - stats["total"]
        if balance >= 0:
            message += f"\n🟢 Balance: +{currency}{balance:.2f}\n"
        else:
            message += f"\n🔴 Balance: -{currency}{abs(balance):.2f}\n"
    
    if has_expenses and stats['by_category']:
        message += f"\n📂 By Category:\n"
        for category_id, amount in stats['by_category'].items():
            category_name = categories_dict.get(category_id, 'Unknown')
            percentage = (amount / stats['total']) * 100
            message += f"├ {category_name}: {currency}{amount:.2f} ({percentage:.1f}%)\n"
    
    return message


async def fetch_and_display_statistics(message_or_callback, telegram_id: int, month: int, year: int):
    """Fetch expenses and display statistics for given period.
    
    Args:
        message_or_callback: Message or CallbackQuery object
        telegram_id: User's telegram ID
        month: Month number (1-12)
        year: Year number
    """
    # Fetch user to get currency
    user_response = await api_client.get_user(telegram_id)
    currency = "€"  # Default currency
    if user_response.status_code == 200:
        user_data = user_response.json()
        currency = user_data.get("currency", "€")
    
    # Fetch all expenses for the period (use large per_page to get all)
    response = await api_client.get_expenses_for_month(
        telegram_id=telegram_id,
        year=year,
        month=month,
        page=1,
        per_page=1000
    )
    
    if response.status_code != 200 and response.status_code != 404:
        logger.error(f"Failed to get expenses: status={response.status_code}")
        error_msg = "❌ Error loading statistics. Please try again later."
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(error_msg)
        else:
            await message_or_callback.answer(error_msg)
        return
    
    expenses = response.json() if response.status_code == 200 else []

    # Fetch all salaries for the period
    salary_response = await api_client.get_salaries_for_month(
        telegram_id=telegram_id,
        year=year,
        month=month,
        page=1,
        per_page=1000,
    )
    salaries = salary_response.json() if salary_response.status_code == 200 else []
    salary_total = sum(s['amount'] for s in salaries)
    
    # Fetch categories for display
    categories_response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=100)
    
    if categories_response.status_code == 200:
        categories = categories_response.json()
    elif categories_response.status_code == 404:
        categories = []
    else:
        logger.error(f"Failed to get categories: status={categories_response.status_code}")
        categories = []
    
    categories_dict = {cat['id']: cat['title'] for cat in categories}
    
    # Calculate and format statistics
    stats = calculate_statistics(expenses)
    message_text = format_statistics_message(stats, categories_dict, month, year, currency, salary_total)
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(message_text)
    else:
        await message_or_callback.answer(message_text)


@router.message(F.text == "📊 Statistics")
async def show_statistics_menu(message: Message):
    """Show statistics period selection menu."""
    await message.answer(
        "📊 Statistics\n\nSelect a period to view your expense statistics:",
        reply_markup=get_statistics_menu()
    )


@router.callback_query(F.data == "stats_current_month")
async def show_current_month_statistics(callback: CallbackQuery):
    """Show statistics for current month."""
    now = datetime.now()
    telegram_id = callback.from_user.id
    
    await fetch_and_display_statistics(callback, telegram_id, now.month, now.year)
    await callback.answer()


@router.callback_query(F.data == "stats_previous_month")
async def show_previous_month_statistics(callback: CallbackQuery):
    """Show statistics for previous month."""
    now = datetime.now()
    telegram_id = callback.from_user.id
    
    # Calculate previous month (handle year transition)
    if now.month == 1:
        prev_month = 12
        prev_year = now.year - 1
    else:
        prev_month = now.month - 1
        prev_year = now.year
    
    await fetch_and_display_statistics(callback, telegram_id, prev_month, prev_year)
    await callback.answer()


@router.callback_query(F.data == "stats_custom")
async def start_custom_statistics(callback: CallbackQuery, state: FSMContext):
    """Start custom statistics flow - ask for month."""
    await callback.message.answer(
        "📅 Enter the month number (1-12):\n\n"
        "For example:\n"
        "• 1 for January\n"
        "• 2 for February\n"
        "• 12 for December",
        reply_markup=get_custom_stats_back_keyboard()
    )
    await state.set_state(StatisticsStates.waiting_for_month)
    await callback.answer()


@router.callback_query(F.data == "stats_back")
async def back_to_statistics(callback: CallbackQuery, state: FSMContext):
    """Cancel custom stats and go back to menu."""
    await state.clear()
    await callback.message.edit_text(
        "📊 Statistics\n\nSelect a period to view your expense statistics:",
        reply_markup=get_statistics_menu()
    )
    await callback.answer()


@router.message(StatisticsStates.waiting_for_month)
async def process_month_input(message: Message, state: FSMContext):
    """Process month input for custom statistics."""
    try:
        month = int(message.text.strip())
        
        if month < 1 or month > 12:
            await message.answer(
                "❌ Invalid month. Please enter a number between 1 and 12:",
                reply_markup=get_custom_stats_back_keyboard()
            )
            return
        
        await state.update_data(month=month)
        await message.answer(
            "📅 Now enter the year (e.g., 2026):",
            reply_markup=get_custom_stats_back_keyboard()
        )
        await state.set_state(StatisticsStates.waiting_for_year)
        
    except ValueError:
        await message.answer(
            "❌ Invalid input. Please enter a number (1-12):",
            reply_markup=get_custom_stats_back_keyboard()
        )


@router.message(StatisticsStates.waiting_for_year)
async def process_year_input(message: Message, state: FSMContext):
    """Process year input and display statistics."""
    try:
        year = int(message.text.strip())
        
        if year < 2020 or year > 2030:
            await message.answer(
                "❌ Invalid year. Please enter a year between 2020 and 2030:",
                reply_markup=get_custom_stats_back_keyboard()
            )
            return
        
        data = await state.get_data()
        month = data.get("month")
        telegram_id = message.from_user.id
        
        await fetch_and_display_statistics(message, telegram_id, month, year)
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ Invalid input. Please enter a valid year (e.g., 2026):",
            reply_markup=get_custom_stats_back_keyboard()
        )
