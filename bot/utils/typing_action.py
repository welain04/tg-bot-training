import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from aiogram import Bot
from aiogram.enums import ChatAction

T = TypeVar("T")


async def with_typing(bot: Bot, chat_id: int, coro: Awaitable[T]) -> T:
    stop = asyncio.Event()

    async def keep_typing() -> None:
        while not stop.is_set():
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            try:
                await asyncio.wait_for(stop.wait(), timeout=4.0)
            except TimeoutError:
                continue

    task = asyncio.create_task(keep_typing())
    try:
        return await coro
    finally:
        stop.set()
        await task
