from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

class ChatTypeMiddleware(BaseMiddleware):
    """
    Strict DM Restriction Middleware.
    Blocks all execution in private chats (DM).
    Only allows execution inside Group and Supergroup chats.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        chat = None
        if isinstance(event, Message):
            chat = event.chat
        elif isinstance(event, CallbackQuery) and event.message:
            chat = event.message.chat

        if chat and chat.type == "private":
            if isinstance(event, Message):
                try:
                    await event.reply("⛔ Данный бот работает исключительно внутри групповых чатов.")
                except Exception:
                    pass
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("⛔ Данный бот работает исключительно в группах.", show_alert=True)
                except Exception:
                    pass
            # STOP execution for DM!
            return None

        return await handler(event, data)
