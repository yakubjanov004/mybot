"""
Enhanced Error Handler Middleware with Comprehensive Error Recovery

This middleware integrates with the comprehensive error recovery system to provide:
- Categorized error handling
- User-friendly error messages based on severity
- Critical error alerting
- Context-aware error logging

Requirements implemented: Task 12 - Create comprehensive error handling and recovery
"""

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from typing import Callable, Dict, Any, Union
import logging
import asyncio

from utils.error_recovery import error_handler, ErrorCategory

logger = logging.getLogger(__name__)


class EnhancedErrorHandlerMiddleware(BaseMiddleware):
    """Enhanced error handler middleware with comprehensive error recovery"""
    
    def __init__(self):
        self.error_handler = error_handler
    
    async def __call__(
        self,
        handler: Callable,
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramAPIError as e:
            # Handle Telegram API errors with context
            context = {
                'user_id': event.from_user.id,
                'event_type': type(event).__name__,
                'chat_id': event.chat.id if hasattr(event, 'chat') else None,
                'message_text': getattr(event, 'text', None) or getattr(event, 'data', None)
            }
            
            error_record = await self.error_handler.handle_error(e, context)
            
            # Send user-friendly error message based on language
            user_lang = data.get('user_lang', 'ru')
            if user_lang == 'uz':
                error_msg = "❗️ Xatolik yuz berdi. Keyinroq urinib ko'ring."
            else:
                error_msg = "❗️ Произошла ошибка. Попробуйте позже."
            
            try:
                if hasattr(event, 'answer'):
                    await event.answer(error_msg)
                elif hasattr(event, 'reply'):
                    await event.reply(error_msg)
            except Exception:
                # If we can't send error message, just log it
                logger.error(f"Failed to send error message to user {event.from_user.id}")
            
            logger.exception(f"Telegram error from user {event.from_user.id}: {str(e)}")
            
        except Exception as e:
            # Handle unexpected errors with comprehensive error recovery
            context = {
                'user_id': event.from_user.id,
                'event_type': type(event).__name__,
                'chat_id': event.chat.id if hasattr(event, 'chat') else None,
                'message_text': getattr(event, 'text', None) or getattr(event, 'data', None),
                'handler_name': handler.__name__ if hasattr(handler, '__name__') else 'unknown'
            }
            
            error_record = await self.error_handler.handle_error(e, context)
            
            # Send user-friendly error message based on language and severity
            user_lang = data.get('user_lang', 'ru')
            
            if error_record.severity.value in ['high', 'critical']:
                if user_lang == 'uz':
                    error_msg = "⚠️ Jiddiy xatolik yuz berdi. Admin bilan bog'laning."
                else:
                    error_msg = "⚠️ Произошла серьезная ошибка. Обратитесь к администратору."
            else:
                if user_lang == 'uz':
                    error_msg = "❗️ Xatolik yuz berdi. Keyinroq urinib ko'ring."
                else:
                    error_msg = "❗️ Произошла ошибка. Попробуйте позже."
            
            try:
                if hasattr(event, 'answer'):
                    await event.answer(error_msg)
                elif hasattr(event, 'reply'):
                    await event.reply(error_msg)
            except Exception:
                # If we can't send error message, just log it
                logger.error(f"Failed to send error message to user {event.from_user.id}")
            
            logger.exception(f"Unexpected error from user {event.from_user.id}: {str(e)}")
            
            # For critical errors, could trigger additional alerts
            if error_record.severity.value == 'critical':
                asyncio.create_task(self._handle_critical_error(error_record, context))
    
    async def _handle_critical_error(self, error_record, context):
        """Handle critical errors with additional alerting"""
        try:
            # In a real implementation, this could:
            # - Send alerts to admin users
            # - Create incident tickets
            # - Trigger emergency procedures
            logger.critical(f"Critical error handled: {error_record.id}")
            
            # For now, just log the critical error
            pass
            
        except Exception as e:
            logger.error(f"Failed to handle critical error: {e}")