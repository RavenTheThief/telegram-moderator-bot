from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.models import AuditLog
from backend.schemas.schemas import AuditLogResponse

router = APIRouter(tags=["Audit Logs"])

@router.get("/api/chats/{chat_id}/logs", response_model=List[AuditLogResponse])
async def get_chat_logs(
    chat_id: int,
    action: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    query = select(AuditLog).where(AuditLog.chat_id == chat_id)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/api/chats/{chat_id}/logs/clean")
async def clean_chat_logs(
    chat_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        delete(AuditLog).where(
            AuditLog.chat_id == chat_id,
            AuditLog.created_at < cutoff_date
        )
    )
    await db.commit()
    return {"status": "success", "message": f"Очищены логи старше {days} дней для чата {chat_id}"}

@router.get("/api/logs/all", response_model=List[AuditLogResponse])
async def get_all_logs(
    action: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/api/logs/all/clean")
async def clean_all_logs(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    username: str = Depends(get_current_user)
):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        delete(AuditLog).where(AuditLog.created_at < cutoff_date)
    )
    await db.commit()
    return {"status": "success", "message": f"Очищены все логи системы старше {days} дней"}
