"""FSM states for salary management."""
from aiogram.fsm.state import State, StatesGroup


class AddSalaryStates(StatesGroup):
    """States for adding a new salary."""
    waiting_for_amount = State()
    waiting_for_description = State()


class EditSalaryStates(StatesGroup):
    """States for editing a salary."""
    waiting_for_new_amount = State()
    waiting_for_new_description = State()
