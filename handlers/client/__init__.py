from utils.role_router import get_role_router
from .start import get_client_start_router
from .contact import get_client_contact_router
from .feedback import get_client_feedback_router
from .help import get_client_help_router
from .language import get_client_language_router
from .main_menu import get_client_main_menu_router
from .connection_order import get_connection_order_router
from .service_order import get_service_order_router
from .profile import get_client_profile_router
from aiogram.types import Message

client_router = get_role_router("client")
client_router.include_router(get_client_start_router())
client_router.include_router(get_client_contact_router())
client_router.include_router(get_client_feedback_router())
client_router.include_router(get_client_help_router())
client_router.include_router(get_client_language_router())
client_router.include_router(get_client_main_menu_router())
client_router.include_router(get_connection_order_router())
client_router.include_router(get_service_order_router())
client_router.include_router(get_client_profile_router())

def get_client_router():
    return client_router

