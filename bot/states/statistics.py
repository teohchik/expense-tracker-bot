"""Statistics FSM states."""
from aiogram.fsm.state import State, StatesGroup


class StatisticsStates(StatesGroup):
    """States for custom statistics flow."""
    waiting_for_month = State()
    waiting_for_year = State()
