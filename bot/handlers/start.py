"""Start command handler."""
from datetime import datetime
from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

from api.client import api_client
from bot.keyboards.main_menu import get_main_menu
from config import settings

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
        
        # Notify admin about new user
        bot = Bot(token=settings.bot_token)
        try:
            admin_message = (
                f"🆕 New User Registered!\n\n"
                f"👤 Name: {first_name}"
            )
            if last_name:
                admin_message += f" {last_name}"
            admin_message += f"\n🆔 Telegram ID: {telegram_id}\n"
            if username:
                admin_message += f"📝 Username: @{username}\n"
            admin_message += f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await bot.send_message(chat_id=settings.admin_id, text=admin_message)
        except Exception as e:
            # Don't fail user registration if admin notification fails
            print(f"Failed to notify admin: {e}")
        finally:
            await bot.session.close()
        
        await message.answer(
            f"Hello, {first_name}! 🎉\n\n"
            "Welcome to Expense Tracker Bot! 💰\n\n"
            "This bot helps you:\n"
            "✅ Track your daily expenses\n"
            "✅ Organize spending by categories\n"
            "✅ View your expense history\n"
            "✅ Manage your budget\n\n"
            "Let's get started! First, create a category to organize your expenses.\n\n"
            "💡 Examples: Food 🍔, Transport 🚗, Shopping 🛍, Entertainment 🎮",
            reply_markup=get_main_menu()
        )
    
    else:
        await message.answer("An error occurred. Please try again later.")
