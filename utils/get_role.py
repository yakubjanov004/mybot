from typing import Optional, List
from aiogram.types import User
from database.base_queries import get_user_by_telegram_id
from config import config
from utils.logger import setup_module_logger
import logging

logger = logging.getLogger(__name__)

# Role hierarchy and permissions
ROLE_HIERARCHY = {
    'admin': 100,
    'manager': 80,
    'junior_manager': 70,
    'controller': 70,
    'call_center': 60,
    'warehouse': 50,
    'technician': 40,
    'client': 10,
    'blocked': 0
}

ROLE_PERMISSIONS = {
    'admin': [
        'manage_users', 'manage_roles', 'view_all_zayavkas', 'manage_zayavkas',
        'view_statistics', 'manage_system', 'access_logs', 'manage_materials',
        'assign_tasks', 'manage_technicians', 'view_reports'
    ],
    'manager': [
        'view_all_zayavkas', 'manage_zayavkas', 'assign_tasks', 'view_statistics',
        'manage_technicians', 'view_reports', 'approve_requests'
    ],
    'junior_manager': [
        'create_zayavka', 'view_all_zayavkas', 'filter_zayavkas'
    ],
    'controller': [
        'view_all_zayavkas', 'quality_control', 'view_statistics', 'view_reports',
        'validate_completion'
    ],
    'call_center': [
        'create_zayavkas', 'view_client_info', 'manage_calls', 'search_clients',
        'create_feedback', 'view_call_stats'
    ],
    'warehouse': [
        'manage_materials', 'issue_materials', 'view_inventory', 'update_stock',
        'view_warehouse_stats', 'manage_equipment'
    ],
    'technician': [
        'view_assigned_tasks', 'update_task_status', 'complete_tasks',
        'request_materials', 'request_help', 'view_own_stats'
    ],
    'client': [
        'create_zayavka', 'view_own_zayavkas', 'provide_feedback',
        'update_profile', 'cancel_own_zayavka'
    ],
    'blocked': []
}

async def get_user_role(user: User | int) -> str:
    """Get user role from database. Accepts either User object or user_id."""
    try:
        # Safely get user ID from either User object or int
        user_id = user if isinstance(user, int) else user.id
        
        # Check if user is admin by ID first
        if config.is_admin(user_id):
            return 'admin'
        
        # Get from database
        db_user = await get_user_by_telegram_id(user_id)
        if db_user and db_user.get('role'):
            role = db_user['role']
            logger.debug(f"User {user_id} role: {role}")
            return role
        
        # Default role for new users
        return 'client'
        
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}", exc_info=True)
        return 'client'

async def get_user_role_by_telegram_id(telegram_id: int) -> str:
    """Get user role by telegram ID"""
    try:
        # Check if user is admin by ID first
        if config.is_admin(telegram_id):
            return 'admin'
        
        # Get from database
        db_user = await get_user_by_telegram_id(telegram_id)
        if db_user and db_user.get('role'):
            return db_user['role']
        
        return 'client'
        
    except Exception as e:
        logger.error(f"Error getting user role by telegram_id: {str(e)}")
        return 'client'

def is_admin(user: User) -> bool:
    """Check if user is admin"""
    return config.is_admin(user.id)

async def is_role(user: User, role: str) -> bool:
    """Check if user has specific role"""
    user_role = await get_user_role(user)
    return user_role == role

async def has_role(user: User, roles: List[str]) -> bool:
    """Check if user has any of the specified roles"""
    user_role = await get_user_role(user)
    return user_role in roles

async def has_permission(user: User, permission: str) -> bool:
    """Check if user has specific permission"""
    user_role = await get_user_role(user)
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return permission in role_perms

async def has_permissions(user: User, permissions: List[str]) -> bool:
    """Check if user has all specified permissions"""
    user_role = await get_user_role(user)
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return all(perm in role_perms for perm in permissions)

async def has_any_permission(user: User, permissions: List[str]) -> bool:
    """Check if user has any of the specified permissions"""
    user_role = await get_user_role(user)
    role_perms = ROLE_PERMISSIONS.get(user_role, [])
    return any(perm in role_perms for perm in permissions)

def get_role_level(role: str) -> int:
    """Get role hierarchy level"""
    return ROLE_HIERARCHY.get(role, 0)

async def has_higher_role(user: User, target_role: str) -> bool:
    """Check if user has higher role than target role"""
    user_role = await get_user_role(user)
    user_level = get_role_level(user_role)
    target_level = get_role_level(target_role)
    return user_level > target_level

async def can_manage_user(manager: User, target_user: User) -> bool:
    """Check if manager can manage target user"""
    manager_role = await get_user_role(manager)
    target_role = await get_user_role(target_user)
    
    # Admins can manage everyone except other admins
    if manager_role == 'admin':
        return target_role != 'admin' or manager.id in config.ADMIN_IDS
    
    # Managers can manage lower roles
    if manager_role == 'manager':
        return get_role_level(target_role) < get_role_level(manager_role)
    
    return False

def get_available_roles_for_user(user_role: str) -> List[str]:
    """Get roles that user can assign to others"""
    user_level = get_role_level(user_role)
    
    if user_role == 'admin':
        # Admins can assign all roles except admin
        return [role for role, level in ROLE_HIERARCHY.items() 
                if role != 'admin' and role != 'blocked']
    
    if user_role == 'manager':
        # Managers can assign roles below their level
        return [role for role, level in ROLE_HIERARCHY.items() 
                if level < user_level and role != 'blocked']
    
    return []

def get_role_display_name(role: str, language: str = 'ru') -> str:
    """Get display name for role"""
    role_names = {
        'admin': {'uz': 'Administrator', 'ru': 'Администратор'},
        'manager': {'uz': 'Menejer', 'ru': 'Менеджер'},
        'controller': {'uz': 'Nazoratchi', 'ru': 'Контролер'},
        'call_center': {'uz': 'Call-markaz', 'ru': 'Call-центр'},
        'warehouse': {'uz': 'Ombor', 'ru': 'Склад'},
        'technician': {'uz': 'Texnik', 'ru': 'Техник'},
        'client': {'uz': 'Mijoz', 'ru': 'Клиент'},
        'blocked': {'uz': 'Bloklangan', 'ru': 'Заблокирован'}
    }
    
    return role_names.get(role, {}).get(language, role)

def get_role_emoji(role: str) -> str:
    """Get emoji for role"""
    role_emojis = {
        'admin': '👑',
        'manager': '👨‍💼',
        'controller': '🔍',
        'call_center': '📞',
        'warehouse': '📦',
        'technician': '🔧',
        'client': '👤',
        'blocked': '🚫'
    }
    
    return role_emojis.get(role, '❓')

async def get_role_statistics() -> dict:
    """Get role distribution statistics"""
    try:
        from database.base_queries import get_user_statistics
        stats = await get_user_statistics()
        return stats.get('role_distribution', {})
    except Exception as e:
        logger.error(f"Error getting role statistics: {str(e)}")
        return {}

def validate_role(role: str) -> bool:
    """Validate if role exists"""
    return role in ROLE_HIERARCHY

def get_all_roles() -> List[str]:
    """Get all available roles"""
    return list(ROLE_HIERARCHY.keys())

def get_staff_roles() -> List[str]:
    """Get staff roles (non-client roles)"""
    return [role for role in ROLE_HIERARCHY.keys() 
            if role not in ['client', 'blocked']]

def get_management_roles() -> List[str]:
    """Get management roles"""
    return ['admin', 'manager', 'junior_manager', 'controller']

def get_operational_roles() -> List[str]:
    """Get operational roles"""
    return ['call_center', 'warehouse', 'technician']

async def require_role(user: User, required_roles: List[str]) -> bool:
    """Decorator helper to require specific roles"""
    user_role = await get_user_role(user)
    return user_role in required_roles

async def require_permission(user: User, required_permission: str) -> bool:
    """Decorator helper to require specific permission"""
    return await has_permission(user, required_permission)

# Role-based access control decorators
def role_required(roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            user = message_or_callback.from_user
            if await require_role(user, roles):
                return await func(message_or_callback, *args, **kwargs)
            else:
                # Handle access denied
                await message_or_callback.answer("Access denied")
                return None
        return wrapper
    return decorator

def permission_required(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            user = message_or_callback.from_user
            if await require_permission(user, permission):
                return await func(message_or_callback, *args, **kwargs)
            else:
                # Handle access denied
                await message_or_callback.answer("Access denied")
                return None
        return wrapper
    return decorator

# Context managers for role checking
class RoleContext:
    """Context manager for role-based operations"""
    
    def __init__(self, user: User, required_roles: List[str]):
        self.user = user
        self.required_roles = required_roles
        self.has_access = False
    
    async def __aenter__(self):
        self.has_access = await require_role(self.user, self.required_roles)
        return self.has_access
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

# Utility functions
async def get_user_capabilities(user: User) -> dict:
    """Get user capabilities based on role"""
    user_role = await get_user_role(user)
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    
    return {
        'role': user_role,
        'level': get_role_level(user_role),
        'permissions': permissions,
        'can_manage_users': 'manage_users' in permissions,
        'can_view_all_zayavkas': 'view_all_zayavkas' in permissions,
        'can_assign_tasks': 'assign_tasks' in permissions,
        'can_manage_materials': 'manage_materials' in permissions
    }

async def log_role_change(user_id: int, old_role: str, new_role: str, changed_by: int):
    """Log role change for audit"""
    try:
        logger.info(f"Role changed for user {user_id}: {old_role} -> {new_role} by {changed_by}")
        # Additional logging to database if needed
    except Exception as e:
        logger.error(f"Error logging role change: {str(e)}")
