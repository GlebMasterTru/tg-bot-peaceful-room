from aiogram.fsm.state import State, StatesGroup

class BroadcastStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_confirmation = State()