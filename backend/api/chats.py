import os
import logging
import httpx
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.core.redis import backend_redis
from backend.models.models import Chat, User, Warn, AuditLog, ChatSettings
from backend.schemas.schemas import ChatResponse, DashboardStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chats", tags=["Chats"])

@router.get("", response_model=List[ChatResponse])
async def get_chats(
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).options(selectinload(Chat.settings)).order_by(desc(Chat.updated_at))
    )
    chats = result.scalars().all()
    return chats

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    # Total active chats
    chats_count = (await db.execute(select(func.count(Chat.id)).where(Chat.is_active == True))).scalar() or 0
    # Total users
    users_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    # Total banned users
    banned_count = (await db.execute(select(func.count(User.id)).where(User.is_banned == True))).scalar() or 0
    # Total warns issued
    warns_count = (await db.execute(select(func.count(Warn.id)))).scalar() or 0

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    logs_24h = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.created_at >= day_ago))).scalar() or 0
    logs_7d = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_ago))).scalar() or 0

    # Actions chart data
    action_counts_query = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
    )
    actions_chart = [{"name": action, "value": count} for action, count in action_counts_query.all()]

    # 7-day activity chart data
    activity_chart = []
    for i in range(6, -1, -1):
        target_date = now.date() - timedelta(days=i)
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        count = (await db.execute(
            select(func.count(AuditLog.id)).where(
                AuditLog.created_at >= start_of_day,
                AuditLog.created_at <= end_of_day
            )
        )).scalar() or 0
        
        activity_chart.append({
            "date": target_date.strftime("%d.%m"),
            "events": count
        })

    return DashboardStatsResponse(
        total_chats=chats_count,
        total_users=users_count,
        total_banned_users=banned_count,
        total_warns=warns_count,
        logs_24h=logs_24h,
        logs_7d=logs_7d,
        actions_chart=actions_chart,
        activity_chart=activity_chart
    )

@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat_by_id(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).options(selectinload(Chat.settings)).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return chat

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    # Call Telegram API leaveChat to make the bot exit the Telegram group
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8797571672:AAGQ2u_C-PWImETr_3YuB5ft0FUkZL3-M9g")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/leaveChat",
                json={"chat_id": chat_id},
                timeout=5.0
            )
            logger.info(f"leaveChat response for chat {chat_id}: {res.status_code} {res.text}")
        except Exception as e:
            logger.error(f"Error calling leaveChat for chat {chat_id}: {e}")

    # Delete chat from PostgreSQL DB (Cascades to settings, users, warns, stop_words, audit_logs)
    await db.delete(chat)
    await db.commit()

    # Invalidate Redis cache
    try:
        await backend_redis.invalidate_chat_cache(chat_id)
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted chat {chat_id}: {e}")

    return {"status": "success", "message": "Чат успешно удален из системы, бот покинул группу"}
