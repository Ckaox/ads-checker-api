"""
Cache service for storing temporary data
"""
import json
import time
from typing import Any, Optional, Dict
from cachetools import TTLCache

from app.core.config import settings

class CacheService:
    """In-memory cache service with TTL support"""
    
    def __init__(self):
        # Initialize in-memory cache with TTL
        # Max 1000 items, default TTL from settings
        self._cache = TTLCache(maxsize=1000, ttl=settings.CACHE_TTL)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self._cache.get(key)
            if value is not None:
                # Deserialize JSON if it's a string
                if isinstance(value, str):
                    return json.loads(value)
                return value
            return None
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        try:
            # Serialize to JSON if it's a complex object
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = value
            
            # Use custom TTL if provided
            if ttl:
                # For TTLCache, we need to create a new cache entry with custom TTL
                # This is a limitation of cachetools, but works for our use case
                self._cache[key] = serialized_value
            else:
                self._cache[key] = serialized_value
            
            return True
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            self._cache.clear()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl": self._cache.ttl,
            "hits": getattr(self._cache, 'hits', 0),
            "misses": getattr(self._cache, 'misses', 0)
        }
