from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .main_menu import get_admin_main_menu_router
from .users import get_admin_users_router
from .orders import get_admin_orders_router
from .statistics import get_admin_statistics_router
from .settings import get_admin_settings_router
from .language import get_admin_language_router

def get_admin_router() -> Router:
    """Get combined admin router"""
    admin_router = Router()
    admin_router.message.filter(RoleFilter("admin"))
    admin_router.callback_query.filter(RoleFilter("admin"))
    
    # Include all sub-routers
    admin_router.include_router(get_admin_main_menu_router())
    admin_router.include_router(get_admin_users_router())
    admin_router.include_router(get_admin_orders_router())
    admin_router.include_router(get_admin_statistics_router())
    admin_router.include_router(get_admin_settings_router())
    admin_router.include_router(get_admin_language_router())
    
    return admin_router
