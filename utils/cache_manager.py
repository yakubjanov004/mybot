import asyncio
import json
import time
from typing import Any, Dict, Optional, Set
from datetime import datetime, timedelta
import weakref
from utils.logger import setup_module_logger

logger = setup_module_logger("cache_manager")

class MemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry['expires_at'] < time.time():
                await self._delete(key)
                return None
            
            # Update access time
            self._access_times[key] = time.time()
            logger.debug(f"Cache hit: {key}")
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            ttl = ttl or self._default_ttl
            expires_at = time.time() + ttl
            
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            self._access_times[key] = time.time()
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            return await self._delete(key)
    
    async def _delete(self, key: str) -> bool:
        """Internal delete method"""
        if key in self._cache:
            del self._cache[key]
            self._access_times.pop(key, None)
            logger.debug(f"Cache delete: {key}")
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries"""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry['expires_at'] < current_time
            ]
            
            for key in expired_keys:
                await self._delete(key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            current_time = time.time()
            total_entries = len(self._cache)
            expired_entries = sum(
                1 for entry in self._cache.values()
                if entry['expires_at'] < current_time
            )
            
            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_entries,
                'expired_entries': expired_entries,
                'memory_usage_kb': len(str(self._cache)) / 1024
            }

# Global cache instance
cache = MemoryCache()

# Cache key generators
def user_cache_key(telegram_id: int) -> str:
    """Generate cache key for user data"""
    return f"user:{telegram_id}"

def zayavka_cache_key(zayavka_id: int) -> str:
    """Generate cache key for zayavka data"""
    return f"zayavka:{zayavka_id}"

def user_zayavkas_cache_key(user_id: int) -> str:
    """Generate cache key for user's zayavkas"""
    return f"user_zayavkas:{user_id}"

def technician_tasks_cache_key(technician_id: int) -> str:
    """Generate cache key for technician tasks"""
    return f"technician_tasks:{technician_id}"

def statistics_cache_key(stat_type: str, period: str = "daily") -> str:
    """Generate cache key for statistics"""
    return f"stats:{stat_type}:{period}"

def materials_cache_key() -> str:
    """Generate cache key for materials list"""
    return "materials:all"

# Cache decorators
def cached(ttl: int = 300, key_func=None):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = await cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

# Cache invalidation helpers
async def invalidate_user_cache(telegram_id: int):
    """Invalidate all cache entries for a user"""
    keys_to_delete = [
        user_cache_key(telegram_id),
        user_zayavkas_cache_key(telegram_id),
    ]
    
    for key in keys_to_delete:
        await cache.delete(key)
    
    logger.info(f"Invalidated cache for user {telegram_id}")

async def invalidate_zayavka_cache(zayavka_id: int, user_id: int = None):
    """Invalidate cache entries for a zayavka"""
    keys_to_delete = [zayavka_cache_key(zayavka_id)]
    
    if user_id:
        keys_to_delete.append(user_zayavkas_cache_key(user_id))
    
    for key in keys_to_delete:
        await cache.delete(key)
    
    logger.info(f"Invalidated cache for zayavka {zayavka_id}")

async def invalidate_statistics_cache():
    """Invalidate all statistics cache"""
    # This is a simple approach - in production you might want to track stat keys
    await cache.clear()
    logger.info("Invalidated statistics cache")

# Cache maintenance task
async def cache_maintenance():
    """Background task for cache maintenance"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            cleaned = await cache.cleanup_expired()
            
            # Log stats periodically
            stats = await cache.get_stats()
            if stats['total_entries'] > 0:
                logger.debug(f"Cache stats: {stats}")
            
        except Exception as e:
            logger.error(f"Cache maintenance error: {str(e)}")

# Context manager for cache operations
class CacheContext:
    """Context manager for cache operations with automatic cleanup"""
    
    def __init__(self, keys_to_invalidate: list = None):
        self.keys_to_invalidate = keys_to_invalidate or []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # Only invalidate on success
            for key in self.keys_to_invalidate:
                await cache.delete(key)

# Utility functions
async def warm_cache():
    """Warm up cache with frequently accessed data"""
    try:
        from database.base_queries import get_user_statistics, get_zayavka_statistics
        
        # Cache statistics
        user_stats = await get_user_statistics()
        await cache.set(statistics_cache_key("users"), user_stats, 600)
        
        zayavka_stats = await get_zayavka_statistics()
        await cache.set(statistics_cache_key("zayavkas"), zayavka_stats, 600)
        
        logger.info("Cache warmed up successfully")
        
    except Exception as e:
        logger.error(f"Cache warm-up failed: {str(e)}")

async def get_cache_info() -> Dict[str, Any]:
    """Get comprehensive cache information"""
    stats = await cache.get_stats()
    
    return {
        'cache_stats': stats,
        'default_ttl': cache._default_ttl,
        'maintenance_running': True  # Simplified check
    }
