from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .chat import get_call_center_chat_router
from .clients import get_call_center_clients_router
from .feedback import get_call_center_feedback_router
from .language import get_call_center_language_router
from .main_menu import get_call_center_main_menu_router
from .orders import get_call_center_orders_router
from .statistics import get_call_center_statistics_router

def get_call_center_router() -> Router:
    call_center_router = Router()
    call_center_router.message.filter(RoleFilter("call_center"))
    call_center_router.include_router(get_call_center_chat_router())
    call_center_router.include_router(get_call_center_clients_router())
    call_center_router.include_router(get_call_center_feedback_router())
    call_center_router.include_router(get_call_center_language_router())
    call_center_router.include_router(get_call_center_main_menu_router())
    call_center_router.include_router(get_call_center_orders_router())
    call_center_router.include_router(get_call_center_statistics_router())
    
    @call_center_router.message()
    async def unknown_command(message: Message):
        await message.answer("⚠️ Noma'lum buyruq. Iltimos, menyudan tanlang.")
    
    return call_center_router

__all__ = ['get_call_center_router']
