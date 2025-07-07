from aiogram import Router
from filters.role_filter import RoleFilter


def get_role_router(role_name: str) -> Router:
    """
    Returns a Router for the given role, with RoleFilter applied to all messages and callback queries.
    The router is named as <role_name>_router.
    """
    router = Router(name=f"{role_name}_router")
    router.message.filter(RoleFilter(role_name))
    router.callback_query.filter(RoleFilter(role_name))
    return router 