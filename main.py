"""Main entry point for Expense Tracker Telegram Bot."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import settings
from bot.handlers.start import router as start_router
from bot.handlers.categories import router as categories_router
from bot.handlers.expenses import router as expenses_router


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(categories_router)
    dp.include_router(expenses_router)

    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text="🤖 Bot successfully started!"
        )
        logger.info("Bot started, admin notified")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
