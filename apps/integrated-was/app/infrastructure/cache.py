import asyncio
import json
import time
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings


class Cache:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        self.memory: dict[str, tuple[float, Any]] = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value is not None else None
        except Exception:
            async with self.lock:
                cached = self.memory.get(key)
                if cached is None:
                    return None
                expires_at, value = cached
                if expires_at <= time.monotonic():
                    self.memory.pop(key, None)
                    return None
                return value

    async def set(self, key: str, value: Any, ttl: int) -> None:
        try:
            await self.redis.set(key, json.dumps(value), ex=ttl)
        except Exception:
            async with self.lock:
                self.memory[key] = (time.monotonic() + ttl, value)


cache = Cache()

