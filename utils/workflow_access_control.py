"""
Workflow Access Control System - Role-based access control for workflow operations
Implements comprehensive permission validation and unauthorized access prevention
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple
from abc import ABC, abstractmethod
from functools import wraps

from database.models import (
    UserRole, WorkflowType, WorkflowAction, ServiceRequest, 
    StateTransition, RequestStatus
)
from utils.logger import setup_module_logger

logger = setup_module_logger("workflow_access_control")


class AccessControlInterface(ABC):
    """Abstract interface for workflow access control"""
    
    @abstractmethod
    async def validate_workflow_action(self, user_id: int, user_role: str, action: str, 
                                     request_id: str = None, target_data: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Validates if user can perform workflow action"""
        pass
    
    @abstractmethod
    async def validate_request_access(self, user_id: int, user_role: str, request_id: str, 
                                    access_type: str = 'read') -> Tuple[bool, str]:
        """Validates if user can access specific request"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: int, user_role: str) -> Dict[str, Any]:
        """Returns user permissions and capabilities"""
        pass
    
    @abstractmethod
    async def log_access_attempt(self, user_id: int, action: str, resource: str, 
                               granted: bool, reason: str = None) -> bool:
        """Logs access attempts for audit trail"""
        pass


class WorkflowAccessControl(AccessControlInterface):
    """Comprehensive workflow access control implementation"""
    
    def __init__(self, pool=None):
        self.pool = pool
        self._load_role_permissions()
        self._load_workflow_permissions()
    
    def _get_pool(self):
        """Get database pool"""
        if self.pool:
            return self.pool
        try:
            from loader import bot
            return bot.db
        except ImportError:
            logger.error("No database pool available")
            return None
    
    def _load_role_permissions(self):
        """Load role-based permissions matrix"""
        self.role_permissions = {
            UserRole.CLIENT.value: {
                'workflow_actions': [
                    WorkflowAction.SUBMIT_REQUEST.value,
                    WorkflowAction.SUBMIT_TECHNICAL_REQUEST.value,
                    WorkflowAction.RATE_SERVICE.value,
                    WorkflowAction.CANCEL_REQUEST.value
                ],
                'request_access': ['own_requests'],
                'data_access': ['own_data'],
                'can_create_requests': True,
                'can_view_all_requests': False,
                'can_assign_requests': False,
                'can_modify_others_requests': False
            },
            
            UserRole.MANAGER.value: {
                'workflow_actions': [
                    WorkflowAction.ASSIGN_TO_JUNIOR_MANAGER.value,
                    WorkflowAction.ESCALATE.value,
                    WorkflowAction.ADD_COMMENTS.value,
                    WorkflowAction.CANCEL_REQUEST.value
                ],
                'request_access': ['connection_requests', 'assigned_requests'],
                'data_access': ['client_data', 'request_data'],
                'can_create_requests': True,
                'can_view_all_requests': False,
                'can_assign_requests': True,
                'can_modify_others_requests': True
            },
            
            UserRole.JUNIOR_MANAGER.value: {
                'workflow_actions': [
                    WorkflowAction.CALL_CLIENT.value,
                    WorkflowAction.FORWARD_TO_CONTROLLER.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['assigned_requests'],
                'data_access': ['client_data', 'request_data'],
                'can_create_requests': False,
                'can_view_all_requests': False,
                'can_assign_requests': False,
                'can_modify_others_requests': True
            },
            
            UserRole.CONTROLLER.value: {
                'workflow_actions': [
                    WorkflowAction.ASSIGN_TO_TECHNICIAN.value,
                    WorkflowAction.ASSIGN_TECHNICAL_TO_TECHNICIAN.value,
                    WorkflowAction.ESCALATE.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['technical_requests', 'assigned_requests'],
                'data_access': ['client_data', 'request_data', 'technician_data'],
                'can_create_requests': True,
                'can_view_all_requests': False,
                'can_assign_requests': True,
                'can_modify_others_requests': True
            },
            
            UserRole.TECHNICIAN.value: {
                'workflow_actions': [
                    WorkflowAction.START_INSTALLATION.value,
                    WorkflowAction.START_DIAGNOSTICS.value,
                    WorkflowAction.DECIDE_WAREHOUSE_INVOLVEMENT.value,
                    WorkflowAction.RESOLVE_WITHOUT_WAREHOUSE.value,
                    WorkflowAction.REQUEST_WAREHOUSE_SUPPORT.value,
                    WorkflowAction.DOCUMENT_EQUIPMENT.value,
                    WorkflowAction.COMPLETE_TECHNICAL_SERVICE.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['assigned_requests'],
                'data_access': ['client_data', 'request_data', 'equipment_data'],
                'can_create_requests': False,
                'can_view_all_requests': False,
                'can_assign_requests': False,
                'can_modify_others_requests': True
            },
            
            UserRole.WAREHOUSE.value: {
                'workflow_actions': [
                    WorkflowAction.PREPARE_EQUIPMENT.value,
                    WorkflowAction.CONFIRM_EQUIPMENT_READY.value,
                    WorkflowAction.UPDATE_INVENTORY.value,
                    WorkflowAction.CLOSE_REQUEST.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['warehouse_requests', 'assigned_requests'],
                'data_access': ['equipment_data', 'inventory_data', 'request_data'],
                'can_create_requests': False,
                'can_view_all_requests': False,
                'can_assign_requests': False,
                'can_modify_others_requests': True
            },
            
            UserRole.CALL_CENTER.value: {
                'workflow_actions': [
                    WorkflowAction.CREATE_CALL_CENTER_REQUEST.value,
                    WorkflowAction.RESOLVE_REMOTELY.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['call_center_requests', 'assigned_requests'],
                'data_access': ['client_data', 'request_data'],
                'can_create_requests': True,
                'can_view_all_requests': False,
                'can_assign_requests': False,
                'can_modify_others_requests': True
            },
            
            UserRole.CALL_CENTER_SUPERVISOR.value: {
                'workflow_actions': [
                    WorkflowAction.ASSIGN_TO_CALL_CENTER_OPERATOR.value,
                    WorkflowAction.ESCALATE.value,
                    WorkflowAction.ADD_COMMENTS.value
                ],
                'request_access': ['call_center_requests', 'assigned_requests'],
                'data_access': ['client_data', 'request_data', 'call_center_data'],
                'can_create_requests': True,
                'can_view_all_requests': False,
                'can_assign_requests': True,
                'can_modify_others_requests': True
            },
            
            UserRole.ADMIN.value: {
                'workflow_actions': [action.value for action in WorkflowAction],
                'request_access': ['all_requests'],
                'data_access': ['all_data'],
                'can_create_requests': True,
                'can_view_all_requests': True,
                'can_assign_requests': True,
                'can_modify_others_requests': True
            }
        }
    
    def _load_workflow_permissions(self):
        """Load workflow-specific permission requirements"""
        self.workflow_permissions = {
            WorkflowType.CONNECTION_REQUEST.value: {
                'allowed_initiators': [UserRole.CLIENT.value, UserRole.CALL_CENTER.value],
                'role_transitions': {
                    UserRole.CLIENT.value: [UserRole.MANAGER.value],
                    UserRole.CALL_CENTER.value: [UserRole.MANAGER.value],
                    UserRole.MANAGER.value: [UserRole.JUNIOR_MANAGER.value],
                    UserRole.JUNIOR_MANAGER.value: [UserRole.CONTROLLER.value],
                    UserRole.CONTROLLER.value: [UserRole.TECHNICIAN.value],
                    UserRole.TECHNICIAN.value: [UserRole.WAREHOUSE.value],
                    UserRole.WAREHOUSE.value: [UserRole.CLIENT.value]
                }
            },
            
            WorkflowType.TECHNICAL_SERVICE.value: {
                'allowed_initiators': [UserRole.CLIENT.value, UserRole.CALL_CENTER.value],
                'role_transitions': {
                    UserRole.CLIENT.value: [UserRole.CONTROLLER.value],
                    UserRole.CALL_CENTER.value: [UserRole.CONTROLLER.value],
                    UserRole.CONTROLLER.value: [UserRole.TECHNICIAN.value],
                    UserRole.TECHNICIAN.value: [UserRole.WAREHOUSE.value, UserRole.CLIENT.value],
                    UserRole.WAREHOUSE.value: [UserRole.TECHNICIAN.value]
                }
            },
            
            WorkflowType.CALL_CENTER_DIRECT.value: {
                'allowed_initiators': [UserRole.CALL_CENTER.value],
                'role_transitions': {
                    UserRole.CALL_CENTER.value: [UserRole.CALL_CENTER_SUPERVISOR.value],
                    UserRole.CALL_CENTER_SUPERVISOR.value: [UserRole.CALL_CENTER.value],
                    UserRole.CALL_CENTER.value: [UserRole.CLIENT.value]
                }
            }
        }
    
    async def validate_workflow_action(self, user_id: int, user_role: str, action: str, 
                                     request_id: str = None, target_data: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Validates if user can perform workflow action"""
        try:
            # Check if role has permission for this action
            role_perms = self.role_permissions.get(user_role, {})
            allowed_actions = role_perms.get('workflow_actions', [])
            
            if action not in allowed_actions:
                reason = f"Role {user_role} not authorized for action {action}"
                await self.log_access_attempt(user_id, action, f"workflow_action:{action}", False, reason)
                return False, reason
            
            # If request_id provided, validate request-specific permissions
            if request_id:
                request_access_valid, request_reason = await self.validate_request_access(
                    user_id, user_role, request_id, 'modify'
                )
                if not request_access_valid:
                    await self.log_access_attempt(user_id, action, f"request:{request_id}", False, request_reason)
                    return False, request_reason
            
            # Log successful validation
            await self.log_access_attempt(user_id, action, f"workflow_action:{action}", True)
            return True, "Access granted"
            
        except Exception as e:
            logger.error(f"Error validating workflow action: {e}", exc_info=True)
            reason = f"Validation error: {str(e)}"
            await self.log_access_attempt(user_id, action, f"workflow_action:{action}", False, reason)
            return False, reason
    
    async def validate_request_access(self, user_id: int, user_role: str, request_id: str, 
                                    access_type: str = 'read') -> Tuple[bool, str]:
        """Validates if user can access specific request"""
        try:
            pool = self._get_pool()
            if not pool:
                return False, "Database unavailable"
            
            async with pool.acquire() as conn:
                # Get request details
                request_query = """
                SELECT id, workflow_type, client_id, role_current , current_status,
                       created_at, state_data
                FROM service_requests
                WHERE id = $1
                """
                
                request_row = await conn.fetchrow(request_query, request_id)
                if not request_row:
                    reason = f"Request {request_id} not found"
                    await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", False, reason)
                    return False, reason
                
                # Admin has access to all requests
                if user_role == UserRole.ADMIN.value:
                    await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", True, "Admin access")
                    return True, "Admin access granted"
                
                # Client can only access their own requests
                if user_role == UserRole.CLIENT.value:
                    if request_row['client_id'] == user_id:
                        await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", True, "Own request")
                        return True, "Own request access granted"
                    else:
                        reason = f"Client can only access own requests"
                        await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", False, reason)
                        return False, reason
                
                # Check role-based request access permissions
                role_perms = self.role_permissions.get(user_role, {})
                request_access_types = role_perms.get('request_access', [])
                
                # Check if user's role can access this type of request
                workflow_type = request_row['workflow_type']
                role_current = request_row['role_current ']
                
                access_granted = False
                access_reason = ""
                
                # Check various access patterns
                if 'all_requests' in request_access_types:
                    access_granted = True
                    access_reason = "All requests access"
                elif 'assigned_requests' in request_access_types and role_current == user_role:
                    access_granted = True
                    access_reason = "Assigned request access"
                elif 'connection_requests' in request_access_types and workflow_type == WorkflowType.CONNECTION_REQUEST.value:
                    access_granted = True
                    access_reason = "Connection request access"
                elif 'technical_requests' in request_access_types and workflow_type == WorkflowType.TECHNICAL_SERVICE.value:
                    access_granted = True
                    access_reason = "Technical request access"
                elif 'call_center_requests' in request_access_types and workflow_type == WorkflowType.CALL_CENTER_DIRECT.value:
                    access_granted = True
                    access_reason = "Call center request access"
                
                if access_granted:
                    await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", True, access_reason)
                    return True, access_reason
                else:
                    reason = f"Role {user_role} not authorized to access request {request_id}"
                    await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", False, reason)
                    return False, reason
                
        except Exception as e:
            logger.error(f"Error validating request access: {e}", exc_info=True)
            reason = f"Access validation error: {str(e)}"
            await self.log_access_attempt(user_id, f"access_{access_type}", f"request:{request_id}", False, reason)
            return False, reason
    
    async def get_user_permissions(self, user_id: int, user_role: str) -> Dict[str, Any]:
        """Returns user permissions and capabilities"""
        try:
            base_permissions = self.role_permissions.get(user_role, {})
            
            return {
                'user_id': user_id,
                'role': user_role,
                'static_permissions': base_permissions,
                'effective_permissions': base_permissions
            }
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}", exc_info=True)
            return {'error': str(e)}
    
    async def log_access_attempt(self, user_id: int, action: str, resource: str, 
                               granted: bool, reason: str = None) -> bool:
        """Logs access attempts for audit trail"""
        try:
            pool = self._get_pool()
            if not pool:
                logger.error("No database pool available for access logging")
                return False
            
            async with pool.acquire() as conn:
                # Insert access log entry
                log_query = """
                INSERT INTO access_control_logs 
                (user_id, action, resource, granted, reason, timestamp, ip_address, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await conn.execute(
                    log_query,
                    user_id, action, resource, granted, reason,
                    datetime.now(), None, None  # IP and user agent can be added later
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error logging access attempt: {e}", exc_info=True)
            return False
    
    async def get_filtered_requests_for_role(self, user_id: int, user_role: str, 
                                           status_filter: str = None, 
                                           workflow_filter: str = None) -> List[Dict[str, Any]]:
        """Get requests filtered by role permissions"""
        try:
            pool = self._get_pool()
            if not pool:
                return []
            
            async with pool.acquire() as conn:
                # Build base query
                base_query = """
                SELECT sr.id, sr.workflow_type, sr.client_id, sr.role_current , 
                       sr.current_status, sr.created_at, sr.updated_at, sr.priority,
                       sr.description, sr.location, sr.contact_info, sr.state_data,
                       sr.equipment_used, sr.inventory_updated, sr.completion_rating,
                       sr.feedback_comments
                FROM service_requests sr
                WHERE 1=1
                """
                
                params = []
                param_count = 0
                
                # Apply role-based filtering
                if user_role == UserRole.CLIENT.value:
                    base_query += f" AND sr.client_id = ${param_count + 1}"
                    params.append(user_id)
                    param_count += 1
                elif user_role == UserRole.ADMIN.value:
                    # Admin sees all requests
                    pass
                else:
                    # Staff roles see requests assigned to them or relevant to their role
                    role_conditions = []
                    
                    # Current assignments
                    role_conditions.append(f"sr.role_current = ${param_count + 1}")
                    params.append(user_role)
                    param_count += 1
                    
                    # Role-specific workflow access
                    role_perms = self.role_permissions.get(user_role, {})
                    request_access_types = role_perms.get('request_access', [])
                    
                    if 'connection_requests' in request_access_types:
                        role_conditions.append(f"sr.workflow_type = ${param_count + 1}")
                        params.append(WorkflowType.CONNECTION_REQUEST.value)
                        param_count += 1
                    
                    if 'technical_requests' in request_access_types:
                        role_conditions.append(f"sr.workflow_type = ${param_count + 1}")
                        params.append(WorkflowType.TECHNICAL_SERVICE.value)
                        param_count += 1
                    
                    if 'call_center_requests' in request_access_types:
                        role_conditions.append(f"sr.workflow_type = ${param_count + 1}")
                        params.append(WorkflowType.CALL_CENTER_DIRECT.value)
                        param_count += 1
                    
                    if role_conditions:
                        base_query += " AND (" + " OR ".join(role_conditions) + ")"
                
                # Apply additional filters
                if status_filter:
                    base_query += f" AND sr.current_status = ${param_count + 1}"
                    params.append(status_filter)
                    param_count += 1
                
                if workflow_filter:
                    base_query += f" AND sr.workflow_type = ${param_count + 1}"
                    params.append(workflow_filter)
                    param_count += 1
                
                # Order by priority and creation date
                base_query += " ORDER BY sr.priority DESC, sr.created_at DESC"
                
                # Execute query
                rows = await conn.fetch(base_query, *params)
                
                # Convert to dictionaries
                requests = []
                for row in rows:
                    request_dict = dict(row)
                    # Parse JSON fields
                    if request_dict.get('contact_info'):
                        try:
                            request_dict['contact_info'] = json.loads(request_dict['contact_info'])
                        except:
                            pass
                    if request_dict.get('state_data'):
                        try:
                            request_dict['state_data'] = json.loads(request_dict['state_data'])
                        except:
                            pass
                    if request_dict.get('equipment_used'):
                        try:
                            request_dict['equipment_used'] = json.loads(request_dict['equipment_used'])
                        except:
                            pass
                    
                    requests.append(request_dict)
                
                logger.info(f"Retrieved {len(requests)} filtered requests for user {user_id} with role {user_role}")
                return requests
                
        except Exception as e:
            logger.error(f"Error getting filtered requests: {e}", exc_info=True)
            return []


def require_workflow_permission(required_action: str, request_id_param: str = 'request_id'):
    """
    Decorator to enforce workflow permissions on handler functions
    
    Args:
        required_action: The workflow action that requires permission
        request_id_param: Parameter name containing the request ID (optional)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Extract user information from kwargs
                user_id = kwargs.get('user_id')
                user_role = kwargs.get('user_role')
                request_id = kwargs.get(request_id_param)
                
                if not user_id or not user_role:
                    return {
                        'success': False,
                        'error': 'Authentication required: user_id and user_role must be provided'
                    }
                
                # Initialize access control
                access_control = WorkflowAccessControl()
                
                # Validate permission
                has_permission, reason = await access_control.validate_workflow_action(
                    user_id=user_id,
                    user_role=user_role,
                    action=required_action,
                    request_id=request_id,
                    target_data=kwargs
                )
                
                if not has_permission:
                    return {
                        'success': False,
                        'error': f'Access denied: {reason}'
                    }
                
                # Execute the original function
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in permission decorator: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Permission validation error: {str(e)}'
                }
        
        return wrapper
    return decorator


class PermissionTransferManager:
    """Manages permission transfers during role transitions"""
    
    def __init__(self, pool=None):
        self.pool = pool
        self.access_control = WorkflowAccessControl(pool)
    
    def _get_pool(self):
        """Get database pool"""
        if self.pool:
            return self.pool
        try:
            from loader import bot
            return bot.db
        except ImportError:
            logger.error("No database pool available")
            return None
    
    async def transfer_request_permissions(self, request_id: str, from_role: str, 
                                        to_role: str, actor_id: int) -> bool:
        """Transfer request permissions during role transitions"""
        try:
            pool = self._get_pool()
            if not pool:
                return False
            
            async with pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Update request current role
                    update_query = """
                    UPDATE service_requests 
                    SET role_current = $1, updated_at = $2
                    WHERE id = $3
                    """
                    
                    await conn.execute(update_query, to_role, datetime.now(), request_id)
                    
                    # Log the role transition
                    transition_query = """
                    INSERT INTO state_transitions 
                    (request_id, from_role, to_role, actor_id, action, timestamp, comments)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """
                    
                    await conn.execute(
                        transition_query,
                        request_id, from_role, to_role, actor_id,
                        'role_transfer', datetime.now(),
                        f'Permission transferred from {from_role} to {to_role}'
                    )
                    
                    # Log access control event
                    await self.access_control.log_access_attempt(
                        actor_id, 'transfer_permissions', f'request:{request_id}',
                        True, f'Transferred from {from_role} to {to_role}'
                    )
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error transferring permissions: {e}", exc_info=True)
            return False
    
    async def validate_permission_transfer(self, request_id: str, from_role: str, 
                                         to_role: str, actor_id: int, actor_role: str) -> Tuple[bool, str]:
        """Validate if permission transfer is allowed"""
        try:
            # Check if role transition is valid for workflow
            pool = self._get_pool()
            if not pool:
                return False, "Database unavailable"
            
            async with pool.acquire() as conn:
                # Get request workflow type
                request_query = """
                SELECT workflow_type FROM service_requests WHERE id = $1
                """
                
                request_row = await conn.fetchrow(request_query, request_id)
                if not request_row:
                    return False, "Request not found"
                
                workflow_type = request_row['workflow_type']
                
                # Validate role transition
                workflow_perms = self.access_control.workflow_permissions.get(workflow_type, {})
                role_transitions = workflow_perms.get('role_transitions', {})
                allowed_next_roles = role_transitions.get(from_role, [])
                
                if to_role not in allowed_next_roles:
                    return False, f"Invalid role transition from {from_role} to {to_role} for workflow {workflow_type}"
                
                return True, "Permission transfer valid"
                
        except Exception as e:
            logger.error(f"Error validating permission transfer: {e}", exc_info=True)
            return False, f"Validation error: {str(e)}"


class AccessControlFactory:
    """Factory for creating access control instances"""
    
    @staticmethod
    def create_access_control() -> WorkflowAccessControl:
        """Creates a new access control instance"""
        return WorkflowAccessControl()