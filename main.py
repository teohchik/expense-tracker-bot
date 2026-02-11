"""Main entry point for Expense Tracker Telegram Bot."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import settings


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
