from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.core.redis import backend_redis
from backend.models.models import ChatSettings, StopWord, Chat
from backend.schemas.schemas import ChatSettingsResponse, ChatSettingsUpdate, StopWordResponse, StopWordCreate

router = APIRouter(prefix="/api/chats/{chat_id}", tags=["Settings & Filters"])

@router.get("/settings", response_model=ChatSettingsResponse)
async def get_chat_settings(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
    settings = result.scalar_one_or_none()

    if not settings:
        chat = (await db.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        settings = ChatSettings(chat_id=chat_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings

@router.put("/settings", response_model=ChatSettingsResponse)
async def update_chat_settings(
    chat_id: int,
    settings_update: ChatSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(select(ChatSettings).where(ChatSettings.chat_id == chat_id))
    settings = result.scalar_one_or_none()

    if not settings:
        chat = (await db.execute(select(Chat).where(Chat.id == chat_id))).scalar_one_or_none()
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        settings = ChatSettings(chat_id=chat_id)
        db.add(settings)

    for field, value in settings_update.model_dump().items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    # Invalidate Redis cache after DB commit
    try:
        await backend_redis.invalidate_chat_cache(chat_id)
    except Exception as e:
        pass

    return settings

# Stop Words Endpoints
@router.get("/stopwords", response_model=List[StopWordResponse])
async def get_stop_words(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(StopWord).where(StopWord.chat_id == chat_id).order_by(StopWord.id.desc())
    )
    return result.scalars().all()

@router.post("/stopwords", response_model=StopWordResponse)
async def add_stop_word(
    chat_id: int,
    data: StopWordCreate,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    stop_word = StopWord(
        chat_id=chat_id,
        word=data.word.strip(),
        is_regex=data.is_regex
    )
    db.add(stop_word)
    await db.commit()
    await db.refresh(stop_word)

    # Invalidate Redis cache after DB commit
    try:
        await backend_redis.invalidate_chat_cache(chat_id)
    except Exception as e:
        pass

    return stop_word

@router.delete("/stopwords/{stop_word_id}")
async def delete_stop_word(
    chat_id: int,
    stop_word_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    await db.execute(
        delete(StopWord).where(StopWord.chat_id == chat_id, StopWord.id == stop_word_id)
    )
    await db.commit()

    # Invalidate Redis cache after DB commit
    try:
        await backend_redis.invalidate_chat_cache(chat_id)
    except Exception as e:
        pass

    return {"status": "success", "message": "Стоп-слово удалено"}
