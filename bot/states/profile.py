"""Profile states."""
from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """States for profile management."""
    waiting_for_custom_currency = State()
