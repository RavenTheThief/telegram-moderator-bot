import os
import json
import logging
from typing import Optional
from redis.asyncio import Redis

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

class BackendRedis:
    def __init__(self):
        self.redis: Optional[Redis] = None

    async def get_client(self) -> Redis:
        if not self.redis:
            self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
        return self.redis

    async def invalidate_chat_cache(self, chat_id: int):
        client = await self.get_client()
        # 1. Delete Redis keys directly
        await client.delete(f"chat_settings:{chat_id}")
        await client.delete(f"stop_words:{chat_id}")

        # 2. Publish Real-time Pub/Sub notification for active bot instances
        try:
            payload = json.dumps({"chat_id": chat_id, "action": "settings_updated"})
            await client.publish("settings_updates", payload)
            logger.info(f"Published Pub/Sub settings_updated event for chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to publish Pub/Sub event for chat {chat_id}: {e}")

backend_redis = BackendRedis()
