from aiogram import Router
from filters.role_filter import RoleFilter


def get_role_router(role):
    """
    Returns a Router for the given role, with RoleFilter applied to all messages and callback queries.
    The router is named as <role_name>_router.
    """
    router = Router(name=f"{role}_router")
    router.message.filter(RoleFilter(role))
    router.callback_query.filter(RoleFilter(role))
    return router 