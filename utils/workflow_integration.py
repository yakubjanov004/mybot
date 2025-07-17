"""
Workflow Integration Utilities
Provides helper functions and decorators to integrate existing handlers with the workflow system
"""

import functools
from typing import Optional, Dict, Any, Callable
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.models import UserRole, WorkflowType, WorkflowAction
from database.base_queries import get_user_by_telegram_id
from utils.logger import setup_module_logger

logger = setup_module_logger("workflow_integration")


class WorkflowIntegration:
    """Helper class for integrating existing handlers with workflow system"""
    
    @staticmethod
    async def get_workflow_manager():
        """Get the workflow manager from bot instance"""
        try:
            from loader import bot
            return getattr(bot, 'workflow_engine', None)
        except ImportError:
            logger.error("Could not import bot instance")
            return None
    
    @staticmethod
    async def get_state_manager():
        """Get the state manager from bot instance"""
        try:
            from loader import bot
            return getattr(bot, 'state_manager', None)
        except ImportError:
            logger.error("Could not import bot instance")
            return None
    
    @staticmethod
    async def get_notification_system():
        """Get the notification system from bot instance"""
        try:
            from loader import bot
            return getattr(bot, 'notification_system', None)
        except ImportError:
            logger.error("Could not import bot instance")
            return None
    
    @staticmethod
    async def get_inventory_manager():
        """Get the inventory manager from bot instance"""
        try:
            from loader import bot
            return getattr(bot, 'inventory_manager', None)
        except ImportError:
            logger.error("Could not import bot instance")
            return None
    
    @staticmethod
    async def create_workflow_request(workflow_type: str, user_id: int, request_data: Dict[str, Any]) -> Optional[str]:
        """Create a new workflow request with staff creation context support"""
        try:
            workflow_engine = await WorkflowIntegration.get_workflow_manager()
            if not workflow_engine:
                logger.error("Workflow engine not available")
                return None
            
            # Get user info
            user = await get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return None
            
            # Determine if this is a staff-created application
            user_role = user.get('role', UserRole.CLIENT.value)
            is_staff_created = user_role in [
                UserRole.MANAGER.value, 
                UserRole.JUNIOR_MANAGER.value, 
                UserRole.CONTROLLER.value, 
                UserRole.CALL_CENTER.value
            ]
            
            # Add user info to request data
            if is_staff_created:
                # For staff-created applications, the client_id should be different from the creator
                client_id = request_data.get('client_id')  # Should be provided by staff creation handler
                if not client_id:
                    logger.error("Staff-created application missing client_id")
                    return None
                
                request_data.update({
                    'client_id': client_id,
                    'created_by_role': user_role,
                    'created_by_staff': True,
                    'staff_creator_info': {
                        'creator_id': user['id'],
                        'creator_role': user_role,
                        'creator_name': user.get('full_name', 'Unknown Staff'),
                        'creator_telegram_id': user_id
                    }
                })
            else:
                # Regular client-created application
                request_data.update({
                    'client_id': user['id'],
                    'created_by_role': user_role,
                    'created_by_staff': False
                })
            
            # Create workflow request
            request_id = await workflow_engine.initiate_workflow(workflow_type, request_data)
            
            if request_id:
                creation_type = "staff-created" if is_staff_created else "client-created"
                logger.info(f"Created {creation_type} workflow request {request_id} for user {user_id}")
            
            return request_id
            
        except Exception as e:
            logger.error(f"Error creating workflow request: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def transition_workflow(request_id: str, action: str, user_id: int, data: Dict[str, Any] = None) -> bool:
        """Transition a workflow to the next state"""
        try:
            workflow_engine = await WorkflowIntegration.get_workflow_manager()
            if not workflow_engine:
                logger.error("Workflow engine not available")
                return False
            
            # Get user info
            user = await get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Prepare transition data
            transition_data = data or {}
            transition_data.update({
                'actor_id': user['id'],
                'actor_telegram_id': user_id
            })
            
            # Execute transition
            success = await workflow_engine.transition_workflow(
                request_id, action, user['role'], transition_data
            )
            
            if success:
                logger.info(f"Transitioned workflow {request_id} with action {action}")
            else:
                logger.warning(f"Failed to transition workflow {request_id} with action {action}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error transitioning workflow: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def get_user_requests(user_id: int, role: str = None) -> list:
        """Get requests assigned to user's role"""
        try:
            state_manager = await WorkflowIntegration.get_state_manager()
            if not state_manager:
                logger.error("State manager not available")
                return []
            
            # Get user info if role not provided
            if not role:
                user = await get_user_by_telegram_id(user_id)
                if not user:
                    logger.error(f"User not found: {user_id}")
                    return []
                role = user['role']
            
            # Get requests for role
            requests = await state_manager.get_requests_by_role(role)
            
            logger.info(f"Retrieved {len(requests)} requests for role {role}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting user requests: {e}", exc_info=True)
            return []
    
    @staticmethod
    async def get_request_details(request_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a request"""
        try:
            state_manager = await WorkflowIntegration.get_state_manager()
            if not state_manager:
                logger.error("State manager not available")
                return None
            
            # Get request
            request = await state_manager.get_request(request_id)
            if not request:
                logger.error(f"Request not found: {request_id}")
                return None
            
            # Get request history
            history = await state_manager.get_request_history(request_id)
            
            return {
                'request': request,
                'history': history
            }
            
        except Exception as e:
            logger.error(f"Error getting request details: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def mark_notification_handled(user_id: int, request_id: str) -> bool:
        """Mark a notification as handled"""
        try:
            notification_system = await WorkflowIntegration.get_notification_system()
            if not notification_system:
                logger.error("Notification system not available")
                return False
            
            # Get user info
            user = await get_user_by_telegram_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Mark notification as handled
            success = await notification_system.mark_notification_handled(user['id'], request_id)
            
            if success:
                logger.info(f"Marked notification as handled for user {user_id}, request {request_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error marking notification as handled: {e}", exc_info=True)
            return False


def workflow_handler(workflow_type: str = None, action: str = None):
    """Decorator to integrate existing handlers with workflow system"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract message/callback and state from args
                event = args[0] if args else None
                state = None
                
                # Find FSMContext in args
                for arg in args:
                    if isinstance(arg, FSMContext):
                        state = arg
                        break
                
                # Get user ID
                user_id = None
                if isinstance(event, (Message, CallbackQuery)):
                    user_id = event.from_user.id
                
                # Execute original handler
                result = await func(*args, **kwargs)
                
                # If workflow integration is requested and we have the necessary info
                if workflow_type and action and user_id and state:
                    # Get request_id from state if available
                    state_data = await state.get_data()
                    request_id = state_data.get('request_id')
                    
                    if request_id:
                        # Transition workflow
                        await WorkflowIntegration.transition_workflow(
                            request_id, action, user_id, state_data
                        )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in workflow handler wrapper: {e}", exc_info=True)
                # Still execute original handler even if workflow integration fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def workflow_action(action: str):
    """Decorator to mark a handler as performing a specific workflow action"""
    def decorator(func: Callable):
        func._workflow_action = action
        return func
    return decorator


class LegacyWorkflowBridge:
    """Bridge between legacy zayavka system and new workflow system"""
    
    @staticmethod
    async def migrate_zayavka_to_workflow(zayavka_id: int) -> Optional[str]:
        """Migrate an existing zayavka to the workflow system"""
        try:
            from database.base_queries import get_zayavka_by_id
            
            # Get zayavka details
            zayavka = await get_zayavka_by_id(zayavka_id)
            if not zayavka:
                logger.error(f"Zayavka not found: {zayavka_id}")
                return None
            
            # Determine workflow type based on zayavka type or status
            workflow_type = WorkflowType.CONNECTION_REQUEST.value
            if hasattr(zayavka, 'zayavka_type'):
                if zayavka.zayavka_type == 'tx':
                    workflow_type = WorkflowType.TECHNICAL_SERVICE.value
            
            # Create workflow request data
            request_data = {
                'description': zayavka.get('description', ''),
                'location': zayavka.get('address', ''),
                'priority': zayavka.get('priority', 'medium'),
                'legacy_zayavka_id': zayavka_id,
                'contact_info': {
                    'phone': zayavka.get('phone', ''),
                    'address': zayavka.get('address', '')
                }
            }
            
            # Create workflow request
            request_id = await WorkflowIntegration.create_workflow_request(
                workflow_type, zayavka.get('user_id'), request_data
            )
            
            if request_id:
                logger.info(f"Migrated zayavka {zayavka_id} to workflow request {request_id}")
            
            return request_id
            
        except Exception as e:
            logger.error(f"Error migrating zayavka to workflow: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def sync_workflow_to_zayavka(request_id: str) -> bool:
        """Sync workflow state back to legacy zayavka system"""
        try:
            # Get workflow request details
            details = await WorkflowIntegration.get_request_details(request_id)
            if not details:
                return False
            
            request = details['request']
            legacy_zayavka_id = request.state_data.get('legacy_zayavka_id')
            
            if not legacy_zayavka_id:
                return True  # No legacy zayavka to sync
            
            # Map workflow status to zayavka status
            status_mapping = {
                'created': 'new',
                'in_progress': 'assigned_to_technician',
                'completed': 'closed',
                'cancelled': 'cancelled'
            }
            
            zayavka_status = status_mapping.get(request.current_status, 'new')
            
            # Update zayavka status
            from database.base_queries import update_zayavka_status
            success = await update_zayavka_status(legacy_zayavka_id, zayavka_status)
            
            if success:
                logger.info(f"Synced workflow {request_id} to zayavka {legacy_zayavka_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing workflow to zayavka: {e}", exc_info=True)
            return False


# Global workflow integration instance
workflow_integration = WorkflowIntegration()

# Export commonly used functions
async def create_workflow_request(workflow_type: str, user_id: int, request_data: Dict[str, Any]) -> Optional[str]:
    """Convenience function to create workflow request"""
    return await WorkflowIntegration.create_workflow_request(workflow_type, user_id, request_data)

async def transition_workflow(request_id: str, action: str, user_id: int, data: Dict[str, Any] = None) -> bool:
    """Convenience function to transition workflow"""
    return await WorkflowIntegration.transition_workflow(request_id, action, user_id, data)

async def get_user_requests(user_id: int, role: str = None) -> list:
    """Convenience function to get user requests"""
    return await WorkflowIntegration.get_user_requests(user_id, role)

async def get_request_details(request_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get request details"""
    return await WorkflowIntegration.get_request_details(request_id)