"""Redis Cache Service"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis

from app.config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL or "redis://localhost:6379"
        self.client = None
        self.default_ttl = settings.REDIS_CACHE_TTL or 300
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self.client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get failed for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl
            await self.client.set(key, serialized, ex=ttl)
            logger.debug(f"Cached {key} for {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern"""
        if not self.client:
            return False
        
        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern failed: {e}")
            return False
    
    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key"""
        return f"{prefix}:{':'.join(str(arg) for arg in args)}"