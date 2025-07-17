from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Union
import logging
from utils.get_role import get_user_role
from utils.workflow_access_control import WorkflowAccessControl

logger = logging.getLogger(__name__)

class EnhancedRoleFilterMiddleware(BaseMiddleware):
    """
    Enhanced middleware that provides comprehensive role-based filtering
    with workflow access control integration
    """
    
    def __init__(self):
        self.access_control = WorkflowAccessControl()
    
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        try:
            # Get user information
            user = getattr(event, "from_user", None)
            if not user:
                return await handler(event, data)
            
            user_role = await get_user_role(user.id)
            
            # Add comprehensive role information to handler data
            data['user_id'] = user.id
            data['user_role'] = user_role
            data['user_capabilities'] = await self._get_user_capabilities(user.id, user_role)
            data['access_control'] = self.access_control
            
            # Log user activity for audit trail
            await self._log_user_activity(user.id, user_role, event)
            
            # Continue with handler execution
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Enhanced role filter middleware error: {str(e)}")
            return await handler(event, data)
    
    async def _get_user_capabilities(self, user_id: int, role: str) -> dict:
        """Get comprehensive user capabilities including workflow permissions"""
        try:
            # Get workflow-based permissions
            workflow_permissions = await self.access_control.get_user_permissions(user_id, role)
            
            # Get legacy permissions for backward compatibility
            legacy_permissions = await self._get_legacy_capabilities(role)
            
            return {
                **legacy_permissions,
                'workflow_permissions': workflow_permissions,
                'user_id': user_id,
                'role': role
            }
            
        except Exception as e:
            logger.error(f"Error getting user capabilities: {e}")
            return {'role': role, 'error': str(e)}
    
    async def _get_legacy_capabilities(self, role: str) -> dict:
        """Get legacy capabilities for backward compatibility"""
        try:
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
        except Exception as e:
            logger.error(f"Error getting legacy capabilities: {e}")
            return {'role': role}
    
    async def _log_user_activity(self, user_id: int, user_role: str, event: Union[Message, CallbackQuery]):
        """Log user activity for audit purposes"""
        try:
            if isinstance(event, Message):
                activity_type = "message"
                activity_detail = f"text:{event.text[:50]}..." if event.text else "non_text_message"
            elif isinstance(event, CallbackQuery):
                activity_type = "callback"
                activity_detail = f"data:{event.data}" if event.data else "no_data"
            else:
                activity_type = "unknown"
                activity_detail = str(type(event))
            
            # Log to access control system
            await self.access_control.log_access_attempt(
                user_id=user_id,
                action=f"user_activity_{activity_type}",
                resource=activity_detail,
                granted=True,
                reason=f"User {user_role} activity logged"
            )
            
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")


class WorkflowAccessMiddleware(BaseMiddleware):
    """
    Middleware specifically for workflow access control validation
    """
    
    def __init__(self):
        self.access_control = WorkflowAccessControl()
    
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        try:
            # Skip if not a workflow-related handler
            if not self._is_workflow_handler(handler):
                return await handler(event, data)
            
            # Get user information
            user = getattr(event, "from_user", None)
            if not user:
                return await handler(event, data)
            
            user_role = data.get('user_role') or await get_user_role(user.id)
            
            # Extract workflow action from callback data or handler name
            workflow_action = self._extract_workflow_action(event, handler)
            if not workflow_action:
                return await handler(event, data)
            
            # Extract request ID if available
            request_id = self._extract_request_id(event, data)
            
            # Validate workflow access
            valid, reason = await self.access_control.validate_workflow_action(
                user_id=user.id,
                user_role=user_role,
                action=workflow_action,
                request_id=request_id,
                target_data=data
            )
            
            if not valid:
                # Send access denied message
                await self._send_access_denied_message(event, reason, user_role)
                return None
            
            # Access granted, continue with handler
            data['workflow_action'] = workflow_action
            data['request_id'] = request_id
            return await handler(event, data)
            
        except Exception as e:
            logger.error(f"Workflow access middleware error: {str(e)}")
            return await handler(event, data)
    
    def _is_workflow_handler(self, handler: Callable) -> bool:
        """Check if handler is workflow-related"""
        handler_name = getattr(handler, '__name__', '')
        workflow_keywords = [
            'workflow', 'request', 'assign', 'transition', 
            'technician', 'manager', 'controller', 'warehouse'
        ]
        return any(keyword in handler_name.lower() for keyword in workflow_keywords)
    
    def _extract_workflow_action(self, event: Union[Message, CallbackQuery], handler: Callable) -> str:
        """Extract workflow action from event or handler"""
        if isinstance(event, CallbackQuery) and event.data:
            # Try to extract action from callback data
            callback_parts = event.data.split('_')
            if len(callback_parts) >= 2:
                return '_'.join(callback_parts[:2])
        
        # Fallback to handler name analysis
        handler_name = getattr(handler, '__name__', '')
        if 'assign' in handler_name:
            return 'assign_request'
        elif 'complete' in handler_name:
            return 'complete_request'
        elif 'start' in handler_name:
            return 'start_task'
        
        return None
    
    def _extract_request_id(self, event: Union[Message, CallbackQuery], data: Dict[str, Any]) -> str:
        """Extract request ID from event or data"""
        # Try callback data first
        if isinstance(event, CallbackQuery) and event.data:
            parts = event.data.split('_')
            for part in parts:
                if len(part) > 10 and '-' in part:  # UUID-like format
                    return part
        
        # Try from handler data
        return data.get('request_id')
    
    async def _send_access_denied_message(self, event: Union[Message, CallbackQuery], 
                                        reason: str, user_role: str):
        """Send access denied message to user"""
        try:
            # Get user language
            from database.base_queries import get_user_lang
            user_id = event.from_user.id
            
            try:
                lang = await get_user_lang(user_id)
            except:
                lang = 'ru'
            
            if lang == 'uz':
                error_text = f"❌ Ruxsat berilmadi!\n\nSabab: {reason}\n\nSizning rolingiz: {user_role}"
            else:
                error_text = f"❌ Доступ запрещен!\n\nПричина: {reason}\n\nВаша роль: {user_role}"
            
            if isinstance(event, Message):
                await event.answer(error_text)
            else:  # CallbackQuery
                await event.answer(error_text, show_alert=True)
                
        except Exception as e:
            logger.error(f"Error sending access denied message: {e}")
