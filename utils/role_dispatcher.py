from aiogram import Dispatcher, Router
from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger('bot.role_dispatcher')

class RoleAwareDispatcher:
    """Dispatcher wrapper that handles role-based routing"""
    
    def __init__(self, dispatcher: Dispatcher):
        self.dispatcher = dispatcher
        self.role_routers: Dict[str, Router] = {}
        self.global_routers: List[Router] = []
        
    def register_role_router(self, role: str, router: Router):
        """Register a router for a specific role"""
        self.role_routers[role] = router
        self.dispatcher.include_router(router)
        logger.info(f"Registered role router: {role}")
        
    def register_global_router(self, router: Router):
        """Register a router that handles global commands"""
        self.global_routers.append(router)
        self.dispatcher.include_router(router)
        logger.info("Registered global router")
        
    def get_role_router(self, role: str) -> Router:
        """Get router for specific role"""
        return self.role_routers.get(role)
        
    def get_all_roles(self) -> List[str]:
        """Get list of all registered roles"""
        return list(self.role_routers.keys())

# Global RoleAwareDispatcher instance (to be initialized in main or loader)
global_role_dispatcher: RoleAwareDispatcher = None

def set_global_role_dispatcher(dispatcher: RoleAwareDispatcher):
    global global_role_dispatcher
    global_role_dispatcher = dispatcher
    logger.info("Global RoleAwareDispatcher set.")

def get_role_router(role: str):
    if global_role_dispatcher is None:
        raise RuntimeError("Global RoleAwareDispatcher is not set.")
    return global_role_dispatcher.get_role_router(role)
