from aiogram import Router
from aiogram.types import Message
from filters.role_filter import RoleFilter
from .start import get_client_start_router
from .contact import get_client_contact_router
from .feedback import get_client_feedback_router
from .help import get_client_help_router
from .language import get_client_language_router
from .main_menu import get_client_main_menu_router
from .order import get_client_order_router
from .profile import get_client_profile_router

def get_client_router() -> Router:
    router = Router()
    router.message.filter(RoleFilter("client"))
    router.callback_query.filter(RoleFilter("client"))
    
    router.include_router(get_client_start_router())
    router.include_router(get_client_contact_router())
    router.include_router(get_client_feedback_router())
    router.include_router(get_client_help_router())
    router.include_router(get_client_language_router())
    router.include_router(get_client_main_menu_router())
    router.include_router(get_client_order_router())
    router.include_router(get_client_profile_router())
    
    return router
