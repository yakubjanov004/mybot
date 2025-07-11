from utils.role_router import get_role_router
from .main_menu import router as main_menu_router
from .language import router as language_router
from .orders import router as orders_router
from .statistics import router as statistics_router

junior_manager_router = get_role_router("junior_manager")
junior_manager_router.include_router(main_menu_router)
junior_manager_router.include_router(language_router)
junior_manager_router.include_router(orders_router)
junior_manager_router.include_router(statistics_router)

def get_junior_manager_router():
    return junior_manager_router 