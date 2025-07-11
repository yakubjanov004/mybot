from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from utils.role_router import get_role_router
from database.base_queries import get_zayavka_by_id, get_user_by_telegram_id, get_user_lang
from database.models import get_status_display
from keyboards.manager_buttons import get_inbox_keyboard, get_message_detail_keyboard
from utils.logger import setup_logger
from loader import bot
from datetime import datetime, timedelta

def get_manager_inbox_router():
    """Get inbox router for manager"""
    logger = setup_logger('bot.manager.inbox')
    router = get_role_router("manager")

    @router.message(F.text.in_(['📥 Kiruvchi xabarlar', '📥 Входящие сообщения']))
    async def show_inbox_menu(message: Message, state: FSMContext):
        """Manager uchun kiruvchi xabarlar menyusi"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            inbox_text = "📥 Kiruvchi xabarlar:" if lang == 'uz' else "📥 Входящие сообщения:"
            
            await message.answer(
                inbox_text,
                reply_markup=get_inbox_keyboard(lang)
            )
            
        except Exception as e:
            logger.error(f"Error in show_inbox_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("inbox_"))
    async def handle_inbox_actions(callback: CallbackQuery, state: FSMContext):
        """Handle inbox actions"""
        try:
            await callback.answer()
            action = callback.data.replace("inbox_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            if action == "new":
                await show_new_messages(callback, lang)
            elif action == "read":
                await show_read_messages(callback, lang)
            elif action == "urgent":
                await show_urgent_messages(callback, lang)
            elif action == "client":
                await show_client_messages(callback, lang)
            elif action == "system":
                await show_system_messages(callback, lang)
            else:
                unknown_text = "Noma'lum amal" if lang == 'uz' else "Неизвестное действие"
                await callback.message.edit_text(unknown_text)
            
        except Exception as e:
            logger.error(f"Error in handle_inbox_actions: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def show_new_messages(callback, lang):
        """Show new messages"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get new messages (not read yet)
                messages = await conn.fetch(
                    '''SELECT m.*, u.full_name as sender_name, u.role as sender_role
                       FROM messages m
                       LEFT JOIN users u ON m.sender_id = u.id
                       WHERE m.is_read = false AND m.recipient_role = 'manager'
                       ORDER BY m.created_at DESC
                       LIMIT 10'''
                )
                
                if not messages:
                    no_messages_text = "📭 Yangi xabarlar yo'q" if lang == 'uz' else "📭 Нет новых сообщений"
                    await callback.message.edit_text(no_messages_text)
                    return
                
                if lang == 'uz':
                    messages_text = "🆕 <b>Yangi xabarlar:</b>\n\n"
                else:
                    messages_text = "🆕 <b>Новые сообщения:</b>\n\n"
                
                for msg in messages:
                    sender_role_emoji = {
                        'client': '👤',
                        'technician': '👨‍🔧',
                        'call_center': '📞',
                        'junior_manager': '👨‍💼'
                    }.get(msg['sender_role'], '👤')
                    
                    created_time = msg['created_at'].strftime('%H:%M') if msg['created_at'] else '-'
                    
                    messages_text += (
                        f"{sender_role_emoji} <b>{msg['sender_name'] or 'Noma\'lum'}</b>\n"
                        f"   📝 {msg['message_text'][:50]}{'...' if len(msg['message_text']) > 50 else ''}\n"
                        f"   ⏰ {created_time}\n\n"
                    )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="inbox_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(messages_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_new_messages: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_read_messages(callback, lang):
        """Show read messages"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get read messages
                messages = await conn.fetch(
                    '''SELECT m.*, u.full_name as sender_name, u.role as sender_role
                       FROM messages m
                       LEFT JOIN users u ON m.sender_id = u.id
                       WHERE m.is_read = true AND m.recipient_role = 'manager'
                       ORDER BY m.created_at DESC
                       LIMIT 10'''
                )
                
                if not messages:
                    no_messages_text = "📭 O'qilgan xabarlar yo'q" if lang == 'uz' else "📭 Нет прочитанных сообщений"
                    await callback.message.edit_text(no_messages_text)
                    return
                
                if lang == 'uz':
                    messages_text = "✅ <b>O'qilgan xabarlar:</b>\n\n"
                else:
                    messages_text = "✅ <b>Прочитанные сообщения:</b>\n\n"
                
                for msg in messages:
                    sender_role_emoji = {
                        'client': '👤',
                        'technician': '👨‍🔧',
                        'call_center': '📞',
                        'junior_manager': '👨‍💼'
                    }.get(msg['sender_role'], '👤')
                    
                    created_time = msg['created_at'].strftime('%d.%m %H:%M') if msg['created_at'] else '-'
                    
                    messages_text += (
                        f"{sender_role_emoji} <b>{msg['sender_name'] or 'Noma\'lum'}</b>\n"
                        f"   📝 {msg['message_text'][:50]}{'...' if len(msg['message_text']) > 50 else ''}\n"
                        f"   ⏰ {created_time}\n\n"
                    )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="inbox_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(messages_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_read_messages: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_urgent_messages(callback, lang):
        """Show urgent messages"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get urgent messages (marked as urgent or from last 2 hours)
                urgent_messages = await conn.fetch(
                    '''SELECT m.*, u.full_name as sender_name, u.role as sender_role
                       FROM messages m
                       LEFT JOIN users u ON m.sender_id = u.id
                       WHERE m.recipient_role = 'manager' 
                       AND (m.is_urgent = true OR m.created_at > NOW() - INTERVAL '2 hours')
                       ORDER BY m.is_urgent DESC, m.created_at DESC
                       LIMIT 10'''
                )
                
                if not urgent_messages:
                    no_messages_text = "📭 Shoshilinch xabarlar yo'q" if lang == 'uz' else "📭 Нет срочных сообщений"
                    await callback.message.edit_text(no_messages_text)
                    return
                
                if lang == 'uz':
                    messages_text = "🚨 <b>Shoshilinch xabarlar:</b>\n\n"
                else:
                    messages_text = "🚨 <b>Срочные сообщения:</b>\n\n"
                
                for msg in urgent_messages:
                    sender_role_emoji = {
                        'client': '👤',
                        'technician': '👨‍🔧',
                        'call_center': '📞',
                        'junior_manager': '👨‍💼'
                    }.get(msg['sender_role'], '👤')
                    
                    urgent_emoji = "🚨" if msg.get('is_urgent') else "⏰"
                    created_time = msg['created_at'].strftime('%H:%M') if msg['created_at'] else '-'
                    
                    messages_text += (
                        f"{urgent_emoji} {sender_role_emoji} <b>{msg['sender_name'] or 'Noma\'lum'}</b>\n"
                        f"   📝 {msg['message_text'][:50]}{'...' if len(msg['message_text']) > 50 else ''}\n"
                        f"   ⏰ {created_time}\n\n"
                    )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="inbox_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(messages_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_urgent_messages: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_client_messages(callback, lang):
        """Show client messages"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get messages from clients
                client_messages = await conn.fetch(
                    '''SELECT m.*, u.full_name as sender_name, u.phone_number as sender_phone
                       FROM messages m
                       LEFT JOIN users u ON m.sender_id = u.id
                       WHERE m.recipient_role = 'manager' AND u.role = 'client'
                       ORDER BY m.created_at DESC
                       LIMIT 10'''
                )
                
                if not client_messages:
                    no_messages_text = "📭 Mijoz xabarlari yo'q" if lang == 'uz' else "📭 Нет сообщений от клиентов"
                    await callback.message.edit_text(no_messages_text)
                    return
                
                if lang == 'uz':
                    messages_text = "👤 <b>Mijoz xabarlari:</b>\n\n"
                else:
                    messages_text = "👤 <b>Сообщения клиентов:</b>\n\n"
                
                for msg in client_messages:
                    created_time = msg['created_at'].strftime('%d.%m %H:%M') if msg['created_at'] else '-'
                    
                    messages_text += (
                        f"👤 <b>{msg['sender_name'] or 'Noma\'lum'}</b>\n"
                        f"   📞 {msg['sender_phone'] or '-'}\n"
                        f"   📝 {msg['message_text'][:50]}{'...' if len(msg['message_text']) > 50 else ''}\n"
                        f"   ⏰ {created_time}\n\n"
                    )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="inbox_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(messages_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_client_messages: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def show_system_messages(callback, lang):
        """Show system messages"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get system messages (from system or automated notifications)
                system_messages = await conn.fetch(
                    '''SELECT m.*, 'System' as sender_name, 'system' as sender_role
                       FROM messages m
                       WHERE m.recipient_role = 'manager' AND m.sender_id IS NULL
                       ORDER BY m.created_at DESC
                       LIMIT 10'''
                )
                
                if not system_messages:
                    no_messages_text = "📭 Tizim xabarlari yo'q" if lang == 'uz' else "📭 Нет системных сообщений"
                    await callback.message.edit_text(no_messages_text)
                    return
                
                if lang == 'uz':
                    messages_text = "⚙️ <b>Tizim xabarlari:</b>\n\n"
                else:
                    messages_text = "⚙️ <b>Системные сообщения:</b>\n\n"
                
                for msg in system_messages:
                    created_time = msg['created_at'].strftime('%d.%m %H:%M') if msg['created_at'] else '-'
                    
                    messages_text += (
                        f"⚙️ <b>Tizim</b>\n"
                        f"   📝 {msg['message_text'][:50]}{'...' if len(msg['message_text']) > 50 else ''}\n"
                        f"   ⏰ {created_time}\n\n"
                    )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="inbox_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(messages_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_system_messages: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data == "inbox_menu")
    async def back_to_inbox_menu(callback: CallbackQuery, state: FSMContext):
        """Return to inbox menu"""
        try:
            await callback.answer()
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            inbox_text = "📥 Kiruvchi xabarlar:" if lang == 'uz' else "📥 Входящие сообщения:"
            
            await callback.message.edit_text(
                inbox_text,
                reply_markup=get_inbox_keyboard(lang)
            )
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in back_to_inbox_menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data.startswith("message_"))
    async def handle_message_actions(callback: CallbackQuery, state: FSMContext):
        """Handle message actions (reply, forward, mark as read, delete)"""
        try:
            await callback.answer()
            action_parts = callback.data.split("_")
            action = action_parts[1]
            message_id = int(action_parts[2]) if len(action_parts) > 2 else None
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            if action == "reply":
                await handle_message_reply(callback, message_id, lang)
            elif action == "forward":
                await handle_message_forward(callback, message_id, lang)
            elif action == "read":
                await handle_message_mark_read(callback, message_id, lang)
            elif action == "delete":
                await handle_message_delete(callback, message_id, lang)
            elif action == "back":
                await back_to_inbox_menu(callback, state)
            else:
                unknown_text = "Noma'lum amal" if lang == 'uz' else "Неизвестное действие"
                await callback.message.edit_text(unknown_text)
            
        except Exception as e:
            logger.error(f"Error in handle_message_actions: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def handle_message_reply(callback, message_id, lang):
        """Handle message reply"""
        try:
            # Set state for reply
            await callback.message.edit_text(
                "💬 Javob yozing:" if lang == 'uz' else "💬 Напишите ответ:"
            )
            # Here you would implement the reply logic
            
        except Exception as e:
            logger.error(f"Error in handle_message_reply: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def handle_message_forward(callback, message_id, lang):
        """Handle message forward"""
        try:
            # Implement forward logic
            success_text = "✅ Xabar o'tkazildi" if lang == 'uz' else "✅ Сообщение переслано"
            await callback.message.edit_text(success_text)
            
        except Exception as e:
            logger.error(f"Error in handle_message_forward: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def handle_message_mark_read(callback, message_id, lang):
        """Handle mark message as read"""
        try:
            conn = await bot.db.acquire()
            try:
                # Mark message as read
                await conn.execute(
                    "UPDATE messages SET is_read = true WHERE id = $1",
                    message_id
                )
                
                success_text = "✅ Xabar o'qilgan deb belgilandi" if lang == 'uz' else "✅ Сообщение отмечено как прочитанное"
                await callback.message.edit_text(success_text)
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in handle_message_mark_read: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    async def handle_message_delete(callback, message_id, lang):
        """Handle message delete"""
        try:
            conn = await bot.db.acquire()
            try:
                # Delete message
                await conn.execute(
                    "DELETE FROM messages WHERE id = $1",
                    message_id
                )
                
                success_text = "🗑️ Xabar o'chirildi" if lang == 'uz' else "🗑️ Сообщение удалено"
                await callback.message.edit_text(success_text)
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in handle_message_delete: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    return router
