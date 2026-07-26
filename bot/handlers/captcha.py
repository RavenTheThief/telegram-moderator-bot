import random
import asyncio
import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPermissions
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOINED

from bot.services.db_service import db_service
from bot.services.redis_service import redis_service

logger = logging.getLogger(__name__)
router = Router(name="captcha_router")

async def start_captcha_background_worker(bot: Bot):
    """
    Persistent Redis-backed Captcha Expiration Background Task.
    Runs periodically every 10 seconds. Scans Redis for expired captcha timers.
    Survives container restarts cleanly because state is persisted in Redis!
    """
    logger.info("Starting Redis-backed Captcha Expiration Background Worker...")
    while True:
        try:
            await asyncio.sleep(10)
            expired_list = await redis_service.get_expired_captchas()

            for captcha_data in expired_list:
                chat_id = captcha_data.get("chat_id")
                user_id = captcha_data.get("user_id")
                message_id = captcha_data.get("message_id")
                user_fullname = captcha_data.get("user_fullname", "Пользователь")

                if not chat_id or not user_id:
                    continue

                logger.info(f"Captcha expired for user {user_id} in chat {chat_id}. Applying action...")

                # Delete Redis keys immediately so it's not processed twice
                await redis_service.delete_captcha(chat_id, user_id)

                settings = await db_service.get_chat_settings(chat_id)
                action = settings.captcha_fail_action.lower() if settings else "kick"

                # Delete captcha message
                if message_id:
                    try:
                        await bot.delete_message(chat_id, message_id)
                    except Exception:
                        pass

                # Apply Punishment
                if action == "ban":
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="captcha_failed",
                            reason="Таймаут прохождения капчи (Забанен)"
                        )
                    except Exception as e:
                        logger.error(f"Error banning user on captcha timeout: {e}")
                else:  # Kick
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await bot.unban_chat_member(chat_id, user_id)  # Kick and unban so they can retry
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="captcha_failed",
                            reason="Таймаут прохождения капчи (Исключен)"
                        )
                    except Exception as e:
                        logger.error(f"Error kicking user on captcha timeout: {e}")

        except Exception as e:
            logger.error(f"Error in captcha background worker: {e}")

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOINED))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    chat_id = event.chat.id
    new_user = event.new_chat_member.user

    if new_user.is_bot:
        return

    # Register user in DB
    await db_service.upsert_user(
        chat_id=chat_id,
        user_id=new_user.id,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        username=new_user.username,
        is_bot=new_user.is_bot
    )

    settings = await db_service.get_chat_settings(chat_id)
    if not settings or not settings.captcha_enabled:
        return

    # Restrict new member until captcha is solved
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=new_user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except Exception as e:
        logger.error(f"Error restricting user for captcha: {e}")

    user_fullname = new_user.full_name
    timeout = settings.captcha_timeout

    if settings.captcha_type == "math":
        a, b = random.randint(1, 10), random.randint(1, 10)
        correct_ans = a + b
        options = {correct_ans}
        while len(options) < 4:
            options.add(random.randint(2, 20))
        opts_list = list(options)
        random.shuffle(opts_list)

        buttons = []
        for opt in opts_list:
            buttons.append(InlineKeyboardButton(
                text=str(opt),
                callback_data=f"captcha:{new_user.id}:{opt}"
            ))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Для входа в чат решите пример: <b>{a} + {b} = ?</b>\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = str(correct_ans)
    else:
        # Button Captcha
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🟢 Я не робот (Нажмите)", callback_data=f"captcha:{new_user.id}:ok")
        ]])
        caption = (
            f"👋 <b>{user_fullname}</b>, добро пожаловать!\n"
            f"Подтвердите, что вы не робот, нажав кнопку ниже.\n"
            f"У вас есть <b>{timeout} секунд</b>."
        )
        answer_key = "ok"

    captcha_msg = await bot.send_message(chat_id, caption, reply_markup=keyboard)

    # Store state and expiration in Redis
    await redis_service.set_captcha(
        chat_id=chat_id,
        user_id=new_user.id,
        answer=answer_key,
        message_id=captcha_msg.message_id,
        user_fullname=user_fullname,
        timeout=timeout
    )

@router.callback_query(F.data.startswith("captcha:"))
async def on_captcha_callback(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    target_user_id = int(parts[1])
    user_answer = parts[2]
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    if user_id != target_user_id:
        await callback.answer("❌ Эта капча предназначена для другого пользователя!", show_alert=True)
        return

    captcha_data = await redis_service.get_captcha(chat_id, user_id)
    if not captcha_data:
        await callback.answer("⚠️ Капча устарела или уже была пройдена.", show_alert=True)
        return

    correct_answer = captcha_data.get("answer")

    if user_answer == correct_answer:
        await redis_service.delete_captcha(chat_id, user_id)
        await callback.answer("✅ Капча успешно пройдена! Добро пожаловать.")

        # Unmute user
        try:
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True
                )
            )
        except Exception:
            pass

        # Delete captcha message
        try:
            await callback.message.delete()
        except Exception:
            pass

        user_fullname = callback.from_user.full_name
        await db_service.log_action(
            chat_id=chat_id,
            user_id=user_id,
            user_fullname=user_fullname,
            action="captcha_passed",
            reason="Капча успешно пройдена"
        )

        settings = await db_service.get_chat_settings(chat_id)
        if settings and settings.welcome_message_enabled and settings.welcome_text:
            welcome_msg = await bot.send_message(
                chat_id,
                f"🎉 <b>{user_fullname}</b>, {settings.welcome_text}"
            )
            if settings.bot_auto_delete_seconds > 0:
                async def delete_later(m, delay):
                    await asyncio.sleep(delay)
                    try:
                        await m.delete()
                    except Exception:
                        pass
                asyncio.create_task(delete_later(welcome_msg, settings.bot_auto_delete_seconds))
    else:
        await callback.answer("❌ Неверный ответ! Попробуйте еще раз.", show_alert=True)
