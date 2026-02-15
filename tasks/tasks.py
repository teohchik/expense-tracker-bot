import asyncio
import logging
from datetime import date, datetime
from collections import defaultdict
from calendar import monthrange

from aiogram import Bot
from tasks.celery_app import celery_inst
from config import settings
from api.client import api_client

logger = logging.getLogger(__name__)


# Helper to run async functions from Celery
def run_async(coroutine):
    """Helper to run async coroutines from sync Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()


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


def format_statistics_message(stats: dict, categories_dict: dict, month: int, year: int, currency: str = "€") -> str:
    """Format statistics into a beautiful message.
    
    Args:
        stats: Statistics dictionary from calculate_statistics()
        categories_dict: Dictionary mapping category_id to category name
        month: Month number (1-12)
        year: Year number
        currency: User's currency symbol
        
    Returns:
        Formatted message string
    """
    if stats["total"] == 0:
        return f"📊 Statistics for {month:02d}/{year}\n\n" \
               f"💭 No expenses found for this period.\n" \
               f"Start tracking your spending!"
    
    message = f"📊 Statistics for {month:02d}/{year}\n\n"
    message += f"💰 Total: {currency}{stats['total']:.2f}\n"
    message += f"📝 Number of expenses: {stats['count']}\n"
    
    if stats['by_category']:
        message += f"\n📂 By Category:\n"
        for category_id, amount in stats['by_category'].items():
            category_name = categories_dict.get(category_id, 'Unknown')
            percentage = (amount / stats['total']) * 100
            message += f"├ {category_name}: {currency}{amount:.2f} ({percentage:.1f}%)\n"
    
    return message


async def send_monthly_stats_to_all_users():
    """Send monthly statistics to all users for previous month."""
    bot = Bot(token=settings.bot_token)
    
    try:
        # Get previous month
        now = datetime.now()
        if now.month == 1:
            prev_month = 12
            prev_year = now.year - 1
        else:
            prev_month = now.month - 1
            prev_year = now.year
        
        # Get all users
        users = await api_client.get_all_users()
        logger.info(f"Starting monthly stats broadcast to {len(users)} users for {prev_month:02d}/{prev_year}")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                telegram_id = user['telegram_id']
                currency = user.get('currency', '€')
                
                # Fetch expenses for previous month
                response = await api_client.get_expenses_for_month(
                    telegram_id=telegram_id,
                    year=prev_year,
                    month=prev_month,
                    page=1,
                    per_page=1000
                )
                
                expenses = response.json() if response.status_code == 200 else []
                
                # Fetch categories
                categories_response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=100)
                categories = categories_response.json() if categories_response.status_code == 200 else []
                categories_dict = {cat['id']: cat['title'] for cat in categories}
                
                # Calculate and format statistics
                stats = calculate_statistics(expenses)
                message_text = format_statistics_message(stats, categories_dict, prev_month, prev_year, currency)
                
                # Send message
                await bot.send_message(chat_id=telegram_id, text=message_text)
                success_count += 1
                logger.info(f"Sent monthly stats to user {telegram_id}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send monthly stats to user {user.get('telegram_id', 'unknown')}: {e}")
        
        logger.info(f"Monthly stats broadcast completed: {success_count} successful, {error_count} errors")
        
    finally:
        await bot.session.close()


async def send_new_month_reminder_to_all_users(force: bool = False):
    """Send reminder about new month tomorrow to all users.
    
    Args:
        force: If True, skip the last-day-of-month check (for testing)
    """
    bot = Bot(token=settings.bot_token)
    
    try:
        today = date.today()
        
        # Check if tomorrow is the first day of a new month
        # Get the last day of current month
        last_day = monthrange(today.year, today.month)[1]
        
        if not force and today.day != last_day:
            logger.info(f"Today is not the last day of month ({today}), skipping reminder")
            return
        
        # Get all users
        users = await api_client.get_all_users()
        logger.info(f"Starting new month reminder broadcast to {len(users)} users")
        
        success_count = 0
        error_count = 0
        
        # Calculate next month for the message
        if today.month == 12:
            next_month_name = "January"
            next_year = today.year + 1
        else:
            next_month = today.month + 1
            month_names = ["January", "February", "March", "April", "May", "June",
                          "July", "August", "September", "October", "November", "December"]
            next_month_name = month_names[next_month - 1]
            next_year = today.year
        
        current_month_names = ["January", "February", "March", "April", "May", "June",
                              "July", "August", "September", "October", "November", "December"]
        current_month_name = current_month_names[today.month - 1]
        
        message_text = (
            f"📅 Last day of {current_month_name}!\n\n"
            f"🗓 Tomorrow starts {next_month_name} {next_year}.\n"
            f"⚠️ All your expenses are saved, but statistics will start fresh.\n\n"
            f"💡 Don't forget to check your statistics for the current month!"
        )
        
        for user in users:
            try:
                telegram_id = user['telegram_id']
                await bot.send_message(chat_id=telegram_id, text=message_text)
                success_count += 1
                logger.info(f"Sent new month reminder to user {telegram_id}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to send reminder to user {user.get('telegram_id', 'unknown')}: {e}")
        
        logger.info(f"New month reminder broadcast completed: {success_count} successful, {error_count} errors")
        
    finally:
        await bot.session.close()


# Celery tasks
@celery_inst.task(name="monthly_stats")
def monthly_stats_task():
    """Monthly statistics task that runs on 1st day of month."""
    logger.info("Starting monthly stats task")
    return run_async(send_monthly_stats_to_all_users())


@celery_inst.task(name="new_month_reminder")
def new_month_reminder_task(force: bool = False):
    """New month reminder task that checks if today is last day of month.
    
    Args:
        force: If True, send reminder regardless of date (for testing)
    """
    logger.info("Starting new month reminder task")
    return run_async(send_new_month_reminder_to_all_users(force=force))
