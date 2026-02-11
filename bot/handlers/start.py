"""Start command handler."""
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from api.client import api_client
from bot.keyboards.main_menu import get_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user = message.from_user
    telegram_id = user.id
    username = user.username
    first_name = user.first_name or "User"
    last_name = user.last_name

    response = await api_client.get_user(telegram_id)
    
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data.get("id")
        needs_update = (
            user_data.get("username") != username or
            user_data.get("first_name") != first_name or
            user_data.get("last_name") != last_name
        )
        
        if needs_update:
            await api_client.update_user(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
        
        await message.answer(
            f"Welcome back, {first_name}! 👋",
            reply_markup=get_main_menu()
        )
    
    elif response.status_code == 404:
        await api_client.create_user(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        await message.answer(
            f"Hello, {first_name}! 🎉\nWelcome to Expense Tracker Bot!",
            reply_markup=get_main_menu()
        )
    
    else:
        await message.answer("An error occurred. Please try again later.")
