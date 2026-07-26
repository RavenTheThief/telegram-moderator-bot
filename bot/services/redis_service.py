import time
import json
import asyncio
import logging
from typing import Optional, List
from redis.asyncio import Redis

from bot.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.redis: Optional[Redis] = None

    async def connect(self):
        if not self.redis:
            self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        if self.redis:
            await self.redis.close()

    # Anti-flood sliding window rate limit
    async def is_flooding(self, chat_id: int, user_id: int, max_msgs: int, window_sec: int) -> bool:
        if not self.redis:
            await self.connect()

        key = f"flood:{chat_id}:{user_id}"
        now = time.time()
        pipeline = self.redis.pipeline()
        pipeline.zremrangebyscore(key, 0, now - window_sec)
        pipeline.zadd(key, {str(now): now})
        pipeline.zcard(key)
        pipeline.expire(key, window_sec + 5)
        results = await pipeline.execute()

        count = results[2]
        return count > max_msgs

    # Captcha state store with Expiration tracking
    async def set_captcha(
        self,
        chat_id: int,
        user_id: int,
        answer: str,
        message_id: int,
        user_fullname: str,
        timeout: int
    ):
        if not self.redis:
            await self.connect()

        now = time.time()
        expire_at = now + timeout

        data = {
            "chat_id": chat_id,
            "user_id": user_id,
            "answer": str(answer),
            "message_id": message_id,
            "user_fullname": user_fullname,
            "expire_at": expire_at
        }

        key = f"captcha:{chat_id}:{user_id}"
        expire_key = f"captcha_expire:{chat_id}:{user_id}"

        # Safety TTL = timeout + 60 seconds
        ttl = timeout + 60
        await self.redis.set(key, json.dumps(data), ex=ttl)
        await self.redis.set(expire_key, str(expire_at), ex=ttl)

    async def get_captcha(self, chat_id: int, user_id: int) -> Optional[dict]:
        if not self.redis:
            await self.connect()
        key = f"captcha:{chat_id}:{user_id}"
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def delete_captcha(self, chat_id: int, user_id: int):
        if not self.redis:
            await self.connect()
        key = f"captcha:{chat_id}:{user_id}"
        expire_key = f"captcha_expire:{chat_id}:{user_id}"
        await self.redis.delete(key, expire_key)

    # Worker scanner for expired captchas
    async def get_expired_captchas(self) -> List[dict]:
        if not self.redis:
            await self.connect()

        now = time.time()
        expired_captchas = []

        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match="captcha_expire:*", count=100)
            for exp_key in keys:
                try:
                    exp_val = await self.redis.get(exp_key)
                    if exp_val and float(exp_val) <= now:
                        parts = exp_key.split(":")
                        if len(parts) == 3:
                            chat_id = int(parts[1])
                            user_id = int(parts[2])
                            captcha_data = await self.redis.get(f"captcha:{chat_id}:{user_id}")
                            if captcha_data:
                                expired_captchas.append(json.loads(captcha_data))
                            else:
                                await self.redis.delete(exp_key)
                except Exception as e:
                    logger.error(f"Error checking expired captcha key {exp_key}: {e}")

            if cursor == 0:
                break

        return expired_captchas

    # Chat Settings & Stop Words Caching
    async def get_cached_settings(self, chat_id: int) -> Optional[dict]:
        if not self.redis:
            await self.connect()
        raw = await self.redis.get(f"chat_settings:{chat_id}")
        if raw:
            return json.loads(raw)
        return None

    async def set_cached_settings(self, chat_id: int, settings_dict: dict, ttl: int = 300):
        if not self.redis:
            await self.connect()
        await self.redis.set(f"chat_settings:{chat_id}", json.dumps(settings_dict), ex=ttl)

    async def invalidate_settings(self, chat_id: int):
        if not self.redis:
            await self.connect()
        await self.redis.delete(f"chat_settings:{chat_id}")

    async def get_cached_stopwords(self, chat_id: int) -> Optional[List[dict]]:
        if not self.redis:
            await self.connect()
        raw = await self.redis.get(f"stop_words:{chat_id}")
        if raw:
            return json.loads(raw)
        return None

    async def set_cached_stopwords(self, chat_id: int, stopwords_list: List[dict], ttl: int = 300):
        if not self.redis:
            await self.connect()
        await self.redis.set(f"stop_words:{chat_id}", json.dumps(stopwords_list), ex=ttl)

    async def invalidate_stopwords(self, chat_id: int):
        if not self.redis:
            await self.connect()
        await self.redis.delete(f"stop_words:{chat_id}")

    # Real-time Pub/Sub Subscriber Listener
    async def start_pubsub_listener(self):
        logger.info("Starting Redis Pub/Sub settings update listener...")
        r = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe("settings_updates")

        try:
            async for message in pubsub.listen():
                if message and message.get("type") == "message":
                    try:
                        data = json.loads(message.get("data"))
                        chat_id = data.get("chat_id")
                        if chat_id:
                            logger.info(f"Pub/Sub event received: Invalidating cache for chat {chat_id}")
                            await self.invalidate_settings(chat_id)
                            await self.invalidate_stopwords(chat_id)
                    except Exception as e:
                        logger.error(f"Error handling Pub/Sub message: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Pub/Sub listener error: {e}")
        finally:
            await pubsub.unsubscribe("settings_updates")
            await r.close()

redis_service = RedisService()
