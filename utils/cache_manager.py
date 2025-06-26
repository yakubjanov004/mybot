import time
import json
from typing import Any, Dict, Optional, Union, List
from collections import OrderedDict
import asyncio
from utils.logger import logger

class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: OrderedDict = OrderedDict()
        self.ttl_data: Dict[str, float] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.ttl_data:
            return True
        return time.time() > self.ttl_data[key]
    
    def _evict_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self.ttl_data.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self._delete_key(key)
    
    def _delete_key(self, key: str):
        """Delete a key from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl_data:
            del self.ttl_data[key]
    
    def _evict_lru(self):
        """Evict least recently used items"""
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            self._delete_key(oldest_key)
            self.stats['evictions'] += 1
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        self._evict_expired()
        
        if key not in self.cache or self._is_expired(key):
            self.stats['misses'] += 1
            return default
        
        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.stats['hits'] += 1
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            self._evict_expired()
            self._evict_lru()
            
            # Set TTL
            if ttl is None:
                ttl = self.default_ttl
            
            self.ttl_data[key] = time.time() + ttl
            self.cache[key] = value
            
            # Move to end
            self.cache.move_to_end(key)
            
            self.stats['sets'] += 1
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            self._delete_key(key)
            self.stats['deletes'] += 1
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        self._evict_expired()
        return key in self.cache and not self._is_expired(key)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.ttl_data.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._evict_expired()
        
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'evictions': self.stats['evictions']
        }
    
    def get_keys(self, pattern: str = None) -> List[str]:
        """Get all keys, optionally filtered by pattern"""
        self._evict_expired()
        
        keys = list(self.cache.keys())
        if pattern:
            import fnmatch
            keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
        
        return keys

# Specialized cache managers
class UserCache(CacheManager):
    """Cache for user data"""
    
    def __init__(self):
        super().__init__(max_size=500, default_ttl=600)  # 10 minutes
    
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user data from cache"""
        return self.get(f"user:{telegram_id}")
    
    def set_user(self, telegram_id: int, user_data: Dict, ttl: int = None) -> bool:
        """Set user data in cache"""
        return self.set(f"user:{telegram_id}", user_data, ttl)
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user from cache"""
        return self.delete(f"user:{telegram_id}")
    
    def get_user_role(self, telegram_id: int) -> Optional[str]:
        """Get user role from cache"""
        user_data = self.get_user(telegram_id)
        return user_data.get('role') if user_data else None

class ZayavkaCache(CacheManager):
    """Cache for zayavka data"""
    
    def __init__(self):
        super().__init__(max_size=1000, default_ttl=300)  # 5 minutes
    
    def get_zayavka(self, zayavka_id: int) -> Optional[Dict]:
        """Get zayavka data from cache"""
        return self.get(f"zayavka:{zayavka_id}")
    
    def set_zayavka(self, zayavka_id: int, zayavka_data: Dict, ttl: int = None) -> bool:
        """Set zayavka data in cache"""
        return self.set(f"zayavka:{zayavka_id}", zayavka_data, ttl)
    
    def delete_zayavka(self, zayavka_id: int) -> bool:
        """Delete zayavka from cache"""
        return self.delete(f"zayavka:{zayavka_id}")
    
    def get_user_zayavkas(self, user_id: int) -> Optional[List]:
        """Get user's zayavkas from cache"""
        return self.get(f"user_zayavkas:{user_id}")
    
    def set_user_zayavkas(self, user_id: int, zayavkas: List, ttl: int = None) -> bool:
        """Set user's zayavkas in cache"""
        return self.set(f"user_zayavkas:{user_id}", zayavkas, ttl)

class ConfigCache(CacheManager):
    """Cache for configuration data"""
    
    def __init__(self):
        super().__init__(max_size=100, default_ttl=3600)  # 1 hour
    
    def get_config(self, key: str) -> Any:
        """Get configuration value"""
        return self.get(f"config:{key}")
    
    def set_config(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set configuration value"""
        return self.set(f"config:{key}", value, ttl)

# Global cache instances
user_cache = UserCache()
zayavka_cache = ZayavkaCache()
config_cache = ConfigCache()
general_cache = CacheManager()

# Cache decorators
def cache_result(cache_key_func, ttl: int = 300, cache_instance: CacheManager = None):
    """Decorator to cache function results"""
    if cache_instance is None:
        cache_instance = general_cache
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                cache_instance.set(cache_key, result, ttl)
                logger.debug(f"Cached result for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator

def invalidate_cache(cache_key_func, cache_instance: CacheManager = None):
    """Decorator to invalidate cache after function execution"""
    if cache_instance is None:
        cache_instance = general_cache
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            cache_key = cache_key_func(*args, **kwargs)
            cache_instance.delete(cache_key)
            logger.debug(f"Invalidated cache for key: {cache_key}")
            
            return result
        
        return wrapper
    return decorator

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

# Cache maintenance
async def cache_maintenance():
    """Periodic cache maintenance task"""
    while True:
        try:
            # Clean expired entries
            user_cache._evict_expired()
            zayavka_cache._evict_expired()
            config_cache._evict_expired()
            general_cache._evict_expired()
            
            # Log cache stats
            logger.info(f"Cache stats - Users: {user_cache.get_stats()}")
            logger.info(f"Cache stats - Zayavkas: {zayavka_cache.get_stats()}")
            
            # Wait 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Cache maintenance error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute on error
