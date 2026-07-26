import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR

from bot.services.db_service import db_service

router = Router(name="events_router")

@router.message(F.new_chat_members)
@router.message(F.left_chat_member)
@router.message(F.pinned_message)
async def auto_clean_service_messages(message: Message):
    chat_id = message.chat.id
    settings = await db_service.get_chat_settings(chat_id)

    if settings and settings.clean_service_messages:
        try:
            await message.delete()
        except Exception:
            pass

@router.my_chat_member()
async def on_bot_status_changed(event: ChatMemberUpdated):
    chat = event.chat
    if event.new_chat_member.status in ["administrator", "member"]:
        await db_service.get_or_create_chat(
            chat_id=chat.id,
            title=chat.title or "Unassigned Group",
            username=chat.username,
            chat_type=chat.type
        )
