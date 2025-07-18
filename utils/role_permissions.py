"""
Role-based permission system for multi-role application creation.

This module implements the permission matrix and validation functions
for staff members to create applications on behalf of clients.
"""

from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from database.models import UserRole, WorkflowType


class ApplicationType(Enum):
    """Application types that can be created by staff"""
    CONNECTION_REQUEST = "connection_request"
    TECHNICAL_SERVICE = "technical_service"


class PermissionLevel(Enum):
    """Permission levels for different operations"""
    NONE = "none"
    READ = "read"
    CREATE = "create"
    MANAGE = "manage"
    ADMIN = "admin"


@dataclass
class RolePermissions:
    """Permissions for a specific role"""
    can_create_connection: bool = False
    can_create_technical: bool = False
    can_assign_directly: bool = False
    can_select_client: bool = False
    can_create_client: bool = False
    notification_level: str = "low"
    max_applications_per_day: Optional[int] = None
    requires_approval: bool = False
    
    def to_dict(self) -> Dict[str, any]:
        return {
            'can_create_connection': self.can_create_connection,
            'can_create_technical': self.can_create_technical,
            'can_assign_directly': self.can_assign_directly,
            'can_select_client': self.can_select_client,
            'can_create_client': self.can_create_client,
            'notification_level': self.notification_level,
            'max_applications_per_day': self.max_applications_per_day,
            'requires_approval': self.requires_approval
        }


# Role-based permission matrix as defined in the design document
ROLE_PERMISSIONS: Dict[str, RolePermissions] = {
    UserRole.MANAGER.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=True,
        can_assign_directly=True,
        can_select_client=True,
        can_create_client=True,
        notification_level="high",
        max_applications_per_day=None,  # No limit
        requires_approval=False
    ),
    UserRole.JUNIOR_MANAGER.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=False,  # Only connection requests
        can_assign_directly=False,
        can_select_client=True,
        can_create_client=True,
        notification_level="medium",
        max_applications_per_day=50,
        requires_approval=False
    ),
    UserRole.CONTROLLER.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=True,
        can_assign_directly=True,
        can_select_client=True,
        can_create_client=True,
        notification_level="high",
        max_applications_per_day=None,  # No limit
        requires_approval=False
    ),
    UserRole.CALL_CENTER.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=True,
        can_assign_directly=False,
        can_select_client=True,
        can_create_client=True,
        notification_level="medium",
        max_applications_per_day=100,
        requires_approval=False
    ),
    # Non-staff roles have no application creation permissions
    UserRole.CLIENT.value: RolePermissions(),
    UserRole.TECHNICIAN.value: RolePermissions(),
    UserRole.WAREHOUSE.value: RolePermissions(),
    UserRole.ADMIN.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=True,
        can_assign_directly=True,
        can_select_client=True,
        can_create_client=True,
        notification_level="high",
        max_applications_per_day=None,
        requires_approval=False
    ),
    UserRole.BLOCKED.value: RolePermissions(),
    UserRole.CALL_CENTER_SUPERVISOR.value: RolePermissions(
        can_create_connection=True,
        can_create_technical=True,
        can_assign_directly=True,
        can_select_client=True,
        can_create_client=True,
        notification_level="high",
        max_applications_per_day=None,
        requires_approval=False
    )
}


# Exception classes for permission errors
class RolePermissionError(Exception):
    """Base exception for role permission errors"""
    
    def __init__(self, role: str, action: str, message: Optional[str] = None):
        self.role = role
        self.action = action
        self.message = message or f"Role '{role}' does not have permission for action '{action}'"
        super().__init__(self.message)


class ApplicationCreationPermissionError(RolePermissionError):
    """Exception for application creation permission errors"""
    
    def __init__(self, role: str, application_type: str, message: Optional[str] = None):
        self.application_type = application_type
        action = f"create_{application_type}_application"
        message = message or f"Role '{role}' cannot create '{application_type}' applications"
        super().__init__(role, action, message)


class ClientSelectionPermissionError(RolePermissionError):
    """Exception for client selection permission errors"""
    
    def __init__(self, role: str, operation: str, message: Optional[str] = None):
        action = f"client_{operation}"
        message = message or f"Role '{role}' cannot perform client {operation}"
        super().__init__(role, action, message)


class DailyLimitExceededError(RolePermissionError):
    """Exception for daily application creation limit exceeded"""
    
    def __init__(self, role: str, current_count: int, limit: int):
        self.current_count = current_count
        self.limit = limit
        message = f"Role '{role}' has exceeded daily application creation limit ({current_count}/{limit})"
        super().__init__(role, "create_application", message)


# Permission validation functions
def get_role_permissions(role: str) -> RolePermissions:
    """
    Get permissions for a specific role.
    
    Args:
        role: The user role
        
    Returns:
        RolePermissions object for the role
        
    Raises:
        ValueError: If role is not recognized
    """
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Unknown role: {role}")
    
    return ROLE_PERMISSIONS[role]


def can_create_application(role: str, application_type: str) -> bool:
    """
    Check if a role can create a specific type of application.
    
    Args:
        role: The user role
        application_type: Type of application (connection_request or technical_service)
        
    Returns:
        True if role can create the application type, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        
        if application_type == ApplicationType.CONNECTION_REQUEST.value:
            return permissions.can_create_connection
        elif application_type == ApplicationType.TECHNICAL_SERVICE.value:
            return permissions.can_create_technical
        else:
            return False
            
    except ValueError:
        return False


def can_select_client(role: str) -> bool:
    """
    Check if a role can select existing clients.
    
    Args:
        role: The user role
        
    Returns:
        True if role can select clients, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        return permissions.can_select_client
    except ValueError:
        return False


def can_create_client(role: str) -> bool:
    """
    Check if a role can create new client records.
    
    Args:
        role: The user role
        
    Returns:
        True if role can create clients, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        return permissions.can_create_client
    except ValueError:
        return False


def can_assign_directly(role: str) -> bool:
    """
    Check if a role can directly assign applications to technicians.
    
    Args:
        role: The user role
        
    Returns:
        True if role can assign directly, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        return permissions.can_assign_directly
    except ValueError:
        return False


def validate_application_creation_permission(role: str, application_type: str) -> None:
    """
    Validate that a role has permission to create a specific application type.
    
    Args:
        role: The user role
        application_type: Type of application to create
        
    Raises:
        ApplicationCreationPermissionError: If role doesn't have permission
    """
    if not can_create_application(role, application_type):
        raise ApplicationCreationPermissionError(role, application_type)


def validate_client_selection_permission(role: str) -> None:
    """
    Validate that a role has permission to select clients.
    
    Args:
        role: The user role
        
    Raises:
        ClientSelectionPermissionError: If role doesn't have permission
    """
    if not can_select_client(role):
        raise ClientSelectionPermissionError(role, "selection")


def validate_client_creation_permission(role: str) -> None:
    """
    Validate that a role has permission to create new clients.
    
    Args:
        role: The user role
        
    Raises:
        ClientSelectionPermissionError: If role doesn't have permission
    """
    if not can_create_client(role):
        raise ClientSelectionPermissionError(role, "creation")


def validate_daily_limit(role: str, current_count: int) -> None:
    """
    Validate that a role hasn't exceeded their daily application creation limit.
    
    Args:
        role: The user role
        current_count: Current number of applications created today
        
    Raises:
        DailyLimitExceededError: If daily limit is exceeded
    """
    try:
        permissions = get_role_permissions(role)
        
        if permissions.max_applications_per_day is not None:
            if current_count >= permissions.max_applications_per_day:
                raise DailyLimitExceededError(role, current_count, permissions.max_applications_per_day)
                
    except ValueError:
        # Unknown role, treat as no permission
        raise DailyLimitExceededError(role, current_count, 0)


def get_available_application_types(role: str) -> List[str]:
    """
    Get list of application types that a role can create.
    
    Args:
        role: The user role
        
    Returns:
        List of application types the role can create
    """
    available_types = []
    
    try:
        permissions = get_role_permissions(role)
        
        if permissions.can_create_connection:
            available_types.append(ApplicationType.CONNECTION_REQUEST.value)
            
        if permissions.can_create_technical:
            available_types.append(ApplicationType.TECHNICAL_SERVICE.value)
            
    except ValueError:
        pass  # Unknown role, return empty list
    
    return available_types


def get_staff_roles_with_application_creation() -> List[str]:
    """
    Get list of roles that can create applications.
    
    Returns:
        List of roles that have application creation permissions
    """
    staff_roles = []
    
    for role, permissions in ROLE_PERMISSIONS.items():
        if permissions.can_create_connection or permissions.can_create_technical:
            staff_roles.append(role)
    
    return staff_roles


def get_notification_level(role: str) -> str:
    """
    Get notification level for a role.
    
    Args:
        role: The user role
        
    Returns:
        Notification level (low, medium, high)
    """
    try:
        permissions = get_role_permissions(role)
        return permissions.notification_level
    except ValueError:
        return "low"


def requires_approval(role: str) -> bool:
    """
    Check if applications created by a role require approval.
    
    Args:
        role: The user role
        
    Returns:
        True if applications require approval, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        return permissions.requires_approval
    except ValueError:
        return True  # Unknown roles require approval by default


def validate_comprehensive_permissions(
    role: str, 
    application_type: str, 
    needs_client_selection: bool = True,
    needs_client_creation: bool = False,
    current_daily_count: int = 0
) -> None:
    """
    Perform comprehensive permission validation for application creation.
    
    Args:
        role: The user role
        application_type: Type of application to create
        needs_client_selection: Whether client selection is needed
        needs_client_creation: Whether new client creation is needed
        current_daily_count: Current number of applications created today
        
    Raises:
        Various permission errors if validation fails
    """
    # Validate application creation permission
    validate_application_creation_permission(role, application_type)
    
    # Validate client-related permissions
    if needs_client_selection:
        validate_client_selection_permission(role)
    
    if needs_client_creation:
        validate_client_creation_permission(role)
    
    # Validate daily limits
    validate_daily_limit(role, current_daily_count)


def get_role_capabilities_summary(role: str) -> Dict[str, any]:
    """
    Get a comprehensive summary of role capabilities.
    
    Args:
        role: The user role
        
    Returns:
        Dictionary containing role capabilities and limits
    """
    try:
        permissions = get_role_permissions(role)
        
        return {
            'role': role,
            'can_create_applications': permissions.can_create_connection or permissions.can_create_technical,
            'available_application_types': get_available_application_types(role),
            'can_select_client': permissions.can_select_client,
            'can_create_client': permissions.can_create_client,
            'can_assign_directly': permissions.can_assign_directly,
            'notification_level': permissions.notification_level,
            'daily_limit': permissions.max_applications_per_day,
            'requires_approval': permissions.requires_approval,
            'permissions': permissions.to_dict()
        }
        
    except ValueError:
        return {
            'role': role,
            'can_create_applications': False,
            'available_application_types': [],
            'can_select_client': False,
            'can_create_client': False,
            'can_assign_directly': False,
            'notification_level': 'none',
            'daily_limit': 0,
            'requires_approval': True,
            'permissions': RolePermissions().to_dict()
        }


# Utility functions for role management
def is_staff_role(role: str) -> bool:
    """
    Check if a role is a staff role (can create applications).
    
    Args:
        role: The user role
        
    Returns:
        True if role is a staff role, False otherwise
    """
    return role in get_staff_roles_with_application_creation()


def get_role_hierarchy_level(role: str) -> int:
    """
    Get hierarchy level for role-based access control.
    
    Args:
        role: The user role
        
    Returns:
        Hierarchy level (higher number = higher authority)
    """
    hierarchy = {
        UserRole.ADMIN.value: 100,
        UserRole.MANAGER.value: 80,
        UserRole.CONTROLLER.value: 70,
        UserRole.CALL_CENTER_SUPERVISOR.value: 65,
        UserRole.JUNIOR_MANAGER.value: 60,
        UserRole.CALL_CENTER.value: 50,
        UserRole.WAREHOUSE.value: 40,
        UserRole.TECHNICIAN.value: 30,
        UserRole.CLIENT.value: 10,
        UserRole.BLOCKED.value: 0
    }
    
    return hierarchy.get(role, 0)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """
    Check if a manager role can manage a target role.
    
    Args:
        manager_role: The manager's role
        target_role: The target user's role
        
    Returns:
        True if manager can manage target, False otherwise
    """
    manager_level = get_role_hierarchy_level(manager_role)
    target_level = get_role_hierarchy_level(target_role)
    
    return manager_level > target_level


async def check_staff_application_permission(role: str, permission_type: str) -> bool:
    """
    Check if a staff role has a specific application-related permission.
    
    Args:
        role: The user role
        permission_type: Type of permission to check
        
    Returns:
        True if role has the permission, False otherwise
    """
    try:
        permissions = get_role_permissions(role)
        
        if permission_type == "create_application":
            return permissions.can_create_connection or permissions.can_create_technical
        elif permission_type == "select_client":
            return permissions.can_select_client
        elif permission_type == "create_client":
            return permissions.can_create_client
        elif permission_type == "assign_directly":
            return permissions.can_assign_directly
        else:
            return False
            
    except ValueError:
        return False


# Constants for external use
STAFF_ROLES = get_staff_roles_with_application_creation()
APPLICATION_TYPES = [app_type.value for app_type in ApplicationType]
NOTIFICATION_LEVELS = ["low", "medium", "high"]
