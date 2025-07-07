from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from utils.inline_cleanup import safe_delete_message, answer_and_cleanup
from keyboards.manager_buttons import get_status_keyboard, get_manager_main_keyboard
from states.manager_states import ManagerStates
from database.base_queries import get_user_by_telegram_id, update_zayavka_status
from database.base_queries import get_user_lang, get_zayavka_by_id
from utils.logger import setup_logger

def get_manager_status_management_router():
    logger = setup_logger('bot.manager.status')
    router = Router()

    @router.message(F.text.in_(['🔄 Status o\'zgartirish', '🔄 Изменить статус']))
    async def change_status_menu(message: Message, state: FSMContext):
        await safe_delete_message(message.bot, message.chat.id, message.message_id)
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            lang = user.get('language', 'uz')
            app_id_text = "Ariza raqamini kiriting (masalan, 123 yoki #123):" if lang == 'uz' else "Введите номер заявки (например, 123 или #123):"
            await message.answer(app_id_text, reply_markup=get_manager_main_keyboard(lang))
            await state.set_state(ManagerStates.entering_application_id_for_status)
        except Exception as e:
            logger.error(f"Error in change_status_menu: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.entering_application_id_for_status))
    async def get_application_for_status_change(message: Message, state: FSMContext):
        """Get application ID for status change, show full info in user's language with emoji"""
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

            # Status emojis
            status_emojis = {
                'new': '🆕',
                'confirmed': '✅',
                'in_progress': '⏳',
                'completed': '🏁',
                'cancelled': '❌'
            }

            # Status labels in both languages
            status_labels = {
                'new': {'uz': 'Yangi', 'ru': 'Новая'},
                'confirmed': {'uz': 'Tasdiqlangan', 'ru': 'Подтверждена'},
                'in_progress': {'uz': 'Jarayonda', 'ru': 'В процессе'},
                'completed': {'uz': 'Bajarilgan', 'ru': 'Выполнена'},
                'cancelled': {'uz': 'Bekor qilingan', 'ru': 'Отменена'}
            }

            current_status = application.get('status', 'new')
            status_emoji = status_emojis.get(current_status, '📋')
            status_label = status_labels.get(current_status, {}).get(lang, current_status)

            # Format application info with emojis
            if lang == 'uz':
                app_info = (
                    f"📋 <b>Ariza ma'lumotlari:</b>\n\n"
                    f"🆔 <b>Raqam:</b> #{application['id']}\n"
                    f"👤 <b>Mijoz:</b> {application.get('client_name', 'Noma\'lum')}\n"
                    f"📞 <b>Telefon:</b> {application.get('client_phone', '-')}\n"
                    f"📍 <b>Manzil:</b> {application.get('address', '-')}\n"
                    f"📝 <b>Tavsif:</b> {application.get('description', '-')}\n"
                    f"📊 <b>Joriy status:</b> {status_emoji} {status_label}\n"
                    f"👨‍🔧 <b>Texnik:</b> {application.get('technician_name', 'Tayinlanmagan')}\n"
                    f"🕒 <b>Yaratilgan:</b> {application.get('created_at', '-')}\n\n"
                    f"Yangi statusni tanlang:"
                )
            else:
                app_info = (
                    f"📋 <b>Информация о заявке:</b>\n\n"
                    f"🆔 <b>Номер:</b> #{application['id']}\n"
                    f"👤 <b>Клиент:</b> {application.get('client_name', 'Неизвестно')}\n"
                    f"📞 <b>Телефон:</b> {application.get('client_phone', '-')}\n"
                    f"📍 <b>Адрес:</b> {application.get('address', '-')}\n"
                    f"📝 <b>Описание:</b> {application.get('description', '-')}\n"
                    f"📊 <b>Текущий статус:</b> {status_emoji} {status_label}\n"
                    f"👨‍🔧 <b>Техник:</b> {application.get('technician_name', 'Не назначен')}\n"
                    f"🕒 <b>Создано:</b> {application.get('created_at', '-')}\n\n"
                    f"Выберите новый статус:"
                )

            await state.update_data(application_id=app_id)
            await message.answer(
                app_info,
                reply_markup=get_status_keyboard(lang, current_status),
                parse_mode='HTML'
            )
            await state.set_state(ManagerStates.selecting_new_status)

        except ValueError:
            lang = await get_user_lang(message.from_user.id)
            invalid_text = "❌ Noto'g'ri format. Faqat raqam kiriting." if lang == 'uz' else "❌ Неверный формат. Введите только число."
            await message.answer(invalid_text)
        except Exception as e:
            logger.error(f"Error in get_application_for_status_change: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "❌ Xatolik yuz berdi" if lang == 'uz' else "❌ Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("status_"))
    async def change_application_status(callback: CallbackQuery, state: FSMContext):
        """Change application status with confirmation"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            new_status = callback.data.replace("status_", "")
            data = await state.get_data()
            app_id = data.get('application_id')

            if not app_id:
                await callback.answer("❌ Ariza ID topilmadi", show_alert=True)
                return

            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')

            # Status labels with emojis
            status_labels = {
                'new': {'uz': '🆕 Yangi', 'ru': '🆕 Новая'},
                'confirmed': {'uz': '✅ Tasdiqlangan', 'ru': '✅ Подтверждена'},
                'in_progress': {'uz': '⏳ Jarayonda', 'ru': '⏳ В процессе'},
                'completed': {'uz': '🏁 Bajarilgan', 'ru': '🏁 Выполнена'},
                'cancelled': {'uz': '❌ Bekor qilingan', 'ru': '❌ Отменена'}
            }

            status_label = status_labels.get(new_status, {}).get(lang, new_status)

            # Update status in database
            success = await update_zayavka_status(app_id, new_status, user['id'])

            if success:
                success_text = (
                    f"✅ #{app_id} raqamli arizaning statusi muvaffaqiyatli o'zgartirildi!\n\n"
                    f"📊 Yangi status: {status_label}"
                    if lang == 'uz' else
                    f"✅ Статус заявки #{app_id} успешно изменен!\n\n"
                    f"📊 Новый статус: {status_label}"
                )
                await callback.message.edit_text(success_text, parse_mode='HTML')
                logger.info(f"Manager {user['id']} changed status of application #{app_id} to {new_status}")
            else:
                error_text = (
                    f"❌ #{app_id} raqamli arizaning statusini o'zgartirishda xatolik yuz berdi."
                    if lang == 'uz' else
                    f"❌ Ошибка при изменении статуса заявки #{app_id}."
                )
                await callback.message.edit_text(error_text)

            await state.clear()
            await callback.answer()

        except Exception as e:
            logger.error(f"Error in change_application_status: {str(e)}", exc_info=True)
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    return router
