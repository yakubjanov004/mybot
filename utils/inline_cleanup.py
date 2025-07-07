import asyncio
from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from utils.logger import setup_module_logger
import logging

logger = logging.getLogger(__name__)

class InlineMessageManager:
    """Manages inline messages and their cleanup"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self._messages = {}  # user_id: {message_id: timestamp}
        self._cleanup_interval = 60  # sekundlarda tekshirish
        self._message_ttl = 300  # 5 daqiqa ichida tozalansin
        self._cleanup_task = None

    async def stop_auto_cleanup(self):
        """Stop the auto cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("[InlineCleanup] Auto cleanup task stopped")

    async def start_auto_cleanup(self):
        """Start the auto cleanup task"""
        if self._cleanup_task and not self._cleanup_task.done():
            await self.stop_auto_cleanup()

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self._cleanup_interval)
                    await self._cleanup_old_messages()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[InlineCleanup] Error in cleanup loop: {str(e)}", exc_info=True)

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("[InlineCleanup] Auto cleanup task started")
    
    async def track(self, user_id: int, message_id: int):
        """Track inline message for cleanup"""
        logger.info(f"[InlineCleanup] Tracking message: user_id={user_id}, message_id={message_id}")
        # Hide all previous inline keyboards for this user
        old_messages = list(self._messages.get(user_id, {}).keys())
        for old_msg_id in old_messages:
            if old_msg_id != message_id:
                try:
                    logger.info(f"[InlineCleanup] Hiding old inline: user_id={user_id}, message_id={old_msg_id}")
                    # Try to edit the message, but don't fail if it doesn't work
                    try:
                        await self.bot.edit_message_reply_markup(
                            chat_id=user_id,
                            message_id=old_msg_id,
                            reply_markup=None
                        )
                    except Exception as e:
                        logger.debug(f"[InlineCleanup] Failed to edit message {old_msg_id}: {str(e)}")
                finally:
                    # Always remove from tracking
                    if user_id in self._messages and old_msg_id in self._messages[user_id]:
                        del self._messages[user_id][old_msg_id]
        # Only keep the latest message_id for this user
        self._messages[user_id] = {message_id: datetime.utcnow()}

    async def _safe_edit_message(self, chat_id: int, message_id: int, reply_markup: dict):
        """Safe wrapper for edit_message_reply_markup with error handling"""
        try:
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=reply_markup
            )
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e).lower() or "message is not modified" in str(e).lower():
                logger.debug(f"[InlineCleanup] Message {message_id} already deleted or not modified for chat {chat_id}")
            else:
                logger.warning(f"[InlineCleanup] Error editing message {message_id} for chat {chat_id}: {e}")
        except Exception as e:
            logger.warning(f"[InlineCleanup] Error editing message {message_id} for chat {chat_id}: {e}")
        # Only keep the latest message_id for this user
        self._messages[user_id] = {message_id: datetime.utcnow()}
    
    async def _auto_cleanup(self):
        """Start background cleanup task"""
        logger.info("[InlineCleanup] Auto cleanup task started")
        while True:
            await asyncio.sleep(self._cleanup_interval)
            now = datetime.now()
            for user_id, messages in list(self._messages.items()):
                for message_id, timestamp in list(messages.items()):
                    if (now - timestamp).total_seconds() > self._message_ttl:
                        try:
                            logger.info(f"[InlineCleanup] Cleaning up: user_id={user_id}, message_id={message_id}")
                            try:
                                await self.bot.edit_message_reply_markup(
                                    chat_id=user_id,
                                    message_id=message_id,
                                    reply_markup=None
                                )
                            except TelegramBadRequest as e:
                                if "message can't be edited" in str(e).lower():
                                    logger.debug(f"[InlineCleanup] Message {message_id} is too old to edit for user {user_id}")
                                else:
                                    logger.warning(f"[InlineCleanup] Telegram error editing message {message_id} for user {user_id}: {e}")
                            except Exception as e:
                                logger.warning(f"[InlineCleanup] Unexpected error cleaning up message {message_id} for user {user_id}: {e}")
                        except Exception as e:
                            logger.error(f"[InlineCleanup] Critical error in cleanup process for message {message_id}: {e}", exc_info=True)
                        finally:
                            # Always remove from tracking
                            if user_id in self._messages and message_id in self._messages[user_id]:
                                del self._messages[user_id][message_id]
    
    async def cleanup_user_messages(self, user_id: int, keep_last: int = 1):
        """Clean up user's inline messages, keeping the last N messages by removing only the inline keyboard"""
        if user_id not in self._messages:
            return
        
        messages = self._messages[user_id]
        if len(messages) <= keep_last:
            return
        
        # Sort by timestamp and keep only the newest ones
        sorted_messages = sorted(messages.items(), key=lambda x: x[1], reverse=True)
        messages_to_cleanup = sorted_messages[keep_last:]
        
        cleaned_count = 0
        for message_id, _ in messages_to_cleanup:
            try:
                await self.bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=None)
                del self._messages[user_id][message_id]
                cleaned_count += 1
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
            except TelegramBadRequest as e:
                if "message to edit not found" in str(e).lower() or "message is not modified" in str(e).lower():
                    del self._messages[user_id][message_id]
                else:
                    logger.warning(f"Failed to edit reply markup for message {message_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error editing reply markup for message {message_id}: {str(e)}")
        if cleaned_count > 0:
            logger.debug(f"Cleaned up inline keyboards for {cleaned_count} messages for user {user_id}")
    
    async def cleanup_old_messages(self):
        """Clean up old tracked messages by removing only the inline keyboard"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=self._message_ttl)
        total_cleaned = 0
        for user_id in list(self._messages.keys()):
            messages = self._messages[user_id]
            old_messages = [
                msg_id for msg_id, timestamp in messages.items()
                if timestamp < cutoff_time
            ]
            for message_id in old_messages:
                try:
                    await self.bot.edit_message_reply_markup(chat_id=user_id, message_id=message_id, reply_markup=None)
                    del self._messages[user_id][message_id]
                    total_cleaned += 1
                    await asyncio.sleep(0.1)
                except TelegramBadRequest as e:
                    if "message to edit not found" in str(e).lower() or "message is not modified" in str(e).lower():
                        del self._messages[user_id][message_id]
                    else:
                        logger.warning(f"Failed to edit reply markup for old message {message_id}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error editing reply markup for old message {message_id}: {str(e)}")
            if not self._messages[user_id]:
                del self._messages[user_id]
        if total_cleaned > 0:
            logger.info(f"Cleaned up inline keyboards for {total_cleaned} old messages")
    
    def get_stats(self) -> Dict:
        """Get cleanup statistics"""
        total_messages = sum(len(messages) for messages in self._messages.values())
        
        return {
            'tracked_users': len(self._messages),
            'total_tracked_messages': total_messages,
            'cleanup_interval': self._cleanup_interval,
            'message_ttl': self._message_ttl
        }

    def start_auto_cleanup(self, loop=None):
        """Start the auto cleanup task. Should be called from an async context (e.g., on_startup)."""
        import asyncio
        if loop is None:
            loop = asyncio.get_running_loop()
        self._cleanup_task = loop.create_task(self._auto_cleanup())

# Global instance
_inline_manager: Optional[InlineMessageManager] = None

def init_inline_cleanup(bot: Bot):
    """Initialize inline cleanup manager"""
    global _inline_manager
    _inline_manager = InlineMessageManager(bot)
    return _inline_manager

def get_inline_manager() -> Optional[InlineMessageManager]:
    """Get inline cleanup manager instance"""
    return _inline_manager

async def send_and_track(bot: Bot, chat_id: int, text: str, 
                        reply_markup: Optional[InlineKeyboardMarkup] = None,
                        **kwargs) -> Message:
    """Send message and track it for cleanup"""
    message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        **kwargs
    )
    
    if _inline_manager and reply_markup:
        _inline_manager.track(chat_id, message.message_id)
    
    return message

async def edit_and_track(message: Message, text: str,
                        reply_markup: Optional[InlineKeyboardMarkup] = None,
                        **kwargs) -> Message:
    """Edit message and track it for cleanup"""
    edited_message = await message.edit_text(
        text=text,
        reply_markup=reply_markup,
        **kwargs
    )
    
    if _inline_manager and reply_markup:
        _inline_manager.track(message.chat.id, message.message_id)
    
    return edited_message

async def cleanup_user_inline_messages(user_id: int, keep_last: int = 1):
    """Clean up user's inline messages"""
    if _inline_manager:
        await _inline_manager.cleanup_user_messages(user_id, keep_last)

async def answer_and_cleanup(callback_query, text: str = None, show_alert: bool = False,
                           cleanup_after: bool = True):
    """Answer callback query and optionally cleanup messages"""
    try:
        await callback_query.answer(text, show_alert=show_alert)
        
        if cleanup_after and _inline_manager:
            # Schedule cleanup after a short delay
            asyncio.create_task(
                _delayed_cleanup(callback_query.from_user.id, delay=2)
            )
    
    except Exception as e:
        logger.error(f"Error in answer_and_cleanup: {str(e)}")

async def _delayed_cleanup(user_id: int, delay: int = 2):
    """Delayed cleanup helper"""
    await asyncio.sleep(delay)
    await cleanup_user_inline_messages(user_id, keep_last=1)

# Context manager for message cleanup
class MessageCleanupContext:
    """Context manager for automatic message cleanup"""
    
    def __init__(self, user_id: int, keep_last: int = 1):
        self.user_id = user_id
        self.keep_last = keep_last
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if _inline_manager:
            await _inline_manager.cleanup_user_messages(self.user_id, self.keep_last)

# Decorators for automatic cleanup
def cleanup_after(keep_last: int = 1):
    """Decorator to cleanup messages after handler execution"""
    def decorator(func):
        async def wrapper(message_or_callback, *args, **kwargs):
            result = await func(message_or_callback, *args, **kwargs)
            
            # Get user ID
            if hasattr(message_or_callback, 'from_user'):
                user_id = message_or_callback.from_user.id
            elif hasattr(message_or_callback, 'chat'):
                user_id = message_or_callback.chat.id
            else:
                return result
            
            # Schedule cleanup
            if _inline_manager:
                asyncio.create_task(
                    _inline_manager.cleanup_user_messages(user_id, keep_last)
                )
            
            return result
        
        return wrapper
    return decorator

# Utility functions
async def safe_delete_message(bot: Bot, chat_id: int, message_id: int) -> bool:
    """Safely delete message with error handling"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except TelegramBadRequest as e:
        if "message to delete not found" not in str(e).lower():
            logger.warning(f"Failed to delete message {message_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {str(e)}")
        return False

async def safe_edit_message(message: Message, text: str, 
                          reply_markup: Optional[InlineKeyboardMarkup] = None) -> bool:
    """Safely edit message with error handling"""
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"Failed to edit message: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error editing message: {str(e)}")
        return False

def create_cleanup_keyboard(buttons: List[List], cleanup_after: int = 300) -> InlineKeyboardMarkup:
    """Create keyboard that will be cleaned up after specified time"""
    # This is a placeholder - actual implementation would need to track cleanup time
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def batch_delete_messages(bot: Bot, chat_id: int, message_ids: List[int]) -> int:
    """Delete multiple messages in batch"""
    deleted_count = 0
    
    for message_id in message_ids:
        if await safe_delete_message(bot, chat_id, message_id):
            deleted_count += 1
        
        # Small delay to avoid rate limits
        await asyncio.sleep(0.1)
    
    return deleted_count

# Statistics and monitoring
async def get_cleanup_stats() -> Dict:
    """Get cleanup statistics"""
    if _inline_manager:
        return _inline_manager.get_stats()
    
    return {
        'tracked_users': 0,
        'total_tracked_messages': 0,
        'status': 'not_initialized'
    }

async def force_cleanup_all():
    """Force cleanup of all tracked messages"""
    if _inline_manager:
        await _inline_manager.cleanup_old_messages()
        logger.info("Forced cleanup of all tracked messages")

def safe_remove_inline(message: Message):
    """
    Faqat bot yuborgan inline xabarni (reply_markup) olib tashlaydi.
    """
    try:
        return message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

def safe_remove_inline_call(call: CallbackQuery):
    """
    Callback orqali kelgan inline xabarni (reply_markup) olib tashlaydi.
    """
    try:
        return call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
