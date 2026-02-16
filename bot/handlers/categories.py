"""Categories handler."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.categories import get_categories_menu, get_categories_list, get_category_actions, get_empty_categories_keyboard
from bot.states.category import AddCategoryStates, EditCategoryStates
from api.client import api_client
from config import bot_settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "📂 Categories")
async def show_categories_menu(message: Message):
    """Show categories management menu."""
    telegram_id = message.from_user.id
    
    # Check if user has any categories
    response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=1)
    
    if response.status_code == 200:
        categories = response.json()
    elif response.status_code == 404:
        categories = []  # No categories yet
    else:
        logger.error(f"Failed to get categories: status={response.status_code}, telegram_id={telegram_id}")
        await message.answer("❌ Error loading categories. Please try again later.")
        return
    
    if categories:
        # User has categories - show normal menu
        await message.answer(
            "📂 Categories Management\n\nChoose an action:",
            reply_markup=get_categories_menu()
        )
    else:
        # No categories - show welcome message
        await message.answer(
            "📂 Welcome to Categories!\n\n"
            "Categories help you organize and track your expenses by type.\n\n"
            "Create categories for different types of spending:\n"
            "🍔 Food - restaurants, groceries\n"
            "🚗 Transport - gas, taxi, public transport\n"
            "🛍 Shopping - clothes, electronics\n"
            "🎮 Entertainment - movies, games, hobbies\n"
            "🏠 Bills - rent, utilities\n\n"
            "Let's create your first category!",
            reply_markup=get_empty_categories_keyboard()
        )


@router.callback_query(F.data == "category_add")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """Start adding a new category."""
    await callback.message.answer("📝 Enter category title:")
    await state.set_state(AddCategoryStates.waiting_for_title)
    await callback.answer()


@router.message(AddCategoryStates.waiting_for_title)
async def process_category_title(message: Message, state: FSMContext):
    """Process category title and save to database."""
    title = message.text.strip()
    telegram_id = message.from_user.id
    
    if not title:
        await message.answer("❌ Title cannot be empty. Please try again:")
        return
    
    if len(title) > 100:
        await message.answer("❌ Title is too long (max 100 characters). Please try again:")
        return
    
    logger.info(f"Creating category: telegram_id={telegram_id}, title={title}")
    
    response = await api_client.create_category(title=title, telegram_id=telegram_id)
    
    if response.status_code == 201:
        category_data = response.json()
        logger.info(f"Category created successfully: id={category_data.get('id')}, title={title}")
        await message.answer(f"✅ Category '{title}' created successfully!")
        await state.clear()
    else:
        logger.error(f"Unexpected error creating category: status={response.status_code}, telegram_id={telegram_id}")
        await message.answer("❌ An error occurred. Please try again later.")
        await state.clear()


@router.callback_query(F.data == "category_edit")
async def show_categories_list(callback: CallbackQuery):
    """Show list of categories for editing."""
    telegram_id = callback.from_user.id
    per_page = bot_settings.CATEGORIES_PER_PAGE
    
    response = await api_client.get_categories(telegram_id=telegram_id, page=1, per_page=per_page)
    
    if response.status_code == 200:
        categories = response.json()
    elif response.status_code == 404:
        categories = []  # No categories yet
    else:
        logger.error(f"Failed to get categories: status={response.status_code}, telegram_id={telegram_id}")
        await callback.answer("❌ Error loading categories", show_alert=True)
        return
    
    if categories:
        await callback.message.edit_text(
            "📂 Select a category to edit:",
            reply_markup=get_categories_list(categories, page=1, per_page=per_page)
        )
    else:
        await callback.message.edit_text(
            "📂 You don't have any categories yet!\n\n"
            "Categories help you organize your expenses.\n"
            "Create your first category to get started!\n\n"
            "💡 Examples: Food, Transport, Shopping, Entertainment",
            reply_markup=get_empty_categories_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("cat_page:"))
async def paginate_categories(callback: CallbackQuery):
    """Handle category pagination."""
    page = int(callback.data.split(":")[1])
    telegram_id = callback.from_user.id
    per_page = bot_settings.CATEGORIES_PER_PAGE
    
    response = await api_client.get_categories(telegram_id=telegram_id, page=page, per_page=per_page)
    
    if response.status_code == 200:
        categories = response.json()
        await callback.message.edit_reply_markup(
            reply_markup=get_categories_list(categories, page=page, per_page=per_page)
        )
    else:
        logger.error(f"Failed to get categories: status={response.status_code}, telegram_id={telegram_id}")
        await callback.answer("❌ Error loading categories", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("cat_select:"))
async def select_category(callback: CallbackQuery):
    """Show actions for selected category."""
    category_id = int(callback.data.split(":")[1])
    
    await callback.message.edit_text(
        f"🔧 Category Actions\n\nWhat would you like to do?",
        reply_markup=get_category_actions(category_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat_rename:"))
async def start_rename_category(callback: CallbackQuery, state: FSMContext):
    """Start renaming a category."""
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(EditCategoryStates.waiting_for_new_title)
    await callback.message.answer("📝 Enter new category title:")
    await callback.answer()


@router.message(EditCategoryStates.waiting_for_new_title)
async def process_rename_category(message: Message, state: FSMContext):
    """Process category renaming."""
    new_title = message.text.strip()
    
    if not new_title:
        await message.answer("❌ Title cannot be empty. Please try again:")
        return
    
    if len(new_title) > 100:
        await message.answer("❌ Title is too long (max 100 characters). Please try again:")
        return
    
    data = await state.get_data()
    category_id = data.get("category_id")
    
    logger.info(f"Renaming category: category_id={category_id}, new_title={new_title}")
    
    response = await api_client.update_category(category_id=category_id, title=new_title)
    
    if response.status_code == 200:
        category_data = response.json()
        logger.info(f"Category renamed successfully: category_id={category_id}, new_title={new_title}")
        
        # Show updated category data
        updated_title = category_data.get('title', new_title)

        message_text = f"✅ Category updated!\n\n"
        message_text += f"📂 Title: {updated_title}\n"

        await message.answer(message_text)
        await state.clear()
    elif response.status_code == 404:
        logger.warning(f"Category not found: category_id={category_id}")
        await message.answer("❌ Category not found!")
        await state.clear()
    else:
        logger.error(f"Unexpected error renaming category: status={response.status_code}, category_id={category_id}")
        await message.answer("❌ An error occurred. Please try again later.")
        await state.clear()


@router.callback_query(F.data.startswith("cat_toggle:"))
async def delete_category(callback: CallbackQuery):
    """Delete category."""
    category_id = int(callback.data.split(":")[1])
    
    logger.info(f"Deleting category: category_id={category_id}")
    
    response = await api_client.delete_category(category_id=category_id)
    
    if response.status_code == 200:
        logger.info(f"Category deleted: category_id={category_id}")
        await callback.answer("✅ Category deleted!", show_alert=True)
        await callback.message.edit_text("✅ Category deleted!")
    elif response.status_code == 404:
        logger.warning(f"Category not found: category_id={category_id}")
        await callback.answer("❌ Category not found!", show_alert=True)
    else:
        logger.error(f"Unexpected error deleting category: status={response.status_code}, category_id={category_id}")
        await callback.answer("❌ An error occurred", show_alert=True)


@router.callback_query(F.data == "cat_back")
async def back_to_menu(callback: CallbackQuery):
    """Return to categories menu."""
    await callback.message.edit_text(
        "📂 Categories Management\n\nChoose an action:",
        reply_markup=get_categories_menu()
    )
    await callback.answer()
