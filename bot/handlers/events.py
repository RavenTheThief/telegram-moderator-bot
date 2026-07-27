import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import CommandStart, Command
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR

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
            f"🌐 Панель управления: https://rostovskiyperec.ru:8081"
        )

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
            title=chat.title or f"Группа ({chat.id})",
            username=chat.username,
            chat_type=chat.type
        )

# Catch-all handler for any message in group chats to guarantee registration in DB
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message_event(message: Message):
    chat_id = message.chat.id
    await db_service.get_or_create_chat(
        chat_id=chat_id,
        title=message.chat.title or f"Группа ({chat_id})",
        username=message.chat.username,
        chat_type=message.chat.type
    )
