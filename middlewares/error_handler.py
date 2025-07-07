from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from typing import Callable, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramAPIError as e:
            logger.exception(f"Telegram error from user {event.from_user.id}: {str(e)}")
            await event.answer("❗️ Xatolik yuz berdi. Keyinroq urinib ko‘ring.")
        except Exception as e:
            logger.exception(f"Unexpected error from user {event.from_user.id}: {str(e)}")
            await event.answer("⚠️ Ichki xatolik. Admin bilan bog‘laning.")
