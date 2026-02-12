"""FSM states for expense management."""
from aiogram.fsm.state import State, StatesGroup


class AddExpenseStates(StatesGroup):
    """States for adding a new expense."""
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()


class EditExpenseStates(StatesGroup):
    """States for editing an expense."""
    waiting_for_new_amount = State()
    waiting_for_new_description = State()
