from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .language import get_controller_language_router
from .main_menu import get_controller_main_menu_router
from .orders import get_controller_orders_router
from .quality import get_controller_quality_router
from .reports import get_controller_reports_router
from .technicians import get_controller_technicians_router

def get_controller_router() -> Router:
    controller_router = Router()
    controller_router.message.filter(RoleFilter("controller"))
    controller_router.include_router(get_controller_main_menu_router())
    controller_router.include_router(get_controller_orders_router())
    controller_router.include_router(get_controller_quality_router())
    controller_router.include_router(get_controller_reports_router())
    controller_router.include_router(get_controller_technicians_router())
    controller_router.include_router(get_controller_language_router())
    
    @controller_router.message()
    async def unknown_command(message: Message):
        await message.answer("⚠️ Noma'lum buyruq. Iltimos, menyudan tanlang.")
    
    return controller_router

__all__ = ['get_controller_router']
