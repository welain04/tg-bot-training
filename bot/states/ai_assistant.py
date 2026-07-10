from aiogram.fsm.state import State, StatesGroup


class AiAssistantStates(StatesGroup):
    chatting = State()
