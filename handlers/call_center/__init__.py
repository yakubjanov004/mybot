from utils.role_router import get_role_router
from .main_menu import get_call_center_main_menu_router
from .orders import get_call_center_orders_router
from .clients import get_call_center_clients_router
from .feedback import get_call_center_feedback_router
from .chat import get_call_center_chat_router
from .language import get_call_center_language_router
from .statistics import get_call_center_statistics_router
from .inbox import get_call_center_inbox_router
from .supervisor import get_call_center_supervisor_router
from .direct_resolution import get_call_center_direct_resolution_router
from .client_rating import get_call_center_client_rating_router
from .staff_application_creation import get_call_center_staff_application_router
from aiogram.types import Message

call_center_router = get_role_router("call_center")
call_center_router.include_router(get_call_center_main_menu_router())
call_center_router.include_router(get_call_center_orders_router())
call_center_router.include_router(get_call_center_clients_router())
call_center_router.include_router(get_call_center_feedback_router())
call_center_router.include_router(get_call_center_chat_router())
call_center_router.include_router(get_call_center_language_router())
call_center_router.include_router(get_call_center_statistics_router())
call_center_router.include_router(get_call_center_inbox_router())
call_center_router.include_router(get_call_center_direct_resolution_router())
call_center_router.include_router(get_call_center_staff_application_router())

# Separate routers for different roles
call_center_supervisor_router = get_role_router("call_center_supervisor")
call_center_supervisor_router.include_router(get_call_center_supervisor_router())

client_rating_router = get_role_router("client")
client_rating_router.include_router(get_call_center_client_rating_router())

def get_call_center_router():
    return call_center_router

__all__ = ['get_call_center_router']
