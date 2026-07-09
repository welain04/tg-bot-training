import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from bot.handlers import setup_routers
from bot.middlewares.fsm_timeout import FsmTimeoutMiddleware
from bot.middlewares.throttling import CallbackThrottlingMiddleware
from config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    storage = MemoryStorage()
    if settings.redis_url:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            from redis.asyncio import Redis

            redis = Redis.from_url(settings.redis_url)
            storage = RedisStorage(redis=redis)
            logger.info("Using Redis FSM storage")
        except ImportError:
            logger.warning("redis package not installed, falling back to MemoryStorage")

    dp = Dispatcher(storage=storage)
    dp.update.middleware(FsmTimeoutMiddleware())
    dp.callback_query.middleware(CallbackThrottlingMiddleware())
    dp.include_router(setup_routers())

    @dp.errors()
    async def on_error(event: ErrorEvent) -> None:
        logger.exception("Unhandled error while processing update", exc_info=event.exception)

    return dp


async def main() -> None:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dispatcher()

    logger.info("Bot started (polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
