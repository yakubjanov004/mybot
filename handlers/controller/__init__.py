from utils.role_router import get_role_router
from .language import get_controller_language_router
from .main_menu import get_controller_main_menu_router
from .orders import get_controller_orders_router
from .quality import get_controller_quality_router
from .reports import get_controller_reports_router
from .technicians import get_controller_technicians_router
from .technician import get_controller_technician_router
from aiogram.types import Message

controller_router = get_role_router("controller")
controller_router.include_router(get_controller_main_menu_router())
controller_router.include_router(get_controller_orders_router())
controller_router.include_router(get_controller_quality_router())
controller_router.include_router(get_controller_reports_router())
controller_router.include_router(get_controller_technicians_router())
controller_router.include_router(get_controller_technician_router())
controller_router.include_router(get_controller_language_router())

def get_controller_router():
    return controller_router


__all__ = ['get_controller_router']
