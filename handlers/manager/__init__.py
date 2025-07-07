from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .applications import get_manager_applications_router
from .equipment import get_manager_equipment_router
from .filters import get_manager_filters_router
from .language import get_manager_language_router
from .main_menu import get_manager_main_menu_router
from .notifications import get_manager_notifications_router
from .reports import get_manager_reports_router
from .staff_activity import get_manager_staff_activity_router
from .status_management import get_manager_status_management_router
from .technician_assignment import get_manager_technician_assignment_router
from utils.role_router import get_role_router

# Create main manager router using the reusable function
manager_router = get_role_router("manager")

# Include all sub-routers
manager_router.include_router(get_manager_main_menu_router())
manager_router.include_router(get_manager_applications_router())
manager_router.include_router(get_manager_status_management_router())
manager_router.include_router(get_manager_technician_assignment_router())
manager_router.include_router(get_manager_reports_router())
manager_router.include_router(get_manager_equipment_router())
manager_router.include_router(get_manager_staff_activity_router())
manager_router.include_router(get_manager_notifications_router())
manager_router.include_router(get_manager_language_router())
manager_router.include_router(get_manager_filters_router())

# Export the main router
def get_manager_router() -> Router:
    return manager_router


