from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .export import router as export_router
from .inventory import router as inventory_router
from .language import get_warehouse_language_router
from .main_menu import get_warehouse_main_menu_router
from .orders import get_warehouse_orders_router
from .statistics import get_warehouse_statistics_router

def get_warehouse_router() -> Router:
    warehouse_router = Router()
    warehouse_router.message.filter(RoleFilter("warehouse"))
    warehouse_router.include_router(export_router)
    warehouse_router.include_router(inventory_router)
    warehouse_router.include_router(get_warehouse_language_router())
    warehouse_router.include_router(get_warehouse_main_menu_router())
    warehouse_router.include_router(get_warehouse_orders_router())
    warehouse_router.include_router(get_warehouse_statistics_router())
    
    @warehouse_router.message()
    async def unknown_command(message: Message):
        await message.answer("⚠️ Noma'lum buyruq. Iltimos, menyudan tanlang.")
    
    return warehouse_router
