"""
Universal Notification Handler - Handles notification callbacks for all roles
Processes reply button clicks and displays pending assignments
"""

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.base_queries import get_user_by_telegram_id
from utils.notification_system import NotificationSystemFactory
from utils.logger import setup_module_logger
from utils.inline_cleanup import answer_and_cleanup

logger = setup_module_logger("universal_notifications")


def get_universal_notifications_router():
    """Get router for universal notification handling"""
    router = Router()
    notification_system = NotificationSystemFactory.create_notification_system()

    @router.callback_query(F.data.startswith("view_assignments_"))
    async def handle_view_assignments(callback: CallbackQuery):
        """Handle view assignments button click"""
        try:
            await answer_and_cleanup(callback, cleanup_after=False)
            
            # Get user info
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Пользователь не найден", show_alert=True)
                return
            
            # Handle notification reply
            result = await notification_system.handle_notification_reply(
                user['id'], callback.data
            )
            
            if not result['success']:
                error_msg = "Ошибка при загрузке заданий" if user.get('language', 'ru') == 'ru' else "Topshiriqlarni yuklashda xatolik"
                await callback.answer(error_msg, show_alert=True)
                return
            
            # Update message with assignments list
            try:
                await callback.message.edit_text(
                    text=result['message_text'],
                    reply_markup=result['keyboard'],
                    parse_mode='HTML'
                )
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Message content is the same, just answer the callback
                    await callback.answer()
                else:
                    raise
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error handling view assignments: {e}", exc_info=True)
            await callback.answer("Произошла ошибка", show_alert=True)

    @router.callback_query(F.data.startswith("refresh_assignments_"))
    async def handle_refresh_assignments(callback: CallbackQuery):
        """Handle refresh assignments button click"""
        try:
            await answer_and_cleanup(callback, cleanup_after=False)
            
            # Extract user_id from callback data
            user_id = int(callback.data.replace("refresh_assignments_", ""))
            
            # Get user info
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user or user['id'] != user_id:
                await callback.answer("Доступ запрещен", show_alert=True)
                return
            
            # Handle notification reply to get fresh data
            result = await notification_system.handle_notification_reply(
                user_id, f"refresh_{user_id}"
            )
            
            if not result['success']:
                error_msg = "Ошибка при обновлении" if user.get('language', 'ru') == 'ru' else "Yangilashda xatolik"
                await callback.answer(error_msg, show_alert=True)
                return
            
            # Update message with refreshed assignments
            try:
                await callback.message.edit_text(
                    text=result['message_text'],
                    reply_markup=result['keyboard'],
                    parse_mode='HTML'
                )
                
                refresh_msg = "Обновлено" if user.get('language', 'ru') == 'ru' else "Yangilandi"
                await callback.answer(refresh_msg)
                
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    no_changes_msg = "Нет изменений" if user.get('language', 'ru') == 'ru' else "O'zgarishlar yo'q"
                    await callback.answer(no_changes_msg)
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error handling refresh assignments: {e}", exc_info=True)
            await callback.answer("Произошла ошибка", show_alert=True)

    @router.callback_query(F.data.startswith("handle_request_"))
    async def handle_request_action(callback: CallbackQuery):
        """Handle request action button click"""
        try:
            await answer_and_cleanup(callback, cleanup_after=False)
            
            # Extract request_id from callback data
            request_id = callback.data.replace("handle_request_", "")
            
            # Get user info
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer("Пользователь не найден", show_alert=True)
                return
            
            lang = user.get('language', 'ru')
            
            # For now, just show request details and mark as handled
            # In a full implementation, this would redirect to the appropriate workflow handler
            
            # Mark notification as handled
            await notification_system.mark_notification_handled(user['id'], request_id)
            
            if lang == 'uz':
                message = f"📋 Topshiriq {request_id[:8]}... tanlandi.\n\nBu yerda tegishli workflow handler ishga tushadi."
            else:
                message = f"📋 Выбрано задание {request_id[:8]}...\n\nЗдесь должен запуститься соответствующий workflow handler."
            
            await callback.answer(message, show_alert=True)
            
            # Refresh the assignments list
            result = await notification_system.handle_notification_reply(
                user['id'], f"refresh_after_handle_{user['id']}"
            )
            
            if result['success']:
                try:
                    await callback.message.edit_text(
                        text=result['message_text'],
                        reply_markup=result['keyboard'],
                        parse_mode='HTML'
                    )
                except TelegramBadRequest:
                    pass  # Ignore if message is not modified
            
        except Exception as e:
            logger.error(f"Error handling request action: {e}", exc_info=True)
            await callback.answer("Произошла ошибка", show_alert=True)

    return router


# Export the router for registration
universal_notifications_router = get_universal_notifications_router()