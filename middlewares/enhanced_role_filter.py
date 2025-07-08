from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Union
import logging
from utils.get_role import get_user_role

logger = logging.getLogger(__name__)

class EnhancedRoleFilterMiddleware(BaseMiddleware):
    """
    Enhanced middleware that provides better role-based filtering
    and prevents handler conflicts between roles.
    """
    
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        try:
            # Get user role
            user = getattr(event, "from_user", None)
            if not user:
                return await handler(event, data)
            
            user_role = await get_user_role(user.id)
            
            # Add role information to handler data
            data['user_role'] = user_role
            data['user_capabilities'] = await self._get_user_capabilities(user_role)
            
            # Continue with handler execution
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Enhanced role filter middleware error: {str(e)}")
            return await handler(event, data)
    
    async def _get_user_capabilities(self, role: str) -> dict:
        """Get user capabilities based on role"""
        from utils.get_role import ROLE_PERMISSIONS, get_role_level
        
        permissions = ROLE_PERMISSIONS.get(role, [])
        
        return {
            'role': role,
            'level': get_role_level(role),
            'permissions': permissions,
            'can_manage_users': 'manage_users' in permissions,
            'can_view_all_zayavkas': 'view_all_zayavkas' in permissions,
            'can_assign_tasks': 'assign_tasks' in permissions,
            'can_manage_materials': 'manage_materials' in permissions
        }
