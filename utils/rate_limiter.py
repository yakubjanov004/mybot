import asyncio
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
from utils.logger import setup_module_logger

logger = setup_module_logger("rate_limiter")

class RateLimiter:
    """Rate limiter with sliding window algorithm"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()
            
            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(current_time)
                return True
            
            return False
    
    async def get_reset_time(self, key: str) -> Optional[float]:
        """Get time when rate limit resets"""
        async with self._lock:
            if key not in self.requests or not self.requests[key]:
                return None
            
            oldest_request = self.requests[key][0]
            return oldest_request + self.window_seconds
    
    async def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests in current window"""
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.window_seconds
            
            # Clean old requests
            while self.requests[key] and self.requests[key][0] < window_start:
                self.requests[key].popleft()
            
            return max(0, self.max_requests - len(self.requests[key]))
    
    async def clear_user(self, key: str):
        """Clear rate limit for specific key"""
        async with self._lock:
            if key in self.requests:
                del self.requests[key]
    
    async def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        async with self._lock:
            total_keys = len(self.requests)
            total_requests = sum(len(requests) for requests in self.requests.values())
            
            return {
                'total_keys': total_keys,
                'total_active_requests': total_requests,
                'max_requests_per_window': self.max_requests,
                'window_seconds': self.window_seconds
            }

class UserRateLimiter:
    """User-specific rate limiter with different limits for different actions"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {
            'message': RateLimiter(max_requests=30, window_seconds=60),  # 30 messages per minute
            'callback': RateLimiter(max_requests=60, window_seconds=60),  # 60 callbacks per minute
            'zayavka_create': RateLimiter(max_requests=5, window_seconds=300),  # 5 zayavkas per 5 minutes
            'file_upload': RateLimiter(max_requests=10, window_seconds=300),  # 10 files per 5 minutes
            'search': RateLimiter(max_requests=20, window_seconds=60),  # 20 searches per minute
            'export': RateLimiter(max_requests=3, window_seconds=600),  # 3 exports per 10 minutes
        }
        self.user_warnings: Dict[int, int] = defaultdict(int)
        self.blocked_users: Dict[int, float] = {}  # user_id -> unblock_time
    
    async def check_rate_limit(self, user_id: int, action: str) -> Tuple[bool, Optional[str]]:
        """Check rate limit for user action"""
        # Check if user is temporarily blocked
        if user_id in self.blocked_users:
            if time.time() < self.blocked_users[user_id]:
                remaining = int(self.blocked_users[user_id] - time.time())
                return False, f"Вы временно заблокированы. Осталось: {remaining} сек"
            else:
                del self.blocked_users[user_id]
                self.user_warnings[user_id] = 0
        
        # Check specific action rate limit
        if action in self.limiters:
            key = f"{user_id}:{action}"
            allowed = await self.limiters[action].is_allowed(key)
            
            if not allowed:
                # Increment warning count
                self.user_warnings[user_id] += 1
                
                # Block user if too many warnings
                if self.user_warnings[user_id] >= 5:
                    block_duration = min(300 * (self.user_warnings[user_id] - 4), 3600)  # Max 1 hour
                    self.blocked_users[user_id] = time.time() + block_duration
                    logger.warning(f"User {user_id} blocked for {block_duration} seconds due to rate limiting")
                    return False, f"Вы заблокированы на {block_duration // 60} минут за превышение лимитов"
                
                # Get reset time
                reset_time = await self.limiters[action].get_reset_time(key)
                if reset_time:
                    remaining = int(reset_time - time.time())
                    return False, f"Превышен лимит. Попробуйте через {remaining} сек"
                
                return False, "Превышен лимит запросов"
        
        return True, None
    
    async def get_user_limits(self, user_id: int) -> Dict[str, Dict]:
        """Get current limits for user"""
        limits = {}
        
        for action, limiter in self.limiters.items():
            key = f"{user_id}:{action}"
            remaining = await limiter.get_remaining_requests(key)
            reset_time = await limiter.get_reset_time(key)
            
            limits[action] = {
                'max_requests': limiter.max_requests,
                'window_seconds': limiter.window_seconds,
                'remaining': remaining,
                'reset_time': reset_time,
                'reset_in_seconds': int(reset_time - time.time()) if reset_time else 0
            }
        
        return limits
    
    async def clear_user_limits(self, user_id: int):
        """Clear all limits for user (admin function)"""
        for action, limiter in self.limiters.items():
            key = f"{user_id}:{action}"
            await limiter.clear_user(key)
        
        if user_id in self.user_warnings:
            del self.user_warnings[user_id]
        
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
        
        logger.info(f"Cleared all rate limits for user {user_id}")
    
    async def get_blocked_users(self) -> Dict[int, int]:
        """Get currently blocked users"""
        current_time = time.time()
        blocked = {}
        
        for user_id, unblock_time in self.blocked_users.items():
            if unblock_time > current_time:
                blocked[user_id] = int(unblock_time - current_time)
        
        return blocked
    
    async def unblock_user(self, user_id: int) -> bool:
        """Manually unblock user"""
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
            self.user_warnings[user_id] = 0
            logger.info(f"Manually unblocked user {user_id}")
            return True
        return False

# Global rate limiter instance
user_rate_limiter = UserRateLimiter()

# Decorator for rate limiting
def rate_limit(action: str):
    """Decorator to apply rate limiting to handlers"""
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            user_id = message_or_callback.from_user.id
            
            allowed, error_message = await user_rate_limiter.check_rate_limit(user_id, action)
            
            if not allowed:
                try:
                    if hasattr(message_or_callback, 'answer'):
                        await message_or_callback.answer(error_message, show_alert=True)
                    else:
                        await message_or_callback.reply(error_message)
                except Exception as e:
                    logger.error(f"Error sending rate limit message: {str(e)}")
                return
            
            return await func(message_or_callback, *args, **kwargs)
        
        return wrapper
    return decorator

# Context manager for rate limiting
class RateLimitContext:
    """Context manager for rate limiting operations"""
    
    def __init__(self, user_id: int, action: str):
        self.user_id = user_id
        self.action = action
        self.allowed = False
        self.error_message = None
    
    async def __aenter__(self):
        self.allowed, self.error_message = await user_rate_limiter.check_rate_limit(
            self.user_id, self.action
        )
        return self.allowed, self.error_message
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Utility functions
async def check_user_rate_limit(user_id: int, action: str) -> Tuple[bool, Optional[str]]:
    """Check rate limit for user action"""
    return await user_rate_limiter.check_rate_limit(user_id, action)

async def get_user_rate_limits(user_id: int) -> Dict[str, Dict]:
    """Get user rate limits"""
    return await user_rate_limiter.get_user_limits(user_id)

async def clear_user_rate_limits(user_id: int):
    """Clear user rate limits (admin function)"""
    await user_rate_limiter.clear_user_limits(user_id)

async def get_blocked_users() -> Dict[int, int]:
    """Get blocked users"""
    return await user_rate_limiter.get_blocked_users()

async def unblock_user(user_id: int) -> bool:
    """Unblock user"""
    return await user_rate_limiter.unblock_user(user_id)

# Admin rate limiter (more permissive)
class AdminRateLimiter(UserRateLimiter):
    """Rate limiter with higher limits for admin users"""
    
    def __init__(self):
        super().__init__()
        # Override with higher limits for admins
        self.limiters = {
            'message': RateLimiter(max_requests=100, window_seconds=60),
            'callback': RateLimiter(max_requests=200, window_seconds=60),
            'zayavka_create': RateLimiter(max_requests=50, window_seconds=300),
            'file_upload': RateLimiter(max_requests=50, window_seconds=300),
            'search': RateLimiter(max_requests=100, window_seconds=60),
            'export': RateLimiter(max_requests=20, window_seconds=600),
        }

# Role-based rate limiter
class RoleBasedRateLimiter:
    """Rate limiter that applies different limits based on user role"""
    
    def __init__(self):
        self.role_limiters = {
            'client': UserRateLimiter(),
            'technician': UserRateLimiter(),
            'admin': AdminRateLimiter(),
            'manager': AdminRateLimiter(),
            'junior_manager': AdminRateLimiter(),
            'call_center': UserRateLimiter(),
            'warehouse': UserRateLimiter(),
            'controller': UserRateLimiter()
        }
    
    async def check_rate_limit(self, user_id: int, user_role: str, action: str) -> Tuple[bool, Optional[str]]:
        """Check rate limit based on user role"""
        limiter = self.role_limiters.get(user_role, self.role_limiters['client'])
        return await limiter.check_rate_limit(user_id, action)
    
    async def get_user_limits(self, user_id: int, user_role: str) -> Dict[str, Dict]:
        """Get user limits based on role"""
        limiter = self.role_limiters.get(user_role, self.role_limiters['client'])
        return await limiter.get_user_limits(user_id)
    
    async def clear_user_limits(self, user_id: int, user_role: str):
        """Clear user limits based on role"""
        limiter = self.role_limiters.get(user_role, self.role_limiters['client'])
        await limiter.clear_user_limits(user_id)

# Global role-based rate limiter
role_rate_limiter = RoleBasedRateLimiter()

# Background cleanup task
async def cleanup_expired_limits():
    """Background task to cleanup expired rate limit data"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            current_time = time.time()
            
            # Clean up blocked users
            expired_blocks = [
                user_id for user_id, unblock_time in user_rate_limiter.blocked_users.items()
                if unblock_time <= current_time
            ]
            
            for user_id in expired_blocks:
                del user_rate_limiter.blocked_users[user_id]
                user_rate_limiter.user_warnings[user_id] = 0
            
            if expired_blocks:
                logger.info(f"Cleaned up {len(expired_blocks)} expired user blocks")
            
        except Exception as e:
            logger.error(f"Error in rate limiter cleanup: {str(e)}")

# Rate limit monitoring
class RateLimitMonitor:
    """Monitor rate limiting statistics"""
    
    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'blocked_users_count': 0,
            'top_blocked_actions': defaultdict(int)
        }
    
    def record_request(self, action: str, blocked: bool = False):
        """Record rate limit request"""
        self.stats['total_requests'] += 1
        if blocked:
            self.stats['blocked_requests'] += 1
            self.stats['top_blocked_actions'][action] += 1
    
    def record_user_block(self):
        """Record user block"""
        self.stats['blocked_users_count'] += 1
    
    def get_stats(self) -> Dict:
        """Get monitoring statistics"""
        return dict(self.stats)
    
    def reset_stats(self):
        """Reset monitoring statistics"""
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'blocked_users_count': 0,
            'top_blocked_actions': defaultdict(int)
        }

# Global monitor
rate_limit_monitor = RateLimitMonitor()
