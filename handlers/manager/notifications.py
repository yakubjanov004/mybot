from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_notifications_keyboard, get_manager_main_keyboard
from states.manager_states import ManagerStates
from database.manager_queries import get_users_by_role
from database.base_queries import get_user_by_telegram_id, get_user_by_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger

def get_manager_notifications_router():
    logger = setup_logger('bot.manager.notifications')
    router = Router()

    @router.message(F.text.in_(['🔔 Bildirishnomalar', '🔔 Уведомления']))
    async def show_notifications_menu(message: Message, state: FSMContext):
        """Show notifications menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            notifications_text = "🔔 Bildirishnomalar:" if lang == 'uz' else "🔔 Уведомления:"
            
            await message.answer(
                notifications_text,
                reply_markup=get_notifications_keyboard(lang)
            )
            
        except Exception as e:
            logger.error(f"Error in show_notifications_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("notification_"))
    async def handle_notification_action(callback: CallbackQuery, state: FSMContext):
        """Handle notification actions"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            action = callback.data.replace("notification_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            if action == "send_all":
                await start_send_notification_all(callback, state, lang)
            elif action == "send_role":
                await start_send_notification_role(callback, state, lang)
            elif action == "send_individual":
                await start_send_notification_individual(callback, state, lang)
            elif action == "history":
                await show_notification_history(callback, lang)
            else:
                unknown_text = "Noma'lum amal" if lang == 'uz' else "Неизвестное действие"
                await callback.message.edit_text(unknown_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in handle_notification_action: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def start_send_notification_all(callback, state, lang):
        """Start sending notification to all users"""
        try:
            message_text = (
                "📢 Barcha foydalanuvchilarga xabar yuborish:\n\n"
                "Xabar matnini kiriting:"
                if lang == 'uz' else
                "📢 Отправка сообщения всем пользователям:\n\n"
                "Введите текст сообщения:"
            )
            
            await callback.message.edit_text(message_text)
            await state.update_data(notification_type="all")
            await state.set_state(ManagerStates.sending_notification_message)
            
        except Exception as e:
            logger.error(f"Error in start_send_notification_all: {str(e)}", exc_info=True)

    async def start_send_notification_role(callback, state, lang):
        """Start sending notification to specific role"""
        try:
            role_buttons = [
                [InlineKeyboardButton(
                    text="👨‍🔧 Texniklar" if lang == 'uz' else "👨‍🔧 Техники",
                    callback_data="select_role_technician"
                )],
                [InlineKeyboardButton(
                    text="👨‍💼 Menejerlar" if lang == 'uz' else "👨‍💼 Менеджеры",
                    callback_data="select_role_manager"
                )],
                [InlineKeyboardButton(
                    text="📞 Call center" if lang == 'uz' else "📞 Call center",
                    callback_data="select_role_call_center"
                )],
                [InlineKeyboardButton(
                    text="📦 Ombor" if lang == 'uz' else "📦 Склад",
                    callback_data="select_role_warehouse"
                )],
                [InlineKeyboardButton(
                    text="👤 Mijozlar" if lang == 'uz' else "👤 Клиенты",
                    callback_data="select_role_client"
                )],
                [InlineKeyboardButton(
                    text="❌ Bekor qilish" if lang == 'uz' else "❌ Отмена",
                    callback_data="cancel_notification"
                )]
            ]
            
            role_text = (
                "👥 Qaysi guruhga xabar yubormoqchisiz?"
                if lang == 'uz' else
                "👥 Какой группе хотите отправить сообщение?"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=role_buttons)
            await callback.message.edit_text(role_text, reply_markup=keyboard)
            await state.update_data(notification_type="role")
            
        except Exception as e:
            logger.error(f"Error in start_send_notification_role: {str(e)}", exc_info=True)

    @router.callback_query(F.data.startswith("select_role_"))
    async def select_notification_role(callback: CallbackQuery, state: FSMContext):
        """Select role for notification"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            role = callback.data.replace("select_role_", "")
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            role_names = {
                'technician': {'uz': 'Texniklar', 'ru': 'Техники'},
                'manager': {'uz': 'Menejerlar', 'ru': 'Менеджеры'},
                'call_center': {'uz': 'Call center', 'ru': 'Call center'},
                'warehouse': {'uz': 'Ombor', 'ru': 'Склад'},
                'client': {'uz': 'Mijozlar', 'ru': 'Клиенты'}
            }
            
            role_name = role_names.get(role, {}).get(lang, role)
            
            message_text = (
                f"📢 {role_name}ga xabar yuborish:\n\n"
                f"Xabar matnini kiriting:"
                if lang == 'uz' else
                f"�� Отправка сообщения группе {role_name}:\n\n"
                f"Введите текст сообщения:"
            )
            
            await callback.message.edit_text(message_text)
            await state.update_data(notification_type="role", selected_role=role)
            await state.set_state(ManagerStates.sending_notification_message)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in select_notification_role: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    async def start_send_notification_individual(callback, state, lang):
        """Start sending notification to individual user"""
        try:
            message_text = (
                "👤 Shaxsiy xabar yuborish:\n\n"
                "Foydalanuvchi ID raqamini kiriting:"
                if lang == 'uz' else
                "👤 Отправка личного сообщения:\n\n"
                "Введите ID пользователя:"
            )
            
            await callback.message.edit_text(message_text)
            await state.update_data(notification_type="individual")
            await state.set_state(ManagerStates.sending_notification_user_id)
            
        except Exception as e:
            logger.error(f"Error in start_send_notification_individual: {str(e)}", exc_info=True)

    @router.message(StateFilter(ManagerStates.sending_notification_user_id))
    async def get_notification_user_id(message: Message, state: FSMContext):
        """Get user ID for individual notification"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user_id = int(message.text.strip())
            
            # Check if user exists
            conn = await bot.db.acquire()
            try:
                target_user = await conn.fetchrow(
                    'SELECT * FROM users WHERE id = $1',
                    user_id
                )
                
                if not target_user:
                    user = await get_user_by_telegram_id(message.from_user.id)
                    lang = user.get('language', 'uz')
                    not_found_text = f"❌ ID {user_id} bilan foydalanuvchi topilmadi." if lang == 'uz' else f"❌ Пользователь с ID {user_id} не найден."
                    await message.answer(not_found_text)
                    return
                
                await state.update_data(target_user_id=user_id)
                
                user = await get_user_by_telegram_id(message.from_user.id)
                lang = user.get('language', 'uz')
                
                message_text = (
                    f"👤 {target_user['full_name']}ga xabar yuborish:\n\n"
                    f"Xabar matnini kiriting:"
                    if lang == 'uz' else
                    f"👤 Отправка сообщения пользователю {target_user['full_name']}:\n\n"
                    f"Введите текст сообщения:"
                )
                
                await message.answer(message_text)
                await state.set_state(ManagerStates.sending_notification_message)
                
            finally:
                await conn.release()
            
        except ValueError:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            invalid_text = "❌ Noto'g'ri format. Faqat raqam kiriting." if lang == 'uz' else "❌ Неверный формат. Введите только число."
            await message.answer(invalid_text)
        except Exception as e:
            logger.error(f"Error in get_notification_user_id: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.sending_notification_message))
    async def get_notification_message(message: Message, state: FSMContext):
        """Get notification message and send it"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            notification_text = message.text
            data = await state.get_data()
            notification_type = data.get('notification_type')
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            conn = await bot.db.acquire()
            try:
                sent_count = 0
                failed_count = 0
                
                if notification_type == "all":
                    # Send to all users with telegram_id
                    users = await conn.fetch(
                        'SELECT telegram_id FROM users WHERE telegram_id IS NOT NULL'
                    )
                    
                    for target_user in users:
                        try:
                            await message.bot.send_message(
                                chat_id=target_user['telegram_id'],
                                text=f"📢 <b>Umumiy xabar:</b>\n\n{notification_text}" if lang == 'uz' else f"📢 <b>Общее сообщение:</b>\n\n{notification_text}",
                                parse_mode='HTML'
                            )
                            sent_count += 1
                        except Exception as e:
                            logger.error(f"Failed to send notification to {target_user['telegram_id']}: {str(e)}")
                            failed_count += 1
                            
                elif notification_type == "role":
                    selected_role = data.get('selected_role')
                    users = await conn.fetch(
                        'SELECT telegram_id FROM users WHERE role = $1 AND telegram_id IS NOT NULL',
                        selected_role
                    )
                    
                    for target_user in users:
                        try:
                            await message.bot.send_message(
                                chat_id=target_user['telegram_id'],
                                text=f"📢 <b>Guruh xabari:</b>\n\n{notification_text}" if lang == 'uz' else f"📢 <b>Групповое сообщение:</b>\n\n{notification_text}",
                                parse_mode='HTML'
                            )
                            sent_count += 1
                        except Exception as e:
                            logger.error(f"Failed to send notification to {target_user['telegram_id']}: {str(e)}")
                            failed_count += 1
                            
                elif notification_type == "individual":
                    target_user_id = data.get('target_user_id')
                    target_user = await conn.fetchrow(
                        'SELECT telegram_id FROM users WHERE id = $1',
                        target_user_id
                    )
                    
                    if target_user and target_user['telegram_id']:
                        try:
                            await message.bot.send_message(
                                chat_id=target_user['telegram_id'],
                                text=f"📢 <b>Shaxsiy xabar:</b>\n\n{notification_text}" if lang == 'uz' else f"📢 <b>Личное сообщение:</b>\n\n{notification_text}",
                                parse_mode='HTML'
                            )
                            sent_count = 1
                        except Exception as e:
                            logger.error(f"Failed to send notification to {target_user['telegram_id']}: {str(e)}")
                            failed_count = 1
                    else:
                        failed_count = 1
                
                # Save notification to history
                await conn.execute(
                    '''INSERT INTO notifications (sender_id, message_text, notification_type, sent_count, failed_count, created_at)
                       VALUES ($1, $2, $3, $4, $5, NOW())''',
                    user['id'], notification_text, notification_type, sent_count, failed_count
                )
                
                # Send confirmation
                if lang == 'uz':
                    result_text = (
                        f"✅ <b>Xabar yuborildi!</b>\n\n"
                        f"📤 Yuborilgan: {sent_count}\n"
                        f"❌ Xatolik: {failed_count}\n\n"
                        f"📝 Xabar matni:\n{notification_text}"
                    )
                else:
                    result_text = (
                        f"✅ <b>Сообщение отправлено!</b>\n\n"
                        f"📤 Отправлено: {sent_count}\n"
                        f"❌ Ошибок: {failed_count}\n\n"
                        f"📝 Текст сообщения:\n{notification_text}"
                    )
                
                await message.answer(result_text, parse_mode='HTML')
                logger.info(f"Manager {user['id']} sent notification to {sent_count} users")
                
            finally:
                await conn.release()
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in get_notification_message: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def show_notification_history(callback, lang):
        """Show notification history"""
        try:
            conn = await bot.db.acquire()
            try:
                # Get recent notifications
                notifications = await conn.fetch(
                    '''SELECT n.*, u.full_name as sender_name
                       FROM notifications n
                       LEFT JOIN users u ON n.sender_id = u.id
                       ORDER BY n.created_at DESC
                       LIMIT 10'''
                )
                
                if not notifications:
                    no_history_text = "❌ Bildirishnomalar tarixi bo'sh." if lang == 'uz' else "❌ История уведомлений пуста."
                    await callback.message.edit_text(no_history_text)
                    return
                
                if lang == 'uz':
                    history_text = "📋 <b>Bildirishnomalar tarixi:</b>\n\n"
                    
                    for notif in notifications:
                        type_emoji = {
                            'all': '📢',
                            'role': '👥',
                            'individual': '👤'
                        }.get(notif['notification_type'], '📢')
                        
                        history_text += (
                            f"{type_emoji} <b>{notif.get('sender_name', 'Noma\'lum')}</b>\n"
                            f"   📅 {notif['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                            f"   📤 Yuborilgan: {notif['sent_count']}\n"
                            f"   ❌ Xatolik: {notif['failed_count']}\n"
                            f"   📝 {notif['message_text'][:50]}...\n\n"
                        )
                else:
                    history_text = "📋 <b>История уведомлений:</b>\n\n"
                    
                    for notif in notifications:
                        type_emoji = {
                            'all': '📢',
                            'role': '👥',
                            'individual': '👤'
                        }.get(notif['notification_type'], '📢')
                        
                        history_text += (
                            f"{type_emoji} <b>{notif.get('sender_name', 'Неизвестно')}</b>\n"
                            f"   📅 {notif['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                            f"   📤 Отправлено: {notif['sent_count']}\n"
                            f"   ❌ Ошибок: {notif['failed_count']}\n"
                            f"   📝 {notif['message_text'][:50]}...\n\n"
                        )
                
                # Add back button
                back_button = InlineKeyboardButton(
                    text="🔙 Orqaga" if lang == 'uz' else "🔙 Назад",
                    callback_data="notification_menu"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
                
                await callback.message.edit_text(history_text, reply_markup=keyboard, parse_mode='HTML')
                
            finally:
                await conn.release()
                
        except Exception as e:
            logger.error(f"Error in show_notification_history: {str(e)}", exc_info=True)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data == "cancel_notification")
    async def cancel_notification(callback: CallbackQuery, state: FSMContext):
        """Cancel notification sending"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            cancel_text = "❌ Xabar yuborish bekor qilindi." if lang == 'uz' else "❌ Отправка сообщения отменена."
            await callback.message.edit_text(cancel_text)
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in cancel_notification: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data == "notification_menu")
    async def back_to_notification_menu(callback: CallbackQuery, state: FSMContext):
        """Return to notifications menu"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            notifications_text = "🔔 Bildirishnomalar:" if lang == 'uz' else "🔔 Уведомления:"
            
            await callback.message.edit_text(
                notifications_text,
                reply_markup=get_notifications_keyboard(lang)
            )
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in back_to_notification_menu: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi", show_alert=True)

    return router
