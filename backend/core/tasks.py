import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import delete
from backend.core.database import AsyncSessionLocal
from backend.models.models import AuditLog

logger = logging.getLogger(__name__)

async def start_periodic_log_cleanup_worker(retention_days: int = 90):
    """
    Automated Background Maintenance Task.
    Runs every 24 hours to prune audit logs older than retention_days (default: 90 days).
    Prevents PostgreSQL database bloat automatically.
    """
    logger.info(f"Starting Periodic Audit Log Cleanup Worker (Retention: {retention_days} days)...")
    while True:
        try:
            # Sleep 24 hours between cleanup runs
            await asyncio.sleep(86400)
            cutoff = datetime.utcnow() - timedelta(days=retention_days)

            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(AuditLog).where(AuditLog.created_at < cutoff)
                )
                await session.commit()
                deleted_count = result.rowcount
                logger.info(f"Automated log cleanup executed: Deleted {deleted_count} logs older than {retention_days} days.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic audit log cleanup worker: {e}")
