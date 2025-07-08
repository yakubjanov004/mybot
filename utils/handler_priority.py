from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Default priority value for handlers
PRIORITY_DEFAULT = 500
# High priority value for handlers
PRIORITY_HIGH = 1000

class HandlerPriorityManager:
    """
    Manages handler priorities to ensure correct role-based routing.
    This helps prevent conflicts when multiple roles have similar handlers.
    """
    
    # Priority levels (higher number = higher priority)
    PRIORITY_LEVELS = {
        'global': 1000,      # Global navigation (highest)
        'admin': 900,        # Admin functions
        'manager': 800,      # Manager functions
        'controller': 700,   # Controller functions
        'call_center': 600,  # Call center functions
        'warehouse': 500,    # Warehouse functions
        'technician': 400,   # Technician functions
        'client': 100        # Client functions (lowest)
    }
    
    @classmethod
    def get_role_priority(cls, role: str) -> int:
        """Get priority level for a role"""
        return cls.PRIORITY_LEVELS.get(role, 0)
    
    @classmethod
    def sort_roles_by_priority(cls, roles: List[str]) -> List[str]:
        """Sort roles by priority (highest first)"""
        return sorted(roles, key=cls.get_role_priority, reverse=True)
    
    @classmethod
    def should_handle_first(cls, role1: str, role2: str) -> bool:
        """Check if role1 should handle before role2"""
        return cls.get_role_priority(role1) > cls.get_role_priority(role2)
    
    @classmethod
    def get_handler_order(cls) -> List[str]:
        """Get recommended handler registration order"""
        roles = list(cls.PRIORITY_LEVELS.keys())
        return cls.sort_roles_by_priority(roles)
    
    @classmethod
    def log_priority_info(cls):
        """Log priority information for debugging"""
        logger.info("Handler Priority Levels:")
        for role in cls.sort_roles_by_priority(list(cls.PRIORITY_LEVELS.keys())):
            priority = cls.get_role_priority(role)
            logger.info(f"  {role}: {priority}")
