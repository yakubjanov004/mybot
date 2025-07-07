from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from utils.get_role import get_user_role
import logging

logger = logging.getLogger(__name__)

class RoleFilter(BaseFilter):
    def __init__(self, role: str):
        self.role = role

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        try:
            user_id = event.from_user.id
            user_role = await get_user_role(user_id)
            result = user_role == self.role
            logger.debug(f"RoleFilter: user_id={user_id}, user_role={user_role}, required_role={self.role}, result={result}")
            return result
        except Exception as e:
            logger.error(f"Error in RoleFilter: {str(e)}")
            return False
