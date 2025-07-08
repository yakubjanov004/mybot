from utils.role_router import get_role_router
from .main_menu import get_technician_main_menu_router
from .tasks import get_technician_tasks_router
from .reports import get_technician_reports_router
from .language import get_technician_language_router
from .equipment import get_technician_equipment_router
from .communication import get_technician_communication_router
from .help import get_technician_help_router
from .profile import get_technician_profile_router

technician_router = get_role_router("technician")
technician_router.include_router(get_technician_main_menu_router())
technician_router.include_router(get_technician_tasks_router())
technician_router.include_router(get_technician_reports_router())
technician_router.include_router(get_technician_language_router())
technician_router.include_router(get_technician_equipment_router())
technician_router.include_router(get_technician_communication_router())
technician_router.include_router(get_technician_help_router())
technician_router.include_router(get_technician_profile_router())

def get_technician_router():
    return technician_router

