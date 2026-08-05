import os
import httpx
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.models import User, Warn, AuditLog
from backend.schemas.schemas import UserResponse

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

router = APIRouter(prefix="/api/chats/{chat_id}/users", tags=["Users Management"])

@router.get("", response_model=List[UserResponse])
async def get_chat_users(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(User).options(selectinload(User.warns)).where(User.chat_id == chat_id)
    )
    users = result.scalars().all()

    # Populate warns count
    response_users = []
    for u in users:
        u_dict = UserResponse.model_validate(u)
        u_dict.warns_count = len(u.warns)
        response_users.append(u_dict)

    return response_users

@router.post("/{user_id}/unwarn")
async def unwarn_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_username: str = Depends(get_current_user)
):
    # Remove all active warns for this user in chat
    await db.execute(
        delete(Warn).where(Warn.chat_id == chat_id, Warn.user_id == user_id)
    )
    
    # Reset restriction flag if user is not banned
    res = await db.execute(select(User).where(User.chat_id == chat_id, User.id == user_id))
    user = res.scalar_one_or_none()
    if user:
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()
        await db.log_action(
            chat_id=chat_id,
            user_id=user_id,
            user_fullname=user_fullname,
            action="unwarn_user",
            reason=f"Варны полностью сброшены администратором ({admin_username})"
        )

    await db.commit()
    return {"status": "success", "message": "Варны пользователя успешно сброшены"}

@router.post("/{user_id}/unmute")
async def unmute_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_username: str = Depends(get_current_user)
):
    # Call Telegram Bot API unrestrictChatMember
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{TELEGRAM_API_URL}/restrictChatMember",
                json={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "permissions": {
                        "can_send_messages": True,
                        "can_send_media_messages": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True
                    }
                },
                timeout=5.0
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка соединения с Telegram API: {e}")

    # Update DB status
    res = await db.execute(select(User).where(User.chat_id == chat_id, User.id == user_id))
    user = res.scalar_one_or_none()
    if user:
        user.is_restricted = False
        user.restricted_until = None
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()
        
        # Log Action
        log = AuditLog(
            chat_id=chat_id,
            user_id=user_id,
            user_fullname=user_fullname,
            action="unmute_user",
            reason=f"Мут снят администратором ({admin_username})"
        )
        db.add(log)

    await db.commit()
    return {"status": "success", "message": "Мут с пользователя успешно снят в Telegram"}

@router.post("/{user_id}/unban")
async def unban_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_username: str = Depends(get_current_user)
):
    # Call Telegram Bot API unbanChatMember
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{TELEGRAM_API_URL}/unbanChatMember",
                json={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "only_if_banned": True
                },
                timeout=5.0
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка соединения с Telegram API: {e}")

    # Update DB status
    res = await db.execute(select(User).where(User.chat_id == chat_id, User.id == user_id))
    user = res.scalar_one_or_none()
    if user:
        user.is_banned = False
        user_fullname = f"{user.first_name} {user.last_name or ''}".strip()
        
        # Log Action
        log = AuditLog(
            chat_id=chat_id,
            user_id=user_id,
            user_fullname=user_fullname,
            action="unban_user",
            reason=f"Бан снят администратором ({admin_username})"
        )
        db.add(log)

    await db.commit()
    return {"status": "success", "message": "Пользователь разбанен в Telegram"}
