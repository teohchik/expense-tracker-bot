"""Main entry point for Expense Tracker Telegram Bot."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from config import settings
from bot.handlers.start import router as start_router
from bot.handlers.categories import router as categories_router
from bot.handlers.expenses import router as expenses_router
from bot.handlers.statistics import router as statistics_router
from bot.handlers.profile import router as profile_router
from bot.handlers.admin import router as admin_router
from bot.handlers.salary import router as salary_router


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    # Initialize Redis storage for FSM
    storage = RedisStorage.from_url(settings.redis_url)
    
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)

    # Register routers
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(categories_router)
    dp.include_router(expenses_router)
    dp.include_router(statistics_router)
    dp.include_router(profile_router)
    dp.include_router(salary_router)

    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text="🤖 Bot successfully started!"
        )
        logger.info("Bot started, admin notified")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    try:
        await dp.start_polling(bot)
    finally:
        # Close Redis connection on shutdown
        await storage.close()
        logger.info("Redis connection closed")


if __name__ == '__main__':
    asyncio.run(main())
