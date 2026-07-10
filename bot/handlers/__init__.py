from aiogram import Router

from bot.handlers.ai_assistant import router as ai_assistant_router
from bot.handlers.booking import router as booking_router
from bot.handlers.start import router as start_router


def setup_routers() -> Router:
    root = Router()
    root.include_router(booking_router)
    root.include_router(ai_assistant_router)
    root.include_router(start_router)
    return root
