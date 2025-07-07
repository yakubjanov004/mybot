from utils.role_router import get_role_router
from .export import router as export_router
from .inventory import router as inventory_router
from .language import get_warehouse_language_router
from .main_menu import get_warehouse_main_menu_router
from .orders import get_warehouse_orders_router
from .statistics import get_warehouse_statistics_router
from aiogram.types import Message

warehouse_router = get_role_router("warehouse")
warehouse_router.include_router(export_router)
warehouse_router.include_router(inventory_router)
warehouse_router.include_router(get_warehouse_language_router())
warehouse_router.include_router(get_warehouse_main_menu_router())
warehouse_router.include_router(get_warehouse_orders_router())
warehouse_router.include_router(get_warehouse_statistics_router())

def get_warehouse_router():
    return warehouse_router
