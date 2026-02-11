"""FSM states for category management."""
from aiogram.fsm.state import State, StatesGroup


class AddCategoryStates(StatesGroup):
    """States for adding a new category."""
    waiting_for_title = State()


class EditCategoryStates(StatesGroup):
    """States for editing a category."""
    waiting_for_new_title = State()
