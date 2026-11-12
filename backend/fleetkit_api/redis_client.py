from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from fleetkit_api.config import get_settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


async def ping_redis() -> bool:
    try:
        return bool(await get_redis().ping())
    except Exception:
        return False
