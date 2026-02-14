"""Profile handler."""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.profile import (
    get_profile_keyboard,
    get_currency_selection_keyboard,
    get_custom_currency_back_keyboard
)
from bot.states.profile import ProfileStates
from api.client import api_client

router = Router()
logger = logging.getLogger(__name__)


CURRENCY_MAP = {
    "EUR": "€",
    "UAH": "₴",
    "USD": "$",
}


def format_date(date_str: str) -> str:
    """Format date string to readable format."""
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%d.%m.%Y")
    except:
        return "N/A"


async def show_profile(message_or_callback, telegram_id: int):
    """Show user profile with statistics."""
    user_response = await api_client.get_user(telegram_id)
    
    if user_response.status_code != 200:
        error_msg = "❌ Error loading profile. Please try again later."
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.message.answer(error_msg)
        else:
            await message_or_callback.answer(error_msg)
        return
    
    user_data = user_response.json()
    
    # Format profile message
    first_name = user_data.get("first_name", "User")
    currency = user_data.get("currency", "€")
    created_at = user_data.get("created_at", "")
    join_date = format_date(created_at) if created_at else "N/A"
    
    profile_text = (
        f"👤 Profile: {first_name}\n\n"
        f"📊 Statistics:\n"
        f"├ Member since: {join_date}\n"
        f"└ Currency: {currency}\n"
    )
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(
            profile_text,
            reply_markup=get_profile_keyboard()
        )
    else:
        await message_or_callback.answer(
            profile_text,
            reply_markup=get_profile_keyboard()
        )


@router.message(F.text == "👤 Profile")
async def show_profile_handler(message: Message):
    """Handle Profile button press."""
    await show_profile(message, message.from_user.id)


@router.callback_query(F.data == "profile_change_currency")
async def change_currency_menu(callback: CallbackQuery):
    """Show currency selection menu."""
    await callback.message.answer(
        "💱 Select currency:\n\nChoose from preset options or enter custom currency symbol.",
        reply_markup=get_currency_selection_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("currency_"))
async def handle_currency_selection(callback: CallbackQuery, state: FSMContext):
    """Handle currency selection."""
    currency_code = callback.data.split("_")[1]
    telegram_id = callback.from_user.id
    
    if currency_code == "custom":
        await callback.message.answer(
            "✏️ Enter your custom currency symbol (up to 10 characters):",
            reply_markup=get_custom_currency_back_keyboard()
        )
        await state.set_state(ProfileStates.waiting_for_custom_currency)
        await callback.answer()
        return
    
    # Update currency with preset value
    currency_symbol = CURRENCY_MAP.get(currency_code, currency_code)
    
    response = await api_client.update_user_currency(telegram_id, currency_symbol)
    
    if response.status_code == 200:
        await callback.message.answer(
            f"✅ Currency changed to {currency_symbol}"
        )
        # Show updated profile
        await show_profile(callback, telegram_id)
    else:
        await callback.message.answer(
            "❌ Error updating currency. Please try again later."
        )
    
    await callback.answer()


@router.callback_query(F.data == "profile_back")
async def profile_back(callback: CallbackQuery, state: FSMContext):
    """Handle back button - return to profile."""
    await state.clear()
    await show_profile(callback, callback.from_user.id)
    await callback.answer()


@router.message(ProfileStates.waiting_for_custom_currency)
async def process_custom_currency(message: Message, state: FSMContext):
    """Process custom currency input."""
    custom_currency = message.text.strip()
    telegram_id = message.from_user.id
    
    # Validate input
    if not custom_currency:
        await message.answer(
            "❌ Currency cannot be empty. Please enter a valid currency symbol:",
            reply_markup=get_custom_currency_back_keyboard()
        )
        return
    
    if len(custom_currency) > 10:
        await message.answer(
            "❌ Currency is too long. Please enter up to 10 characters:",
            reply_markup=get_custom_currency_back_keyboard()
        )
        return
    
    # Update currency
    response = await api_client.update_user_currency(telegram_id, custom_currency)
    
    if response.status_code == 200:
        await message.answer(
            f"✅ Currency changed to {custom_currency}"
        )
        await state.clear()
        # Show updated profile
        await show_profile(message, telegram_id)
    else:
        await message.answer(
            "❌ Error updating currency. Please try again later."
        )
        await state.clear()
