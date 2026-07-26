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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8797571672:AAGQ2u_C-PWImETr_3YuB5ft0FUkZL3-M9g")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

router = APIRouter(prefix="/api/chats/{chat_id}/users", tags=["Users Management"])

@router.get("", response_model=List[UserResponse])
async def get_chat_users(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.warns))
        .where(User.chat_id == chat_id)
        .order_by(User.joined_at.desc())
    )
    users = result.scalars().all()
    
    response = []
    for u in users:
        u_dict = UserResponse.model_validate(u)
        u_dict.warns_count = len(u.warns)
        response.append(u_dict)
        
    return response

@router.post("/{user_id}/unwarn")
async def unwarn_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    # Delete all warns for this user in chat
    await db.execute(
        delete(Warn).where(Warn.chat_id == chat_id, Warn.user_id == user_id)
    )
    
    # Audit log
    audit = AuditLog(
        chat_id=chat_id,
        user_id=user_id,
        action="unwarn",
        reason="Снятие предупреждений через Веб-панель",
        details=f"Выполнено администратором {username}"
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "message": "Варны сброшены"}

@router.post("/{user_id}/unmute")
async def unmute_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    # Update DB user state
    result = await db.execute(
        select(User).where(User.chat_id == chat_id, User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.is_restricted = False
        user.restricted_until = None
    
    # Call Telegram API to lift restrictions
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{TELEGRAM_API_URL}/restrictChatMember",
                json={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "permissions": {
                        "can_send_messages": True,
                        "can_send_audios": True,
                        "can_send_documents": True,
                        "can_send_photos": True,
                        "can_send_videos": True,
                        "can_send_video_notes": True,
                        "can_send_voice_notes": True,
                        "can_send_polls": True,
                        "can_send_other_messages": True,
                        "can_add_web_page_previews": True,
                        "can_change_info": False,
                        "can_invite_users": True,
                        "can_pin_messages": False,
                    }
                }
            )
        except Exception as e:
            pass

    audit = AuditLog(
        chat_id=chat_id,
        user_id=user_id,
        user_fullname=user.first_name if user else None,
        action="unmute",
        reason="Снятие мута через Веб-панель",
        details=f"Выполнено администратором {username}"
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "message": "Мут снят"}

@router.post("/{user_id}/unban")
async def unban_user(
    chat_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(User).where(User.chat_id == chat_id, User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.is_banned = False

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{TELEGRAM_API_URL}/unbanChatMember",
                json={
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "only_if_banned": True
                }
            )
        except Exception as e:
            pass

    audit = AuditLog(
        chat_id=chat_id,
        user_id=user_id,
        user_fullname=user.first_name if user else None,
        action="unban",
        reason="Разбан через Веб-панель",
        details=f"Выполнено администратором {username}"
    )
    db.add(audit)
    await db.commit()
    return {"status": "success", "message": "Пользователь разбанен"}
