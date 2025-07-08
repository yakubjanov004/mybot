from utils.role_router import get_role_router
from .main_menu import get_admin_main_menu_router
from .users import get_admin_users_router
from .orders import get_admin_orders_router
from .statistics import get_admin_statistics_router
from .settings import get_admin_settings_router
from .language import get_admin_language_router
from .callbacks import get_admin_callbacks_router
from aiogram.types import Message

admin_router = get_role_router("admin")
admin_router.include_router(get_admin_main_menu_router())
admin_router.include_router(get_admin_users_router())
admin_router.include_router(get_admin_orders_router())
admin_router.include_router(get_admin_statistics_router())
admin_router.include_router(get_admin_settings_router())
admin_router.include_router(get_admin_language_router())
admin_router.include_router(get_admin_callbacks_router())

def get_admin_router():
    return admin_router


