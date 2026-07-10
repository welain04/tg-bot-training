from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.keyboards.main_menu import main_menu_keyboard
from bot.messages.templates import SESSION_EXPIRED_TEXT, get_main_menu_text
from bot.states.booking import BookingStates
from config.settings import settings

SESSION_UPDATED_AT_KEY = "session_updated_at"

BOOKING_STATES = {
    BookingStates.select_service.state,
    BookingStates.ai_pick_service.state,
    BookingStates.select_doctor.state,
    BookingStates.select_date.state,
    BookingStates.select_time.state,
    BookingStates.input_name.state,
    BookingStates.input_phone.state,
    BookingStates.confirm.state,
}


class FsmTimeoutMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext | None = data.get("state")
        if state is not None:
            current_state = await state.get_state()
            if current_state in BOOKING_STATES and await self._is_expired(state):
                await state.clear()
                await self._notify_expired(event)
                return None

        result = await handler(event, data)

        if state is not None:
            current_state = await state.get_state()
            if current_state in BOOKING_STATES:
                await state.update_data(
                    **{SESSION_UPDATED_AT_KEY: datetime.now().isoformat(timespec="seconds")}
                )

        return result

    async def _is_expired(self, state: FSMContext) -> bool:
        state_data = await state.get_data()
        updated_raw = state_data.get(SESSION_UPDATED_AT_KEY)
        if not updated_raw:
            return False

        updated_at = datetime.fromisoformat(updated_raw)
        timeout = timedelta(minutes=settings.fsm_timeout_minutes)
        return datetime.now() - updated_at > timeout

    @staticmethod
    async def _notify_expired(event: TelegramObject) -> None:
        keyboard = main_menu_keyboard()
        text = f"{SESSION_EXPIRED_TEXT}\n\n{get_main_menu_text()}"

        if isinstance(event, CallbackQuery):
            await event.answer("Сессия истекла", show_alert=True)
            if event.message:
                await event.message.edit_text(text, reply_markup=keyboard)
            return

        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
