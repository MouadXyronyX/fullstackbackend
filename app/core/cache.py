import json
import logging
from typing import Any, Optional
import redis

logger = logging.getLogger(__name__)

_pool: Optional[redis.Redis] = None
CACHE_TTL = 30  # seconds


def init_sync_redis(url: str) -> Optional[redis.Redis]:
    global _pool
    try:
        _pool = redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        _pool.ping()
        logger.info("Sync Redis connected")
        return _pool
    except Exception as e:
        _pool = None
        logger.warning(f"Sync Redis not available: {e}")
        return None


def get_sync_redis() -> Optional[redis.Redis]:
    return _pool


def cache_get(key: str) -> Optional[Any]:
    if not _pool:
        return None
    try:
        raw = _pool.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def cache_set(key: str, value: Any, ttl: int = CACHE_TTL):
    if not _pool:
        return
    try:
        _pool.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
    except Exception:
        pass


def cache_delete_pattern(pattern: str):
    if not _pool:
        return
    try:
        for key in _pool.scan_iter(match=pattern):
            _pool.delete(key)
    except Exception:
        pass
