import logging
from aiogram import Router

from database.base_queries import create_user_if_not_exists

logger = logging.getLogger(__name__)

def setup_handlers(dp):
    """Setup all handlers for the dispatcher"""
    try:
        logger.info("Setting up handlers...")
        
        # Admin handlers
        try:
            from .admin import get_admin_router
            admin_router = get_admin_router()
            dp.include_router(admin_router)
            logger.info("Admin handlers registered")
        except Exception as e:
            logger.error(f"Error registering admin handlers: {str(e)}")

        # Client handlers
        try:
            from .client import get_client_router
            client_router = get_client_router()
            dp.include_router(client_router)
            logger.info("Client handlers registered")
        except Exception as e:
            logger.error(f"Error registering client handlers: {str(e)}")

        # Manager handlers
        try:
            from .manager import get_manager_router
            manager_router = get_manager_router()
            dp.include_router(manager_router)
            logger.info("Manager handlers registered")
        except Exception as e:
            logger.error(f"Error registering manager handlers: {str(e)}")

        # Technician handlers
        try:
            from .technician import get_technician_router
            technician_router = get_technician_router()
            dp.include_router(technician_router)
            logger.info("Technician handlers registered")
        except Exception as e:
            logger.error(f"Error registering technician handlers: {str(e)}")

        # Call Center handlers
        try:
            from .call_center import get_call_center_router
            call_center_router = get_call_center_router()
            dp.include_router(call_center_router)
            logger.info("Call center handlers registered")
        except Exception as e:
            logger.error(f"Error registering call center handlers: {str(e)}")

        # Controller handlers
        try:
            from .controller import get_controller_router
            controller_router = get_controller_router()
            dp.include_router(controller_router)
            logger.info("Controller handlers registered")
        except Exception as e:
            logger.error(f"Error registering controller handlers: {str(e)}")

        # Warehouse handlers
        try:
            from .warehouse import get_warehouse_router
            warehouse_router = get_warehouse_router()
            dp.include_router(warehouse_router)
            logger.info("Warehouse handlers registered")
        except Exception as e:
            logger.error(f"Error registering warehouse handlers: {str(e)}")

        # Global start handler for all users
        start_router = Router()
        
        @start_router.message(lambda message: message.text == "/start")
        async def global_start_handler(message, state):  # <-- add state here
            from utils.get_role import get_user_role
            from handlers.admin.main_menu import show_admin_main_menu

            # Create user if not exists
            await create_user_if_not_exists(
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )
            
            # Get user role and redirect to appropriate handler
            user_role = await get_user_role(message.from_user.id)
            
            if user_role == "admin":
                from handlers.admin.main_menu import show_admin_main_menu
                await show_admin_main_menu(message, state)  # <-- pass state
            elif user_role == "client":
                from handlers.client.start import handle_start
                await handle_start(message)
            elif user_role == "manager":
                from handlers.manager.main_menu import show_manager_main_menu
                await show_manager_main_menu(message)
            elif user_role == "technician":
                from handlers.technician.main_menu import show_technician_main_menu
                await show_technician_main_menu(message)
            elif user_role == "call_center":
                from handlers.call_center.main_menu import show_call_center_main_menu
                await show_call_center_main_menu(message)
            elif user_role == "controller":
                from handlers.controller.main_menu import show_controller_main_menu
                await show_controller_main_menu(message)
            elif user_role == "warehouse":
                from handlers.warehouse.main_menu import show_warehouse_main_menu
                await show_warehouse_main_menu(message)
            else:
                await message.answer("Sizning rolingiz aniqlanmadi. Iltimos, administratorga murojaat qiling.")
        
        dp.include_router(start_router)
        logger.info("Global start handler registered")

        logger.info("All handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Error setting up handlers: {str(e)}")
        raise
