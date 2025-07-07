from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class LoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        logger.info(f"[{user.id}] {user.full_name} → {event.text if isinstance(event, Message) else event.data}")
        return await handler(event, data)
