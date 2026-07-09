from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    select_service = State()
    select_doctor = State()
    select_date = State()
    select_time = State()
    input_name = State()
    input_phone = State()
    confirm = State()
