from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete, func

from bot.config import settings
from bot.services.redis_service import redis_service
from backend.models.models import Chat, ChatSettings, User, Warn, StopWord, AuditLog

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
AsyncSessionMaker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class DBService:
    @staticmethod
    async def get_or_create_chat(chat_id: int, title: str, username: Optional[str], chat_type: str) -> Chat:
        async with AsyncSessionMaker() as session:
            result = await session.execute(select(Chat).where(Chat.id == chat_id))
            chat = result.scalar_one_or_none()

            if not chat:
                chat = Chat(id=chat_id, title=title, username=username, type=chat_type, is_active=True)
                session.add(chat)
                await session.flush()
                # Create default settings
                chat_settings = ChatSettings(chat_id=chat_id)
                session.add(chat_settings)
                await session.commit()
                await session.refresh(chat)
            else:
                if chat.title != title or chat.username != username or not chat.is_active:
                    chat.title = title
                    chat.username = username
                    chat.is_active = True
                    await session.commit()

            return chat

    @staticmethod
    async def get_chat_settings(chat_id: int) -> Optional[ChatSettings]:
        # 1. Try Redis cache first
        cached = await redis_service.get_cached_settings(chat_id)
        if cached:
            s = ChatSettings()
            for k, v in cached.items():
                setattr(s, k, v)
            return s

        # 2. Database fallback
        async with AsyncSessionMaker() as session:
            result = await session.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
            cs = result.scalar_one_or_none()
            if cs:
                # Store in Redis
                s_dict = {
                    c.name: getattr(cs, c.name)
                    for c in cs.__table__.columns
                }
                await redis_service.set_cached_settings(chat_id, s_dict, ttl=300)
            return cs

    @staticmethod
    async def upsert_user(chat_id: int, user_id: int, first_name: str, last_name: Optional[str], username: Optional[str], is_bot: bool) -> User:
        async with AsyncSessionMaker() as session:
            result = await session.execute(select(User).where(User.chat_id == chat_id, User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    id=user_id,
                    chat_id=chat_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    is_bot=is_bot
                )
                session.add(user)
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.username = username
            await session.commit()
            return user

    @staticmethod
    async def get_stop_words(chat_id: int) -> List[StopWord]:
        # 1. Try Redis cache first
        cached = await redis_service.get_cached_stopwords(chat_id)
        if cached is not None:
            res = []
            for item in cached:
                sw = StopWord(
                    id=item["id"],
                    chat_id=item["chat_id"],
                    word=item["word"],
                    is_regex=item["is_regex"]
                )
                res.append(sw)
            return res

        # 2. Database fallback
        async with AsyncSessionMaker() as session:
            result = await session.execute(select(StopWord).where(StopWord.chat_id == chat_id))
            sw_list = result.scalars().all()
            
            # Save to Redis
            cache_list = [
                {"id": sw.id, "chat_id": sw.chat_id, "word": sw.word, "is_regex": sw.is_regex}
                for sw in sw_list
            ]
            await redis_service.set_cached_stopwords(chat_id, cache_list, ttl=300)
            return sw_list

    @staticmethod
    async def log_action(chat_id: int, user_id: Optional[int], user_fullname: Optional[str], action: str, reason: str, details: Optional[str] = None):
        async with AsyncSessionMaker() as session:
            log = AuditLog(
                chat_id=chat_id,
                user_id=user_id,
                user_fullname=user_fullname,
                action=action,
                reason=reason,
                details=details
            )
            session.add(log)
            await session.commit()

    @staticmethod
    async def add_warn(chat_id: int, user_id: int, reason: str, issuer: str = "System") -> int:
        async with AsyncSessionMaker() as session:
            warn = Warn(chat_id=chat_id, user_id=user_id, reason=reason, issuer=issuer)
            session.add(warn)
            await session.commit()

            count_result = await session.execute(
                select(func.count(Warn.id)).where(Warn.chat_id == chat_id, Warn.user_id == user_id)
            )
            return count_result.scalar() or 1

    @staticmethod
    async def clear_warns(chat_id: int, user_id: int):
        async with AsyncSessionMaker() as session:
            await session.execute(delete(Warn).where(Warn.chat_id == chat_id, Warn.user_id == user_id))
            await session.commit()

db_service = DBService()
