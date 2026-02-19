"""Salary handler."""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.salary import (
    get_salary_menu,
    get_salaries_list,
    get_salary_actions,
    get_no_salaries_keyboard,
)
from bot.states.salary import AddSalaryStates, EditSalaryStates
from api.client import api_client
from config import bot_settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "💰 Salary")
async def show_salary_menu(message: Message):
    """Show salary management menu."""
    await message.answer(
        "💰 Salary Management\n\nChoose an action:",
        reply_markup=get_salary_menu()
    )


@router.callback_query(F.data == "salary_create")
async def start_add_salary(callback: CallbackQuery, state: FSMContext):
    """Start adding a new salary entry."""
    await callback.message.answer("💵 Enter salary amount:")
    await state.set_state(AddSalaryStates.waiting_for_amount)
    await callback.answer()


@router.message(AddSalaryStates.waiting_for_amount)
async def process_salary_amount(message: Message, state: FSMContext):
    """Process salary amount input."""
    try:
        amount = float(message.text.strip().replace(',', '.'))
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number:")
        return

    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Please try again:")
        return

    if amount > 1_000_000:
        await message.answer("❌ Amount is too large (max 1,000,000). Please try again:")
        return

    await state.update_data(amount=amount)
    await message.answer("📝 Enter description (optional):\n\nSend /skip to skip.")
    await state.set_state(AddSalaryStates.waiting_for_description)


@router.message(AddSalaryStates.waiting_for_description, F.text == "/skip")
async def skip_salary_description(message: Message, state: FSMContext):
    """Skip description and create salary."""
    await create_salary_from_state(message, state, description=None)


@router.message(AddSalaryStates.waiting_for_description)
async def process_salary_description(message: Message, state: FSMContext):
    """Process salary description."""
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("❌ Description is too long (max 500 characters). Please try again:")
        return
    await create_salary_from_state(message, state, description=description)


async def create_salary_from_state(message: Message, state: FSMContext, description: str = None):
    """Create salary from FSM state data."""
    data = await state.get_data()
    amount = data.get("amount")
    telegram_id = message.from_user.id

    user_response = await api_client.get_user(telegram_id)
    currency = "€"
    if user_response.status_code == 200:
        currency = user_response.json().get("currency", "€")

    response = await api_client.create_salary(
        telegram_id=telegram_id,
        amount=amount,
        description=description,
    )

    if response.status_code == 201:
        logger.info(f"Salary created: telegram_id={telegram_id}, amount={amount}")
        text = f"✅ Salary added!\n\n💰 Amount: {currency}{amount:.2f}"
        if description:
            text += f"\n📝 {description}"
        await message.answer(text)
    else:
        logger.error(f"Failed to create salary: status={response.status_code}")
        await message.answer("❌ An error occurred. Please try again later.")

    await state.clear()


@router.callback_query(F.data == "salary_view")
async def view_salaries(callback: CallbackQuery):
    """Show current month salaries."""
    telegram_id = callback.from_user.id
    now = datetime.now()
    per_page = bot_settings.EXPENSES_PER_PAGE

    user_response = await api_client.get_user(telegram_id)
    currency = "€"
    if user_response.status_code == 200:
        currency = user_response.json().get("currency", "€")

    response = await api_client.get_salaries_for_month(
        telegram_id=telegram_id,
        year=now.year,
        month=now.month,
        page=1,
        per_page=per_page,
    )

    if response.status_code == 200:
        salaries = response.json()
        if salaries:
            await callback.message.edit_text(
                f"📊 Salaries for {now.month}/{now.year}\n\nSelect an entry:",
                reply_markup=get_salaries_list(salaries, page=1, per_page=per_page, currency=currency)
            )
        else:
            await callback.message.edit_text(
                f"📊 No salary entries for {now.month}/{now.year}\n\n"
                "💡 Add your first salary entry!",
                reply_markup=get_no_salaries_keyboard()
            )
    else:
        logger.error(f"Failed to get salaries: status={response.status_code}")
        await callback.answer("❌ Error loading salaries", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("sal_page:"))
async def paginate_salaries(callback: CallbackQuery):
    """Handle salary list pagination."""
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    now = datetime.now()
    per_page = bot_settings.EXPENSES_PER_PAGE

    user_response = await api_client.get_user(telegram_id)
    currency = "€"
    if user_response.status_code == 200:
        currency = user_response.json().get("currency", "€")

    response = await api_client.get_salaries_for_month(
        telegram_id=telegram_id,
        year=now.year,
        month=now.month,
        page=page,
        per_page=per_page,
    )

    if response.status_code == 200:
        salaries = response.json()
        await callback.message.edit_reply_markup(
            reply_markup=get_salaries_list(salaries, page=page, per_page=per_page, currency=currency)
        )
    else:
        logger.error(f"Failed to get salaries: status={response.status_code}")
        await callback.answer("❌ Error loading salaries", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("sal_select:"))
async def select_salary(callback: CallbackQuery):
    """Show actions for selected salary entry."""
    salary_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "🔧 Salary Actions\n\nWhat would you like to do?",
        reply_markup=get_salary_actions(salary_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sal_edit_amount:"))
async def start_edit_salary_amount(callback: CallbackQuery, state: FSMContext):
    """Start editing salary amount."""
    salary_id = int(callback.data.split(":")[1])
    await state.update_data(salary_id=salary_id)
    await state.set_state(EditSalaryStates.waiting_for_new_amount)
    await callback.message.answer("💵 Enter new amount:")
    await callback.answer()


@router.message(EditSalaryStates.waiting_for_new_amount)
async def process_new_salary_amount(message: Message, state: FSMContext):
    """Process new salary amount."""
    try:
        amount = float(message.text.strip().replace(',', '.'))
    except ValueError:
        await message.answer("❌ Invalid amount. Please enter a number:")
        return

    if amount <= 0:
        await message.answer("❌ Amount must be greater than 0. Please try again:")
        return

    if amount > 1_000_000:
        await message.answer("❌ Amount is too large (max 1,000,000). Please try again:")
        return

    data = await state.get_data()
    salary_id = data.get("salary_id")
    telegram_id = message.from_user.id

    user_response = await api_client.get_user(telegram_id)
    currency = "€"
    if user_response.status_code == 200:
        currency = user_response.json().get("currency", "€")

    response = await api_client.update_salary(salary_id=salary_id, amount=amount)

    if response.status_code == 200:
        salary_data = response.json()
        updated_amount = salary_data.get("amount", amount)
        text = f"✅ Salary updated!\n\n💰 Amount: {currency}{updated_amount:.2f}"
        if salary_data.get("description"):
            text += f"\n📝 {salary_data['description']}"
        await message.answer(text)
    else:
        logger.error(f"Failed to update salary amount: status={response.status_code}")
        await message.answer("❌ An error occurred. Please try again later.")

    await state.clear()


@router.callback_query(F.data.startswith("sal_edit_desc:"))
async def start_edit_salary_description(callback: CallbackQuery, state: FSMContext):
    """Start editing salary description."""
    salary_id = int(callback.data.split(":")[1])
    await state.update_data(salary_id=salary_id)
    await state.set_state(EditSalaryStates.waiting_for_new_description)
    await callback.message.answer("📝 Enter new description:")
    await callback.answer()


@router.message(EditSalaryStates.waiting_for_new_description)
async def process_new_salary_description(message: Message, state: FSMContext):
    """Process new salary description."""
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("❌ Description is too long (max 500 characters). Please try again:")
        return

    data = await state.get_data()
    salary_id = data.get("salary_id")
    telegram_id = message.from_user.id

    user_response = await api_client.get_user(telegram_id)
    currency = "€"
    if user_response.status_code == 200:
        currency = user_response.json().get("currency", "€")

    response = await api_client.update_salary(salary_id=salary_id, description=description)

    if response.status_code == 200:
        salary_data = response.json()
        amount = salary_data.get("amount", 0)
        text = f"✅ Salary updated!\n\n💰 Amount: {currency}{amount:.2f}\n📝 {salary_data.get('description', description)}"
        await message.answer(text)
    else:
        logger.error(f"Failed to update salary description: status={response.status_code}")
        await message.answer("❌ An error occurred. Please try again later.")

    await state.clear()


@router.callback_query(F.data.startswith("sal_delete:"))
async def delete_salary(callback: CallbackQuery):
    """Delete salary entry."""
    salary_id = int(callback.data.split(":")[1])

    response = await api_client.delete_salary(salary_id=salary_id)

    if response.status_code == 204:
        logger.info(f"Salary deleted: salary_id={salary_id}")
        await callback.answer("✅ Salary deleted!", show_alert=True)
        await callback.message.edit_text("✅ Salary entry deleted!")
    else:
        logger.error(f"Failed to delete salary: status={response.status_code}")
        await callback.answer("❌ An error occurred", show_alert=True)


@router.callback_query(F.data == "salary_back")
async def back_to_salary_menu(callback: CallbackQuery):
    """Return to salary menu."""
    await callback.message.edit_text(
        "💰 Salary Management\n\nChoose an action:",
        reply_markup=get_salary_menu()
    )
    await callback.answer()
