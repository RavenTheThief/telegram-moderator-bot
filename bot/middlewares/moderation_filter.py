import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, List
from aiogram import BaseMiddleware
from aiogram.types import Message, ChatPermissions
from bot.services.db_service import db_service

class ModerationFilterMiddleware(BaseMiddleware):
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

        # Update or register user info in DB
        await db_service.upsert_user(
            chat_id=chat_id,
            user_id=user_id,
            first_name=event.from_user.first_name,
            last_name=event.from_user.last_name,
            username=event.from_user.username,
            is_bot=event.from_user.is_bot
        )

        # Skip checks for chat admins
        if bot:
            try:
                member = await bot.get_chat_member(chat_id, user_id)
                if member.status in ["administrator", "creator"]:
                    return await handler(event, data)
            except Exception:
                pass

        settings = await db_service.get_chat_settings(chat_id)
        if not settings:
            return await handler(event, data)

        text = event.text or event.caption or ""
        violation_reason = None

        # 1. Anti-Channel Filter (messages sent on behalf of a Telegram channel)
        if settings.filter_anti_channel and event.sender_chat and event.sender_chat.id != chat_id:
            violation_reason = "Отправка сообщения от имени канала"

        # 2. Anti-Forward Filter
        elif settings.filter_anti_forward and (event.forward_from or event.forward_from_chat or event.forward_date):
            violation_reason = "Пересылка сообщений запрещена"

        # 3. Media Filters
        elif settings.filter_gifs and event.animation:
            violation_reason = "Отправка GIF-анимаций запрещена"
        elif settings.filter_stickers and event.sticker:
            violation_reason = "Отправка стикеров запрещена"
        elif settings.filter_voice and event.voice:
            violation_reason = "Голосовые сообщения запрещены"
        elif settings.filter_video_notes and event.video_note:
            violation_reason = "Видео-сообщения (кружочки) запрещены"
        elif settings.filter_audio and event.audio:
            violation_reason = "Аудиозаписи запрещены"
        elif settings.filter_video and event.video:
            violation_reason = "Видеофайлы запрещены"
        elif settings.filter_documents and event.document:
            violation_reason = "Документы и файлы запрещены"

        # 4. Link & Domain Whitelist Filter
        elif settings.filter_links and text:
            # Match URLs, http, https, t.me, etc.
            url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*)'
            urls = re.findall(url_pattern, text)
            if urls:
                allowed_domains = [d.strip().lower() for d in settings.whitelisted_domains.split(",") if d.strip()]
                for url in urls:
                    clean_url = url if url.startswith("http") else "http://" + url
                    try:
                        parsed = urllib.parse.urlparse(clean_url)
                        domain = parsed.netloc.lower().split(":")[0]
                        # Remove www.
                        if domain.startswith("www."):
                            domain = domain[4:]
                        
                        # Check if domain or top-level matches any allowed domain
                        is_allowed = any(domain == allowed or domain.endswith("." + allowed) for allowed in allowed_domains)
                        if not is_allowed:
                            violation_reason = f"Запрещенная ссылка ({domain})"
                            break
                    except Exception:
                        violation_reason = "Запрещенная ссылка"
                        break

        # 5. Stop-Words Filter
        elif text:
            stop_words = await db_service.get_stop_words(chat_id)
            for sw in stop_words:
                if sw.is_regex:
                    try:
                        if re.search(sw.word, text, re.IGNORECASE):
                            violation_reason = f"Стоп-слово (Regex: {sw.word})"
                            break
                    except Exception:
                        pass
                else:
                    if sw.word.lower() in text.lower():
                        violation_reason = f"Стоп-слово ({sw.word})"
                        break

        # 6. Anti-Caps Filter
        if not violation_reason and settings.anti_caps_enabled and text and len(text) >= 8:
            letters = [c for c in text if c.isalpha()]
            if len(letters) >= 6:
                caps = [c for c in letters if c.isupper()]
                caps_percent = (len(caps) / len(letters)) * 100
                if caps_percent >= settings.anti_caps_threshold_percent:
                    violation_reason = f"Капс лок ({int(caps_percent)}% заглавных)"

        # Process Violation if triggered
        if violation_reason:
            try:
                await event.delete()
            except Exception:
                pass

            user_fullname = event.from_user.full_name
            # Log violation audit
            await db_service.log_action(
                chat_id=chat_id,
                user_id=user_id,
                user_fullname=user_fullname,
                action="delete_message",
                reason=violation_reason
            )

            # Issue Warn
            warn_count = await db_service.add_warn(
                chat_id=chat_id,
                user_id=user_id,
                reason=violation_reason,
                issuer="AutoModerator"
            )

            # Check Warn Limit
            if warn_count >= settings.max_warns:
                await db_service.clear_warns(chat_id, user_id)
                punishment = settings.warns_punishment.lower()

                if punishment == "ban":
                    try:
                        await bot.ban_chat_member(chat_id, user_id)
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="ban_user",
                            reason=f"Достигнут лимит варнов ({settings.max_warns}/{settings.max_warns})",
                            details=f"Последнее нарушение: {violation_reason}"
                        )
                        msg = await event.answer(f"🚫 <b>{user_fullname}</b> забанен! Достигнут лимит варнов ({settings.max_warns}).")
                    except Exception:
                        pass
                else:  # Mute
                    mute_until = datetime.utcnow() + timedelta(minutes=settings.warns_mute_duration_minutes)
                    try:
                        await bot.restrict_chat_member(
                            chat_id=chat_id,
                            user_id=user_id,
                            permissions=ChatPermissions(can_send_messages=False),
                            until_date=mute_until
                        )
                        await db_service.log_action(
                            chat_id=chat_id,
                            user_id=user_id,
                            user_fullname=user_fullname,
                            action="mute_user",
                            reason=f"Достигнут лимит варнов ({settings.max_warns}/{settings.max_warns})",
                            details=f"Мут на {settings.warns_mute_duration_minutes} мин. Последнее нарушение: {violation_reason}"
                        )
                        msg = await event.answer(f"🤐 <b>{user_fullname}</b> замучен на {settings.warns_mute_duration_minutes} мин! Достигнут лимит варнов ({settings.max_warns}).")
                    except Exception:
                        pass
            else:
                msg = await event.answer(
                    f"⚠️ <b>{user_fullname}</b>, ваше сообщение удалено.\n"
                    f"Причина: <i>{violation_reason}</i>\n"
                    f"Предупреждения: <b>{warn_count}/{settings.max_warns}</b>"
                )

            # Auto-delete notification message
            if 'msg' in locals() and settings.bot_auto_delete_seconds > 0:
                import asyncio
                async def delete_later(m, delay):
                    await asyncio.sleep(delay)
                    try:
                        await m.delete()
                    except Exception:
                        pass
                asyncio.create_task(delete_later(msg, settings.bot_auto_delete_seconds))

            return None  # Stop handler execution

        return await handler(event, data)
