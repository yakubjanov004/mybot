"""
Database package initialization
"""

from .models import (
    User, Zayavka, Material, MaterialUsage, TechnicianTask,
    Feedback, ChatMessage, SupportChat, HelpRequest, Equipment, Notification,
    UserRole, ZayavkaStatus, Priority, Models, ModelConstants
)

from .base_queries import (
    DatabaseManager,
    get_user_by_telegram_id, create_user,
    get_zayavka_by_id, create_zayavka, update_zayavka_status,
    get_user_statistics, get_zayavka_statistics
)

__all__ = [
    # Models
    'User', 'Zayavka', 'Material', 'MaterialUsage', 'TechnicianTask',
    'Feedback', 'ChatMessage', 'SupportChat', 'HelpRequest', 'Equipment', 'Notification',
    'UserRole', 'ZayavkaStatus', 'Priority', 'Models', 'ModelConstants',
    # Database Manager
    'DatabaseManager',
    # Base queries
    'get_user_by_telegram_id', 'create_user',
    'get_zayavka_by_id', 'create_zayavka', 'update_zayavka_status',
    'get_user_statistics', 'get_zayavka_statistics'
]
