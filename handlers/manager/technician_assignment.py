from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import get_manager_main_keyboard
from states.manager_states import ManagerStates
from database.base_queries import assign_technician, get_technicians
from loader import bot
from database.base_queries import get_user_by_telegram_id, get_zayavka_by_id
from database.base_queries import get_user_lang
from utils.logger import setup_logger
from database.technician_queries import assign_technician_to_zayavka, get_available_technicians
from utils.role_router import get_role_router

def get_manager_technician_assignment_router():
    logger = setup_logger('bot.manager.assignment')
    router = get_role_router("manager")

    @router.message(F.text.in_(['👨‍🔧 Texnik tayinlash', '👨‍🔧 Назначить техника']))
    async def assign_technician_menu(message: Message, state: FSMContext):
        """Start technician assignment process"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            app_id_text = "Ariza raqamini kiriting (masalan, 123 yoki #123):" if lang == 'uz' else "Введите номер заявки (например, 123 или #123):"
            
            await message.answer(app_id_text, reply_markup=get_manager_main_keyboard(lang))
            await state.set_state(ManagerStates.entering_application_id_for_assignment)
            
        except Exception as e:
            logger.error(f"Error in assign_technician_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.entering_application_id_for_assignment))
    async def get_application_for_assignment(message: Message, state: FSMContext):
        """Get application ID and show technician list"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            app_id = int(message.text.strip().replace('#', ''))
            application = await get_zayavka_by_id(app_id)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            if not application:
                not_found_text = f"❌ #{app_id} raqamli ariza topilmadi." if lang == 'uz' else f"❌ Заявка #{app_id} не найдена."
                await message.answer(not_found_text)
                return
            
            # Get available technicians
            technicians = await get_technicians()
            
            if not technicians:
                no_techs_text = "❌ Hozirda mavjud texniklar yo'q." if lang == 'uz' else "❌ В данный момент нет доступных техников."
                await message.answer(no_techs_text)
                return
            
            # Show application info
            status_emojis = {
                'new': '🆕',
                'confirmed': '✅',
                'in_progress': '⏳',
                'completed': '🏁',
                'cancelled': '❌'
            }
            
            current_status = application.get('status', 'new')
            status_emoji = status_emojis.get(current_status, '📋')
            
            if lang == 'uz':
                app_info = (
                    f"📋 <b>Ariza ma'lumotlari:</b>\n\n"
                    f"🆔 <b>Raqam:</b> #{application['id']}\n"
                    f"👤 <b>Mijoz:</b> {application.get('client_name', 'Noma\'lum')}\n"
                    f"📞 <b>Telefon:</b> {application.get('client_phone', '-')}\n"
                    f"📍 <b>Manzil:</b> {application.get('address', '-')}\n"
                    f"📝 <b>Tavsif:</b> {application.get('description', '-')}\n"
                    f"📊 <b>Status:</b> {status_emoji} {current_status}\n"
                    f"👨‍🔧 <b>Joriy texnik:</b> {application.get('technician_name', 'Tayinlanmagan')}\n\n"
                    f"Texnikni tanlang:"
                )
            else:
                app_info = (
                    f"📋 <b>Информация о заявке:</b>\n\n"
                    f"🆔 <b>Номер:</b> #{application['id']}\n"
                    f"👤 <b>Клиент:</b> {application.get('client_name', 'Неизвестно')}\n"
                    f"📞 <b>Телефон:</b> {application.get('client_phone', '-')}\n"
                    f"📍 <b>Адрес:</b> {application.get('address', '-')}\n"
                    f"📝 <b>Описание:</b> {application.get('description', '-')}\n"
                    f"📊 <b>Статус:</b> {status_emoji} {current_status}\n"
                    f"👨‍🔧 <b>Текущий техник:</b> {application.get('technician_name', 'Не назначен')}\n\n"
                    f"Выберите техника:"
                )
            
            # Create technician selection keyboard
            keyboard = []
            for tech in technicians:
                tech_name = tech.get('full_name', f"ID: {tech['id']}")
                tech_phone = tech.get('phone_number', '')
                button_text = f"👨‍🔧 {tech_name}"
                if tech_phone:
                    button_text += f" ({tech_phone})"
                
                keyboard.append([InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"assign_tech_{tech['id']}"
                )])
            
            # Add cancel button
            cancel_text = "❌ Bekor qilish" if lang == 'uz' else "❌ Отмена"
            keyboard.append([InlineKeyboardButton(
                text=cancel_text,
                callback_data="cancel_assignment"
            )])
            
            await state.update_data(application_id=app_id)
            await message.answer(
                app_info,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
                parse_mode='HTML'
            )
            await state.set_state(ManagerStates.selecting_technician)
            
        except ValueError:
            lang = await get_user_lang(message.from_user.id)
            invalid_text = "❌ Noto'g'ri format. Faqat raqam kiriting." if lang == 'uz' else "❌ Неверный формат. Введите только число."
            await message.answer(invalid_text)
        except Exception as e:
            logger.error(f"Error in get_application_for_assignment: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "❌ Xatolik yuz berdi" if lang == 'uz' else "❌ Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("assign_tech_"))
    async def assign_technician_to_application(callback: CallbackQuery, state: FSMContext):
        """Assign selected technician to application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            tech_id = int(callback.data.replace("assign_tech_", ""))
            data = await state.get_data()
            app_id = data.get('application_id')
            
            if not app_id:
                await callback.answer("❌ Ariza ID topilmadi", show_alert=True)
                return
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Get technician info
            conn = await bot.db.acquire()
            try:
                technician = await conn.fetchrow(
                    'SELECT * FROM users WHERE id = $1 AND role = $2',
                    tech_id, 'technician'
                )
                
                if not technician:
                    not_found_text = "❌ Texnik topilmadi." if lang == 'uz' else "❌ Техник не найден."
                    await callback.answer(not_found_text, show_alert=True)
                    return
                
                # Assign technician
                success = await assign_technician_to_zayavka(app_id, tech_id, user['id'])
                
                if success:
                    tech_name = technician.get('full_name', f"ID: {tech_id}")
                    tech_phone = technician.get('phone_number', '')
                    
                    success_text = (
                        f"✅ #{app_id} raqamli ariza muvaffaqiyatli tayinlandi!\n\n"
                        f"👨‍🔧 <b>Texnik:</b> {tech_name}\n"
                        f"📞 <b>Telefon:</b> {tech_phone}\n\n"
                        f"Texnikka bildirishnoma yuborildi."
                        if lang == 'uz' else
                        f"✅ Заявка #{app_id} успешно назначена!\n\n"
                        f"👨‍🔧 <b>Техник:</b> {tech_name}\n"
                        f"📞 <b>Телефон:</b> {tech_phone}\n\n"
                        f"Уведомление отправлено технику."
                    )
                    
                    await callback.message.edit_text(success_text, parse_mode='HTML')
                    logger.info(f"Manager {user['id']} assigned technician {tech_id} to application #{app_id}")
                    
                    # Send notification to technician (if they have telegram_id)
                    if technician.get('telegram_id'):
                        try:
                            app = await get_zayavka_by_id(app_id)
                            if app:
                                notification_text = (
                                    f"🔔 <b>Yangi ariza tayinlandi!</b>\n\n"
                                    f"📋 <b>Ariza:</b> #{app_id}\n"
                                    f"👤 <b>Mijoz:</b> {app.get('client_name', 'Noma\'lum')}\n"
                                    f"📞 <b>Telefon:</b> {app.get('client_phone', '-')}\n"
                                    f"📍 <b>Manzil:</b> {app.get('address', '-')}\n"
                                    f"📝 <b>Tavsif:</b> {app.get('description', '-')}"
                                    if lang == 'uz' else
                                    f"🔔 <b>Назначена новая заявка!</b>\n\n"
                                    f"📋 <b>Заявка:</b> #{app_id}\n"
                                    f"👤 <b>Клиент:</b> {app.get('client_name', 'Неизвестно')}\n"
                                    f"📞 <b>Телефон:</b> {app.get('client_phone', '-')}\n"
                                    f"📍 <b>Адрес:</b> {app.get('address', '-')}\n"
                                    f"📝 <b>Описание:</b> {app.get('description', '-')}"
                                )
                                
                                await callback.bot.send_message(
                                    chat_id=technician['telegram_id'],
                                    text=notification_text,
                                    parse_mode='HTML'
                                )
                        except Exception as e:
                            logger.error(f"Error sending notification to technician: {str(e)}")
                    
                else:
                    error_text = (
                        f"❌ #{app_id} raqamli arizani tayinlashda xatolik yuz berdi."
                        if lang == 'uz' else
                        f"❌ Ошибка при назначении заявки #{app_id}."
                    )
                    await callback.message.edit_text(error_text)
                
            finally:
                await conn.release()
            
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in assign_technician_to_application: {str(e)}", exc_info=True)
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    @router.callback_query(F.data == "cancel_assignment")
    async def cancel_technician_assignment(callback: CallbackQuery, state: FSMContext):
        """Cancel technician assignment"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            cancel_text = "❌ Texnik tayinlash bekor qilindi." if lang == 'uz' else "❌ Назначение техника отменено."
            await callback.message.edit_text(cancel_text)
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in cancel_technician_assignment: {str(e)}", exc_info=True)
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    return router
