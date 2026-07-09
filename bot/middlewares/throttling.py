import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject

from config.settings import settings

logger = logging.getLogger(__name__)


class CallbackThrottlingMiddleware(BaseMiddleware):
    def __init__(self, throttle_seconds: float | None = None) -> None:
        self._throttle_seconds = throttle_seconds or settings.callback_throttle_seconds
        self._last_click: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, CallbackQuery) or event.from_user is None:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        last = self._last_click.get(user_id, 0.0)

        if now - last < self._throttle_seconds:
            await event.answer("Подождите секунду...")
            return None

        self._last_click[user_id] = now
        return await handler(event, data)
