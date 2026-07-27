import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config import settings
from bot.middlewares.chat_type import ChatTypeMiddleware
from bot.middlewares.anti_flood import AntiFloodMiddleware
from bot.middlewares.moderation_filter import ModerationFilterMiddleware
from bot.handlers import captcha, events
from bot.services.redis_service import redis_service
from bot.services.db_service import db_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def start_warn_expiration_background_worker():
    logger.info("Starting Warn Expiration Background Worker...")
    while True:
        try:
            await asyncio.sleep(60)
            await db_service.expire_old_warns()
        except Exception as e:
            logger.error(f"Error in warn expiration worker: {e}")

async def main():
    logger.info("Starting Telegram Moderator Bot...")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # 1. Outer Middleware: STRICT DM Restriction (Blocks all private messages/commands)
    dp.message.outer_middleware(ChatTypeMiddleware())
    dp.callback_query.outer_middleware(ChatTypeMiddleware())

    # 2. Outer Middleware: Content Moderation & Auto Chat Registration for all group updates
    dp.message.outer_middleware(ModerationFilterMiddleware())

    # 3. Inner Middleware for Rate Limiting
    dp.message.middleware(AntiFloodMiddleware())

    # 4. Include Handlers
    dp.include_router(captcha.router)
    dp.include_router(events.router)

    # Initialize Redis connection
    await redis_service.connect()

    # Background Tasks:
    # 1. Captcha expiration scanner worker
    asyncio.create_task(captcha.start_captcha_background_worker(bot))
    # 2. Redis Pub/Sub listener for real-time Web Panel settings invalidation
    asyncio.create_task(redis_service.start_pubsub_listener())
    # 3. Warn expiration scanner worker (runs every 60s)
    asyncio.create_task(start_warn_expiration_background_worker())

    logger.info("Bot starting polling loop...")
    try:
        await dp.start_polling(bot)
    finally:
        await redis_service.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
