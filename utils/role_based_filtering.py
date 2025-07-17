"""
Role-Based Request Filtering - Enhanced filtering system for workflow requests
Provides comprehensive role-based access control for request lists and data access
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from abc import ABC, abstractmethod

from database.models import UserRole, WorkflowType, RequestStatus, ServiceRequest
from utils.workflow_access_control import WorkflowAccessControl
from utils.logger import setup_module_logger

logger = setup_module_logger("role_based_filtering")


class RequestFilterInterface(ABC):
    """Abstract interface for request filtering"""
    
    @abstractmethod
    async def filter_requests_for_user(self, user_id: int, user_role: str, 
                                     requests: List[Dict[str, Any]], 
                                     filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Filter requests based on user role and permissions"""
        pass
    
    @abstractmethod
    async def get_accessible_request_ids(self, user_id: int, user_role: str) -> Set[str]:
        """Get set of request IDs accessible to user"""
        pass
    
    @abstractmethod
    async def filter_request_data(self, user_id: int, user_role: str, 
                                request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from request based on user permissions"""
        pass


class RoleBasedRequestFilter(RequestFilterInterface):
    """Comprehensive role-based request filtering implementation"""
    
    def __init__(self, pool=None):
        self.pool = pool
        self.access_control = WorkflowAccessControl(pool)
        self._load_data_access_rules()
    
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
    
    def _load_data_access_rules(self):
        """Load data access rules for different roles"""
        self.data_access_rules = {
            UserRole.CLIENT.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'description', 'location', 'priority',
                    'current_status', 'created_at', 'updated_at', 'completion_rating',
                    'feedback_comments'
                ],
                'restricted_fields': [
                    'state_data', 'equipment_used', 'inventory_updated'
                ],
                'can_see_internal_comments': False,
                'can_see_assignment_history': False,
                'can_see_other_clients_data': False
            },
            
            UserRole.MANAGER.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'state_data', 'contact_info'
                ],
                'restricted_fields': [
                    'equipment_used', 'inventory_updated'
                ],
                'can_see_internal_comments': True,
                'can_see_assignment_history': True,
                'can_see_other_clients_data': True
            },
            
            UserRole.JUNIOR_MANAGER.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'contact_info'
                ],
                'restricted_fields': [
                    'equipment_used', 'inventory_updated', 'state_data'
                ],
                'can_see_internal_comments': False,
                'can_see_assignment_history': False,
                'can_see_other_clients_data': True
            },
            
            UserRole.CONTROLLER.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'state_data', 'contact_info'
                ],
                'restricted_fields': [
                    'inventory_updated'
                ],
                'can_see_internal_comments': True,
                'can_see_assignment_history': True,
                'can_see_other_clients_data': True
            },
            
            UserRole.TECHNICIAN.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'state_data', 'contact_info', 'equipment_used'
                ],
                'restricted_fields': [
                    'inventory_updated'
                ],
                'can_see_internal_comments': True,
                'can_see_assignment_history': False,
                'can_see_other_clients_data': True
            },
            
            UserRole.WAREHOUSE.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'state_data', 'equipment_used', 'inventory_updated'
                ],
                'restricted_fields': [],
                'can_see_internal_comments': True,
                'can_see_assignment_history': False,
                'can_see_other_clients_data': False
            },
            
            UserRole.CALL_CENTER.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'contact_info'
                ],
                'restricted_fields': [
                    'state_data', 'equipment_used', 'inventory_updated'
                ],
                'can_see_internal_comments': False,
                'can_see_assignment_history': False,
                'can_see_other_clients_data': True
            },
            
            UserRole.CALL_CENTER_SUPERVISOR.value: {
                'allowed_fields': [
                    'id', 'workflow_type', 'client_id', 'description', 'location',
                    'priority', 'role_current ', 'current_status', 'created_at',
                    'updated_at', 'contact_info', 'state_data'
                ],
                'restricted_fields': [
                    'equipment_used', 'inventory_updated'
                ],
                'can_see_internal_comments': True,
                'can_see_assignment_history': True,
                'can_see_other_clients_data': True
            },
            
            UserRole.ADMIN.value: {
                'allowed_fields': 'all',
                'restricted_fields': [],
                'can_see_internal_comments': True,
                'can_see_assignment_history': True,
                'can_see_other_clients_data': True
            }
        }
    
    async def filter_requests_for_user(self, user_id: int, user_role: str, 
                                     requests: List[Dict[str, Any]], 
                                     filter_criteria: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Filter requests based on user role and permissions"""
        try:
            filtered_requests = []
            
            for request in requests:
                # Check if user has access to this request
                has_access, _ = await self.access_control.validate_request_access(
                    user_id, user_role, request.get('id'), 'read'
                )
                
                if not has_access:
                    continue
                
                # Filter request data based on role permissions
                filtered_request = await self.filter_request_data(user_id, user_role, request)
                
                # Apply additional filter criteria if provided
                if filter_criteria and not self._matches_filter_criteria(filtered_request, filter_criteria):
                    continue
                
                filtered_requests.append(filtered_request)
            
            # Apply role-based sorting
            sorted_requests = await self._apply_role_based_sorting(user_role, filtered_requests)
            
            logger.info(f"Filtered {len(requests)} requests to {len(sorted_requests)} for user {user_id} with role {user_role}")
            return sorted_requests
            
        except Exception as e:
            logger.error(f"Error filtering requests for user: {e}", exc_info=True)
            return []
    
    async def get_accessible_request_ids(self, user_id: int, user_role: str) -> Set[str]:
        """Get set of request IDs accessible to user"""
        try:
            pool = self._get_pool()
            if not pool:
                return set()
            
            async with pool.acquire() as conn:
                # Use the access control system to get filtered requests
                filtered_requests = await self.access_control.get_filtered_requests_for_role(
                    user_id, user_role
                )
                
                return {request['id'] for request in filtered_requests}
                
        except Exception as e:
            logger.error(f"Error getting accessible request IDs: {e}", exc_info=True)
            return set()
    
    async def filter_request_data(self, user_id: int, user_role: str, 
                                request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from request based on user permissions"""
        try:
            access_rules = self.data_access_rules.get(user_role, {})
            allowed_fields = access_rules.get('allowed_fields', [])
            restricted_fields = access_rules.get('restricted_fields', [])
            
            # Admin sees all data
            if user_role == UserRole.ADMIN.value or allowed_fields == 'all':
                return request_data
            
            # Filter fields based on role permissions
            filtered_data = {}
            
            for field, value in request_data.items():
                if field in restricted_fields:
                    continue
                
                if allowed_fields and field not in allowed_fields:
                    continue
                
                # Apply field-specific filtering
                filtered_value = await self._filter_field_value(
                    user_id, user_role, field, value, access_rules
                )
                
                filtered_data[field] = filtered_value
            
            # Add computed fields based on permissions
            filtered_data = await self._add_computed_fields(
                user_id, user_role, filtered_data, request_data, access_rules
            )
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error filtering request data: {e}", exc_info=True)
            return request_data
    
    async def _filter_field_value(self, user_id: int, user_role: str, field: str, 
                                value: Any, access_rules: Dict[str, Any]) -> Any:
        """Filter specific field values based on permissions"""
        try:
            # Filter state_data to remove sensitive information
            if field == 'state_data' and isinstance(value, (dict, str)):
                if isinstance(value, str):
                    try:
                        state_dict = json.loads(value)
                    except:
                        return value
                else:
                    state_dict = value
                
                return await self._filter_state_data(user_role, state_dict, access_rules)
            
            # Filter contact_info for non-authorized roles
            elif field == 'contact_info' and isinstance(value, (dict, str)):
                if isinstance(value, str):
                    try:
                        contact_dict = json.loads(value)
                    except:
                        return value
                else:
                    contact_dict = value
                
                return await self._filter_contact_info(user_role, contact_dict, access_rules)
            
            # Filter equipment_used for non-warehouse roles
            elif field == 'equipment_used' and user_role not in [UserRole.WAREHOUSE.value, UserRole.TECHNICIAN.value, UserRole.ADMIN.value]:
                return []
            
            return value
            
        except Exception as e:
            logger.error(f"Error filtering field value: {e}")
            return value
    
    async def _filter_state_data(self, user_role: str, state_data: Dict[str, Any], 
                               access_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Filter state data based on role permissions"""
        try:
            if user_role == UserRole.ADMIN.value:
                return state_data
            
            filtered_state = {}
            
            # Define which state fields each role can see
            role_state_access = {
                UserRole.CLIENT.value: ['client_comments', 'rating', 'feedback'],
                UserRole.MANAGER.value: ['client_comments', 'manager_comments', 'assignment_data'],
                UserRole.JUNIOR_MANAGER.value: ['client_comments', 'call_notes'],
                UserRole.CONTROLLER.value: ['client_comments', 'controller_comments', 'assignment_data', 'technician_assignment'],
                UserRole.TECHNICIAN.value: ['client_comments', 'technician_notes', 'diagnostics', 'equipment_needed', 'warehouse_decision'],
                UserRole.WAREHOUSE.value: ['equipment_used', 'inventory_updates', 'warehouse_comments'],
                UserRole.CALL_CENTER.value: ['client_comments', 'call_center_notes'],
                UserRole.CALL_CENTER_SUPERVISOR.value: ['client_comments', 'call_center_notes', 'supervisor_comments']
            }
            
            allowed_state_fields = role_state_access.get(user_role, [])
            
            for field, value in state_data.items():
                # Allow common fields for all roles
                if field in ['created_at', 'updated_at', 'priority', 'status']:
                    filtered_state[field] = value
                # Allow role-specific fields
                elif any(allowed_field in field for allowed_field in allowed_state_fields):
                    filtered_state[field] = value
                # Filter out sensitive fields
                elif not access_rules.get('can_see_internal_comments', False) and 'comment' in field.lower():
                    continue
            
            return filtered_state
            
        except Exception as e:
            logger.error(f"Error filtering state data: {e}")
            return state_data
    
    async def _filter_contact_info(self, user_role: str, contact_info: Dict[str, Any], 
                                 access_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Filter contact information based on role permissions"""
        try:
            if user_role == UserRole.ADMIN.value:
                return contact_info
            
            # Roles that can see full contact info
            full_access_roles = [
                UserRole.MANAGER.value, UserRole.JUNIOR_MANAGER.value,
                UserRole.CONTROLLER.value, UserRole.TECHNICIAN.value,
                UserRole.CALL_CENTER.value, UserRole.CALL_CENTER_SUPERVISOR.value
            ]
            
            if user_role in full_access_roles:
                return contact_info
            
            # Limited access for other roles
            filtered_contact = {}
            safe_fields = ['name', 'location', 'preferred_contact_time']
            
            for field, value in contact_info.items():
                if field in safe_fields:
                    filtered_contact[field] = value
            
            return filtered_contact
            
        except Exception as e:
            logger.error(f"Error filtering contact info: {e}")
            return contact_info
    
    async def _add_computed_fields(self, user_id: int, user_role: str, 
                                 filtered_data: Dict[str, Any], 
                                 original_data: Dict[str, Any],
                                 access_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Add computed fields based on user permissions"""
        try:
            # Add user-specific computed fields
            if user_role == UserRole.CLIENT.value and original_data.get('client_id') == user_id:
                filtered_data['is_own_request'] = True
            
            # Add assignment status for staff roles
            if user_role != UserRole.CLIENT.value and user_role != UserRole.ADMIN.value:
                filtered_data['is_assigned_to_me'] = original_data.get('role_current ') == user_role
            
            # Add permission flags
            filtered_data['user_permissions'] = {
                'can_modify': await self._can_user_modify_request(user_id, user_role, original_data),
                'can_assign': access_rules.get('can_see_assignment_history', False),
                'can_see_history': access_rules.get('can_see_assignment_history', False),
                'can_see_comments': access_rules.get('can_see_internal_comments', False)
            }
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error adding computed fields: {e}")
            return filtered_data
    
    async def _can_user_modify_request(self, user_id: int, user_role: str, 
                                     request_data: Dict[str, Any]) -> bool:
        """Check if user can modify the request"""
        try:
            # Use access control system to validate modify permission
            has_access, _ = await self.access_control.validate_request_access(
                user_id, user_role, request_data.get('id'), 'modify'
            )
            return has_access
            
        except Exception as e:
            logger.error(f"Error checking modify permission: {e}")
            return False
    
    def _matches_filter_criteria(self, request: Dict[str, Any], 
                               criteria: Dict[str, Any]) -> bool:
        """Check if request matches filter criteria"""
        try:
            for field, expected_value in criteria.items():
                request_value = request.get(field)
                
                # Handle different comparison types
                if isinstance(expected_value, list):
                    if request_value not in expected_value:
                        return False
                elif isinstance(expected_value, dict):
                    # Handle range queries
                    if 'min' in expected_value and request_value < expected_value['min']:
                        return False
                    if 'max' in expected_value and request_value > expected_value['max']:
                        return False
                else:
                    if request_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching filter criteria: {e}")
            return True
    
    async def _apply_role_based_sorting(self, user_role: str, 
                                      requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply role-specific sorting to requests"""
        try:
            # Define sorting priorities for different roles
            role_sorting = {
                UserRole.CLIENT.value: ['created_at', 'priority'],
                UserRole.MANAGER.value: ['priority', 'created_at'],
                UserRole.JUNIOR_MANAGER.value: ['created_at', 'priority'],
                UserRole.CONTROLLER.value: ['priority', 'workflow_type', 'created_at'],
                UserRole.TECHNICIAN.value: ['priority', 'location', 'created_at'],
                UserRole.WAREHOUSE.value: ['priority', 'created_at'],
                UserRole.CALL_CENTER.value: ['created_at', 'priority'],
                UserRole.CALL_CENTER_SUPERVISOR.value: ['priority', 'created_at'],
                UserRole.ADMIN.value: ['priority', 'created_at']
            }
            
            sort_fields = role_sorting.get(user_role, ['created_at'])
            
            # Sort by multiple fields
            def sort_key(request):
                key_values = []
                for field in sort_fields:
                    value = request.get(field)
                    if field == 'priority':
                        # Convert priority to numeric for sorting
                        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
                        value = priority_order.get(value, 0)
                    elif field == 'created_at' and isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            value = datetime.min
                    key_values.append(value)
                return tuple(key_values)
            
            # Sort in descending order (highest priority first, newest first)
            return sorted(requests, key=sort_key, reverse=True)
            
        except Exception as e:
            logger.error(f"Error applying role-based sorting: {e}")
            return requests
    
    async def get_request_summary_for_role(self, user_id: int, user_role: str) -> Dict[str, Any]:
        """Get request summary statistics for user's role"""
        try:
            pool = self._get_pool()
            if not pool:
                return {}
            
            async with pool.acquire() as conn:
                # Get accessible requests
                accessible_requests = await self.access_control.get_filtered_requests_for_role(
                    user_id, user_role
                )
                
                # Calculate statistics
                total_requests = len(accessible_requests)
                status_counts = {}
                priority_counts = {}
                workflow_counts = {}
                
                for request in accessible_requests:
                    # Count by status
                    status = request.get('current_status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                    
                    # Count by priority
                    priority = request.get('priority', 'unknown')
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                    
                    # Count by workflow type
                    workflow = request.get('workflow_type', 'unknown')
                    workflow_counts[workflow] = workflow_counts.get(workflow, 0) + 1
                
                return {
                    'user_id': user_id,
                    'user_role': user_role,
                    'total_requests': total_requests,
                    'status_breakdown': status_counts,
                    'priority_breakdown': priority_counts,
                    'workflow_breakdown': workflow_counts,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting request summary: {e}", exc_info=True)
            return {'error': str(e)}


class RequestFilterFactory:
    """Factory for creating request filter instances"""
    
    @staticmethod
    def create_request_filter() -> RoleBasedRequestFilter:
        """Creates a new request filter instance"""
        return RoleBasedRequestFilter()