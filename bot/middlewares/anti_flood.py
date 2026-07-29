from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, ChatPermissions
from bot.services.redis_service import redis_service
from bot.services.db_service import db_service
from bot.middlewares.moderation_filter import is_admin_or_creator

class AntiFloodMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user or event.from_user.is_bot:
            return await handler(event, data)

        chat_id = event.chat.id
        user_id = event.from_user.id
        bot = data.get("bot")

        # Skip anti-flood checks for chat admins & creators
        if await is_admin_or_creator(bot, chat_id, user_id, event.sender_chat):
            return await handler(event, data)

        settings = await db_service.get_chat_settings(chat_id)
        if not settings or not settings.anti_flood_enabled:
            return await handler(event, data)

        is_flood = await redis_service.is_flooding(
            chat_id=chat_id,
            user_id=user_id,
            max_msgs=settings.anti_flood_max_messages,
            window_sec=settings.anti_flood_window_seconds
        )

        if is_flood:
            try:
                await event.delete()
            except Exception:
                pass

            # Mute user
            mute_until = datetime.utcnow() + timedelta(minutes=settings.anti_flood_mute_duration_minutes)
            try:
                await bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=mute_until
                )
                
                user_fullname = event.from_user.full_name
                await db_service.log_action(
                    chat_id=chat_id,
                    user_id=user_id,
                    user_fullname=user_fullname,
                    action="mute_user",
                    reason=f"Антифлуд: Превышен лимит ({settings.anti_flood_max_messages} сообщ. за {settings.anti_flood_window_seconds} сек)",
                    details=f"Мут на {settings.anti_flood_mute_duration_minutes} минут"
                )

                warning_msg = await event.answer(
                    f"⚠️ <b>{user_fullname}</b> заблокирован на {settings.anti_flood_mute_duration_minutes} мин. Причина: Флуд."
                )
                # Auto delete notice if configured
                if settings.bot_auto_delete_seconds > 0:
                    import asyncio
                    async def delete_later(msg, delay):
                        await asyncio.sleep(delay)
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    asyncio.create_task(delete_later(warning_msg, settings.bot_auto_delete_seconds))

            except Exception as e:
                pass

            return None  # Stop handler chain for flood message

        return await handler(event, data)
