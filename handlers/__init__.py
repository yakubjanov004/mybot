import logging
from aiogram import Router

from handlers.admin import get_admin_router
from handlers.manager import get_manager_router
from handlers.technician import get_technician_router
from handlers.client import get_client_router
from handlers.call_center import get_call_center_router
from handlers.controller import get_controller_router
from handlers.warehouse import get_warehouse_router
from handlers.junior_manager import get_junior_manager_router
from handlers.global_navigation import get_global_navigation_router
from handlers.universal_inbox import get_universal_inbox_router
from handlers.universal_notifications import get_universal_notifications_router
from handlers.connection_workflow import get_connection_workflow_router
from handlers.client_rating import get_client_rating_router
from handlers.technical_service_workflow import get_technical_service_workflow_handler
from handlers.workflow_integration_handler import get_workflow_integration_handler
from handlers.shared_staff_application_flow import get_shared_staff_application_flow_router
# Import any additional shared/global routers if needed

from database.base_queries import create_user_if_not_exists

logger = logging.getLogger(__name__)

def setup_handlers(dp):
    """Setup all handlers for the dispatcher"""
    try:
        logger.info("Setting up handlers...")

        # Include all role-based routers FIRST
        dp.include_router(get_admin_router())
        dp.include_router(get_manager_router())
        dp.include_router(get_technician_router())
        dp.include_router(get_client_router())
        dp.include_router(get_call_center_router())
        dp.include_router(get_controller_router())
        dp.include_router(get_warehouse_router())
        dp.include_router(get_junior_manager_router())
        dp.include_router(get_universal_inbox_router())
        dp.include_router(get_universal_notifications_router())
        
        # Include shared staff application flow handler
        dp.include_router(get_shared_staff_application_flow_router())
        
        # Include workflow handlers
        dp.include_router(get_connection_workflow_router())
        dp.include_router(get_client_rating_router())
        dp.include_router(get_technical_service_workflow_handler().get_router())
        dp.include_router(get_workflow_integration_handler().get_router())

        # Register global navigation router last
        dp.include_router(get_global_navigation_router())

        logger.info("All handlers registered successfully")
    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")
        raise
