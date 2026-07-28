import logging
from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class NullRedis:
    """Fallback when Redis is not available."""

    async def publish(self, channel, message):
        pass

    async def get(self, key):
        return None

    async def setex(self, key, time, value):
        pass

    async def close(self):
        pass

    def __bool__(self):
        return False


redis_client = NullRedis()


async def init_redis():
    global redis_client
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
        await r.ping()
        redis_client = r
        logger.info("Redis connected")
    except Exception as e:
        redis_client = NullRedis()
        logger.warning(f"Redis not available, running without it: {e}")


async def close_redis():
    global redis_client
    if redis_client and not isinstance(redis_client, NullRedis):
        await redis_client.close()
        redis_client = NullRedis()


def get_redis():
    return redis_client
