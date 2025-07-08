from utils.role_router import get_role_router
from .main_menu import get_call_center_main_menu_router
from .orders import get_call_center_orders_router
from .clients import get_call_center_clients_router
from .feedback import get_call_center_feedback_router
from .chat import get_call_center_chat_router
from .language import get_call_center_language_router
from .statistics import get_call_center_statistics_router
from aiogram.types import Message

call_center_router = get_role_router("call_center")
call_center_router.include_router(get_call_center_main_menu_router())
call_center_router.include_router(get_call_center_orders_router())
call_center_router.include_router(get_call_center_clients_router())
call_center_router.include_router(get_call_center_feedback_router())
call_center_router.include_router(get_call_center_chat_router())
call_center_router.include_router(get_call_center_language_router())
call_center_router.include_router(get_call_center_statistics_router())

def get_call_center_router():
    return call_center_router

__all__ = ['get_call_center_router']
