from aiogram import BaseMiddleware, Router
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Union, Optional, Awaitable
import logging
from utils.get_role import get_user_role
from config import config
from database.base_queries import get_user_by_telegram_id
from utils.logger import setup_logger

logger = setup_logger('bot.role_routing')

class RoleRoutingMiddleware(BaseMiddleware):
    """
    Middleware that routes messages to role-specific routers before normal Aiogram processing.
    This prevents role mismatch errors when multiple roles have handlers for the same text.
    """
    
    def __init__(self):
        self.role_routers: Dict[str, Router] = {}
        self.global_router: Optional[Router] = None
        
    def register_role_router(self, role: str, router: Router):
        """Register a role-specific router"""
        self.role_routers[role] = router
        logger.info(f"Registered router for role: {role}")
    
    def register_global_router(self, router: Router):
        """Register the global navigation router"""
        self.global_router = router
        logger.debug("Registered global navigation router")
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Get user info for role-based routing
        user_id = None
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
            
        if user_id:
            try:
                user = await get_user_by_telegram_id(user_id)
                if user:
                    data['user_role'] = user.get('role', 'client')
                    data['user_data'] = user
                else:
                    data['user_role'] = 'client'  # Default role
                    data['user_data'] = None
            except Exception as e:
                logger.error(f"Error getting user role: {e}")
                data['user_role'] = 'client'
                data['user_data'] = None
        
        try:
            # Get user info
            user = getattr(event, "from_user", None)
            if not user:
                return await handler(event, data)
            
            user_id = user.id
            user_role = data.get('user_role', 'client')
            
            if config.DEVELOPMENT:
                event_text = getattr(event, 'text', None) or getattr(event, 'data', None)
                logger.debug(
                    f"[RoleRoutingMiddleware] user_id={user_id}, role={user_role}, "
                    f"event_type={type(event).__name__}, text/data={event_text}"
                )
            
            # Check if we have a role-specific router for this user's role
            role_router = self.role_routers.get(user_role)
            
            if role_router:
                # Try to handle with role-specific router first
                try:
                    # Create a temporary dispatcher to test if the role router can handle this event
                    from aiogram import Dispatcher
                    from aiogram.fsm.storage.memory import MemoryStorage
                    
                    temp_dp = Dispatcher(storage=MemoryStorage())
                    temp_dp.include_router(role_router)
                    
                    # Check if any handler in the role router matches this event
                    if isinstance(event, Message):
                        handlers = role_router.message.handlers
                    elif isinstance(event, CallbackQuery):
                        handlers = role_router.callback_query.handlers
                    else:
                        handlers = []
                    
                    # If we have matching handlers, let the role router handle it
                    if handlers:
                        for handler_obj in handlers:
                            # Check if this handler's filters match the event
                            try:
                                if hasattr(handler_obj, 'filters'):
                                    # This is a simplified check - in practice, Aiogram does more complex matching
                                    can_handle = True
                                    for filter_obj in handler_obj.filters:
                                        if hasattr(filter_obj, '__call__'):
                                            try:
                                                filter_result = await filter_obj(event)
                                                if not filter_result:
                                                    can_handle = False
                                                    break
                                            except Exception:
                                                can_handle = False
                                                break
                                    
                                    if can_handle:
                                        if config.DEVELOPMENT:
                                            logger.debug(f"[RoleRoutingMiddleware] Routing to {user_role} router")
                                        # Let the normal handler processing continue
                                        return await handler(event, data)
                            except Exception as e:
                                if config.DEVELOPMENT:
                                    logger.debug(f"[RoleRoutingMiddleware] Filter check error: {e}")
                                continue
                
                except Exception as e:
                    if config.DEVELOPMENT:
                        logger.debug(f"[RoleRoutingMiddleware] Role router check failed: {e}")
            
            # If global router exists, check if it should handle this
            if self.global_router:
                try:
                    # Global router handles navigation commands that work for all roles
                    if isinstance(event, Message):
                        text = event.text
                        if text and (text.startswith('/') or text in ['🏠 Bosh menyu', '🏠 Главное меню', '⬅️ Orqaga', '⬅️ Назад']):
                            if config.DEVELOPMENT:
                                logger.debug("[RoleRoutingMiddleware] Routing to global router")
                            return await handler(event, data)
                    elif isinstance(event, CallbackQuery):
                        data_str = event.data
                        if data_str and (data_str.startswith('main_menu') or data_str.startswith('back_to')):
                            if config.DEVELOPMENT:
                                logger.debug("[RoleRoutingMiddleware] Routing to global router")
                            return await handler(event, data)
                except Exception as e:
                    if config.DEVELOPMENT:
                        logger.debug(f"[RoleRoutingMiddleware] Global router check failed: {e}")
            
            # Continue with normal processing
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"[RoleRoutingMiddleware] Error: {str(e)}", exc_info=True)
            # Continue with normal processing on error
            return await handler(event, data)

# Global instance
role_routing_middleware = RoleRoutingMiddleware()
