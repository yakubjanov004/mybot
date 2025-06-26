import time
from typing import Dict, Optional
from collections import defaultdict, deque
import asyncio
from utils.logger import logger

class RateLimiter:
    """Rate limiting utility for bot operations"""
    
    def __init__(self):
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        self.global_requests: deque = deque()
        self.blocked_users: Dict[int, float] = {}
        
        # Rate limits
        self.USER_LIMIT = 10  # requests per minute per user
        self.GLOBAL_LIMIT = 100  # requests per minute globally
        self.BLOCK_DURATION = 300  # 5 minutes block
        
    def is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            if current_time < self.blocked_users[user_id]:
                return True
            else:
                del self.blocked_users[user_id]
        
        # Clean old requests (older than 1 minute)
        minute_ago = current_time - 60
        
        # Clean user requests
        user_queue = self.user_requests[user_id]
        while user_queue and user_queue[0] < minute_ago:
            user_queue.popleft()
        
        # Clean global requests
        while self.global_requests and self.global_requests[0] < minute_ago:
            self.global_requests.popleft()
        
        # Check limits
        if len(user_queue) >= self.USER_LIMIT:
            self.blocked_users[user_id] = current_time + self.BLOCK_DURATION
            logger.warning(f"User {user_id} rate limited for {self.BLOCK_DURATION} seconds")
            return True
        
        if len(self.global_requests) >= self.GLOBAL_LIMIT:
            logger.warning("Global rate limit reached")
            return True
        
        # Add current request
        user_queue.append(current_time)
        self.global_requests.append(current_time)
        
        return False
    
    def get_remaining_block_time(self, user_id: int) -> Optional[int]:
        """Get remaining block time for user"""
        if user_id in self.blocked_users:
            remaining = int(self.blocked_users[user_id] - time.time())
            return max(0, remaining)
        return None
    
    def unblock_user(self, user_id: int) -> bool:
        """Manually unblock user"""
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
            logger.info(f"User {user_id} manually unblocked")
            return True
        return False
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Count active requests
        active_users = 0
        total_user_requests = 0
        
        for user_id, requests in self.user_requests.items():
            recent_requests = [r for r in requests if r > minute_ago]
            if recent_requests:
                active_users += 1
                total_user_requests += len(recent_requests)
        
        global_requests = len([r for r in self.global_requests if r > minute_ago])
        blocked_users = len(self.blocked_users)
        
        return {
            'active_users': active_users,
            'total_user_requests': total_user_requests,
            'global_requests': global_requests,
            'blocked_users': blocked_users,
            'user_limit': self.USER_LIMIT,
            'global_limit': self.GLOBAL_LIMIT
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit_check(func):
    """Decorator to check rate limits"""
    async def wrapper(message_or_call, *args, **kwargs):
        user_id = None
        
        # Get user_id from message or callback
        if hasattr(message_or_call, 'from_user'):
            user_id = message_or_call.from_user.id
        elif hasattr(message_or_call, 'message') and hasattr(message_or_call.message, 'from_user'):
            user_id = message_or_call.message.from_user.id
        
        if user_id and rate_limiter.is_rate_limited(user_id):
            remaining_time = rate_limiter.get_remaining_block_time(user_id)
            if remaining_time:
                if hasattr(message_or_call, 'answer'):
                    await message_or_call.answer(
                        f"⚠️ Siz juda ko'p so'rov yubordingiz. {remaining_time} soniyadan keyin qayta urinib ko'ring.",
                        show_alert=True
                    )
                elif hasattr(message_or_call, 'reply'):
                    await message_or_call.reply(
                        f"⚠️ Siz juda ko'p so'rov yubordingiz. {remaining_time} soniyadan keyin qayta urinib ko'ring."
                    )
            return
        
        return await func(message_or_call, *args, **kwargs)
    
    return wrapper
