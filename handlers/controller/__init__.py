from utils.role_router import get_role_router
from .main_menu import get_controller_main_menu_router
from .orders import get_controller_orders_router
from .quality import get_controller_quality_router
from .reports import get_controller_reports_router
from .technician import get_controller_technician_router
from .technicians import get_controller_technicians_router
from .language import get_controller_language_router
from .inbox import get_controller_inbox_router
from .applications import get_applications_router
from .technical_service import get_controller_technical_service_router
from .staff_application_creation import get_controller_staff_application_router

controller_router = get_role_router("controller")
controller_router.include_router(get_controller_main_menu_router())
controller_router.include_router(get_controller_orders_router())
controller_router.include_router(get_controller_quality_router())
controller_router.include_router(get_controller_reports_router())
controller_router.include_router(get_controller_technician_router())
controller_router.include_router(get_controller_technicians_router())
controller_router.include_router(get_controller_language_router())
controller_router.include_router(get_controller_inbox_router())
controller_router.include_router(get_applications_router())
controller_router.include_router(get_controller_technical_service_router())
controller_router.include_router(get_controller_staff_application_router())

def get_controller_router():
    return controller_router


__all__ = ['get_controller_router']
