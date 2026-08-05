import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR

from bot.config import settings
from bot.services.db_service import db_service

router = Router(name="events_router")

@router.message(CommandStart())
@router.message(Command("start", "help", "chatid", "status"))
async def on_start_command(message: Message):
    if message.chat and message.chat.type in ["group", "supergroup"]:
        chat = await db_service.get_or_create_chat(
            chat_id=message.chat.id,
            title=message.chat.title or f"Группа ({message.chat.id})",
            username=message.chat.username,
            chat_type=message.chat.type
        )
        await message.reply(
            f"🛡️ <b>Модератор активирован в чате \"{chat.title}\"!</b>\n\n"
            f"🆔 ID Чата: <code>{message.chat.id}</code>\n"
            f"🌐 Панель управления: {settings.WEB_PANEL_URL}"
        )

@router.message(F.new_chat_members)
@router.message(F.left_chat_member)
@router.message(F.pinned_message)
async def auto_clean_service_messages(message: Message):
    if not message.chat or message.chat.type not in ["group", "supergroup"]:
        return

    chat_settings = await db_service.get_chat_settings(message.chat.id)
    if chat_settings and chat_settings.clean_service_messages:
        try:
            await message.delete()
        except Exception:
            pass

@router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION=MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    chat_id = event.chat.id
    user = event.new_chat_member.user

    await db_service.upsert_user(
        chat_id=chat_id,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        is_bot=user.is_bot
    )

@router.chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION=LEAVE))
async def on_user_leave(event: ChatMemberUpdated):
    pass
