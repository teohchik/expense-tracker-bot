"""Admin command handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from config import settings
from tasks.tasks import broadcast_task

router = Router()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id == settings.admin_id


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Handle /broadcast command - send message to all users."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ You don't have permission to use this command.")
        return
    
    # Extract message text after /broadcast command
    broadcast_text = message.text.replace("/broadcast", "", 1).strip()
    
    if not broadcast_text:
        await message.answer(
            "📢 Broadcast Command\n\n"
            "Usage: /broadcast <message>\n\n"
            "Example:\n"
            "/broadcast Hello everyone! 👋"
        )
        return
    
    # Start broadcast task
    await message.answer("📤 Starting broadcast...\nYou will receive a report when it's done.")
    
    # Run broadcast in Celery (async)
    broadcast_task.delay(broadcast_text, message.from_user.id)
