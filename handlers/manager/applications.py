from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import (
    zayavka_type_keyboard, media_attachment_keyboard, geolocation_keyboard,
    confirmation_keyboard, get_manager_main_keyboard
)
from database.base_queries import get_user_by_telegram_id
from states.manager_states import ManagerStates
from database.base_queries import get_user_lang, create_zayavka
from utils.logger import setup_logger
from utils.role_router import get_role_router

def get_manager_applications_router():
    logger = setup_logger('bot.manager.applications')
    router = get_role_router("manager")

    @router.message(F.text.in_(["📝 Ariza yaratish", "📝 Создать заявку"]))
    async def create_application(message: Message, state: FSMContext):
        """Start creating new application"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            
            lang = user.get('language', 'uz')
            order_type_text = "Ariza turini tanlang:" if lang == 'uz' else "Выберите тип заявки:"
            
            await message.answer(
                order_type_text,
                reply_markup=zayavka_type_keyboard(lang)
            )
            await state.set_state(ManagerStates.creating_application_type)
            
        except Exception as e:
            logger.error(f"Error in create_application: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("manager_zayavka_type_"))
    async def select_application_type(callback: CallbackQuery, state: FSMContext):
        """Select application type"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            app_type = callback.data.split("_")[3]  # b2b or b2c
            await state.update_data(application_type=app_type)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            description_text = "Ariza tavsifini kiriting:" if lang == 'uz' else "Введите описание заявки:"
            await callback.message.edit_text(description_text)
            await state.set_state(ManagerStates.creating_application_description)
            
        except Exception as e:
            logger.error(f"Error in select_application_type: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(ManagerStates.creating_application_description))
    async def get_application_description(message: Message, state: FSMContext):
        """Get application description"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(description=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            address_text = "Manzilni kiriting:" if lang == 'uz' else "Введите адрес:"
            await message.answer(address_text)
            await state.set_state(ManagerStates.creating_application_address)
            
        except Exception as e:
            logger.error(f"Error in get_application_description: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.creating_application_address))
    async def get_application_address(message: Message, state: FSMContext):
        """Get application address"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(address=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            client_name_text = "Mijoz ismini kiriting:" if lang == 'uz' else "Введите имя клиента:"
            await message.answer(client_name_text)
            await state.set_state(ManagerStates.creating_application_client_name)
            
        except Exception as e:
            logger.error(f"Error in get_application_address: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.creating_application_client_name))
    async def get_application_client_name(message: Message, state: FSMContext):
        """Get application client name"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(client_name=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            phone_text = "Mijoz telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона клиента:"
            await message.answer(phone_text)
            await state.set_state(ManagerStates.creating_application_phone)
            
        except Exception as e:
            logger.error(f"Error in get_application_client_name: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(ManagerStates.creating_application_phone))
    async def get_application_phone(message: Message, state: FSMContext):
        """Get application phone"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            await state.update_data(client_phone=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            media_question_text = "Rasm yoki video biriktirmoqchimisiz?" if lang == 'uz' else "Хотите прикрепить фото или видео?"
            await message.answer(
                media_question_text,
                reply_markup=media_attachment_keyboard(lang)
            )
            await state.set_state(ManagerStates.creating_application_media)
            
        except Exception as e:
            logger.error(f"Error in get_application_phone: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "manager_attach_media_yes")
    async def request_application_media(callback: CallbackQuery, state: FSMContext):
        """Request media for application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            media_request_text = "Rasm yoki videoni yuboring:" if lang == 'uz' else "Отправьте фото или видео:"
            await callback.message.edit_text(media_request_text)
            await state.set_state(ManagerStates.creating_application_waiting_media)
            
        except Exception as e:
            logger.error(f"Error in request_application_media: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "manager_attach_media_no")
    async def skip_application_media(callback: CallbackQuery, state: FSMContext):
        """Skip media for application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            await ask_for_application_location(callback, state)
        except Exception as e:
            logger.error(f"Error in skip_application_media: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(ManagerStates.creating_application_waiting_media), F.photo | F.video)
    async def process_application_media(message: Message, state: FSMContext):
        """Process application media"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            if message.photo:
                media_id = message.photo[-1].file_id
                media_type = 'photo'
            elif message.video:
                media_id = message.video.file_id
                media_type = 'video'
            else:
                return
            
            await state.update_data(media_id=media_id, media_type=media_type)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            location_question_text = "Geolokatsiya yubormoqchimisiz?" if lang == 'uz' else "Хотите отправить геолокацию?"
            await message.answer(
                location_question_text,
                reply_markup=geolocation_keyboard(lang)
            )
            await state.set_state(ManagerStates.creating_application_location)
            
        except Exception as e:
            logger.error(f"Error in process_application_media: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def ask_for_application_location(callback_or_message, state: FSMContext):
        """Ask for application location"""
        try:
            user_id = callback_or_message.from_user.id
            user = await get_user_by_telegram_id(user_id)
            lang = user.get('language', 'uz')
            
            location_question_text = "Geolokatsiya yubormoqchimisiz?" if lang == 'uz' else "Хотите отправить геолокацию?"
            
            if hasattr(callback_or_message, 'message'):
                await callback_or_message.message.edit_text(
                    location_question_text,
                    reply_markup=geolocation_keyboard(lang)
                )
                await callback_or_message.answer()
            else:
                await callback_or_message.answer(
                    location_question_text,
                    reply_markup=geolocation_keyboard(lang)
                )
            
            await state.set_state(ManagerStates.creating_application_location)
            
        except Exception as e:
            logger.error(f"Error in ask_for_application_location: {str(e)}", exc_info=True)

    @router.callback_query(F.data == "manager_send_location_yes")
    async def request_application_location(callback: CallbackQuery, state: FSMContext):
        """Request location for application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            location_request_text = "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:"
            await callback.message.edit_text(location_request_text)
            await state.set_state(ManagerStates.creating_application_waiting_location)
            
        except Exception as e:
            logger.error(f"Error in request_application_location: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "manager_send_location_no")
    async def skip_application_location(callback: CallbackQuery, state: FSMContext):
        """Skip location for application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            await show_application_confirmation(callback, state)
        except Exception as e:
            logger.error(f"Error in skip_application_location: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(ManagerStates.creating_application_waiting_location), F.location)
    async def process_application_location(message: Message, state: FSMContext):
        """Process application location"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            location = message.location
            await state.update_data(
                latitude=location.latitude,
                longitude=location.longitude
            )
            
            await show_application_confirmation(message, state)
            
        except Exception as e:
            logger.error(f"Error in process_application_location: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def show_application_confirmation(message_or_callback, state: FSMContext):
        """Show application confirmation"""
        try:
            user_id = message_or_callback.from_user.id
            user = await get_user_by_telegram_id(user_id)
            lang = user.get('language', 'uz')
            
            data = await state.get_data()
            
            app_type_text = "Jismoniy shaxs" if data['application_type'] == 'b2c' else "Yuridik shaxs"
            if lang == 'ru':
                app_type_text = "Физическое лицо" if data['application_type'] == 'b2c' else "Юридическое лицо"
            
            summary_text = (
                f"📋 Ariza xulosasi:\n\n"
                f"👤 Tur: {app_type_text}\n"
                f"📝 Tavsif: {data['description']}\n"
                f"📍 Manzil: {data['address']}\n"
                f"👤 Mijoz: {data['client_name']}\n"
                f"📞 Telefon: {data['client_phone']}\n"
                if lang == 'uz' else
                f"📋 Сводка заявки:\n\n"
                f"👤 Тип: {app_type_text}\n"
                f"📝 Описание: {data['description']}\n"
                f"📍 Адрес: {data['address']}\n"
                f"👤 Клиент: {data['client_name']}\n"
                f"📞 Телефон: {data['client_phone']}\n"
            )
            
            if data.get('media_id'):
                media_text = "✅ Rasm/video biriktirilgan" if lang == 'uz' else "✅ Фото/видео прикреплено"
                summary_text += f"{media_text}\n"
            
            if data.get('latitude'):
                location_text = "✅ Geolokatsiya biriktirilgan" if lang == 'uz' else "✅ Геолокация прикреплена"
                summary_text += f"{location_text}\n"
            
            confirm_text = "\nTasdiqlaysizmi?" if lang == 'uz' else "\nПодтверждаете?"
            summary_text += confirm_text
            
            if hasattr(message_or_callback, 'message'):
                await message_or_callback.message.edit_text(
                    summary_text,
                    reply_markup=confirmation_keyboard(lang)
                )
                await message_or_callback.answer()
            else:
                await message_or_callback.answer(
                    summary_text,
                    reply_markup=confirmation_keyboard(lang)
                )
            
            await state.set_state(ManagerStates.confirming_application)
            
        except Exception as e:
            logger.error(f"Error in show_application_confirmation: {str(e)}", exc_info=True)

    @router.callback_query(F.data == "manager_confirm_zayavka")
    async def confirm_application(callback: CallbackQuery, state: FSMContext):
        """Confirm and create application"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            data = await state.get_data()
            
            # Create application
            app_data = {
                'manager_id': user['id'],
                'zayavka_type': data['application_type'],
                'description': data['description'],
                'address': data['address'],
                'client_name': data['client_name'],
                'client_phone': data['client_phone'],
                'media': data.get('media_id'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'status': 'new',
                'created_by': user['id'],
                'created_by_role': 'manager',
                'phone_number': data['client_phone']
            }
            
            app_id = await create_zayavka(app_data)
            
            if app_id:
                success_text = (
                    f"✅ Ariza muvaffaqiyatli yaratildi!\n"
                    f"Ariza raqami: #{app_id}\n\n"
                    f"Ariza tizimga kiritildi va texniklarga yuboriladi."
                    if lang == 'uz' else
                    f"✅ Заявка успешно создана!\n"
                    f"Номер заявки: #{app_id}\n\n"
                    f"Заявка внесена в систему и отправлена техникам."
                )
                
                await callback.message.edit_text(success_text)
                logger.info(f"Application #{app_id} created by manager {user['id']}")
            else:
                error_text = "Ariza yaratishda xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка при создании заявки."
                await callback.message.edit_text(error_text)
            
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in confirm_application: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "manager_resend_zayavka")
    async def resend_application(callback: CallbackQuery, state: FSMContext):
        """Resend application (restart process)"""
        try:
            await state.clear()
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            order_type_text = "Ariza turini tanlang:" if lang == 'uz' else "Выберите тип заявки:"
            await callback.message.edit_text(
                order_type_text,
                reply_markup=zayavka_type_keyboard(lang)
            )
            await state.set_state(ManagerStates.creating_application_type)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in resend_application: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(F.text.in_(["📋 Arizalarni ko'rish", "📋 Просмотр заявок"]))
    async def view_applications(message: Message, state: FSMContext):
        """Manager: View all applications with pagination and full info"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user or user['role'] != 'manager':
                return
            lang = user.get('language', 'uz')
            page = 1
            per_page = 5
            await state.update_data(manager_apps_page=page)
            conn = await bot.db.acquire()
            try:
                total = await conn.fetchval('SELECT COUNT(*) FROM zayavki')
                if not total or total == 0:
                    no_apps_text = "❗️ Hozircha arizalar yo'q." if lang == 'uz' else "❗️ Пока нет заявок."
                    await message.answer(no_apps_text)
                    return
                offset = (page - 1) * per_page
                apps = await conn.fetch(
                    '''SELECT z.*, u.full_name as client_name, u.phone_number as client_phone, t.full_name as technician_name
                       FROM zayavki z
                       LEFT JOIN users u ON z.user_id = u.id
                       LEFT JOIN users t ON z.assigned_to = t.id
                       ORDER BY z.created_at DESC
                       LIMIT $1 OFFSET $2''',
                    per_page, offset
                )
                for app in apps:
                    status_emoji = {
                        'new': '🆕',
                        'confirmed': '✅',
                        'in_progress': '⏳',
                        'completed': '🏁',
                        'cancelled': '❌'
                    }.get(app['status'], '📋')
                    if lang == 'uz':
                        status_text = {
                            'new': '🆕 Yangi',
                            'confirmed': '✅ Tasdiqlangan',
                            'in_progress': '⏳ Jarayonda',
                            'completed': '🏁 Bajarilgan',
                            'cancelled': '❌ Bekor qilingan'
                        }.get(app['status'], app['status'])
                        tech = app.get('technician_name') or "🧑‍🔧 Tayinlanmagan"
                        info = (
                            f"📄 <b>Zayavka raqami:</b> #{app['id']} {status_emoji}\n"
                            f"👤 <b>Mijoz:</b> {app.get('client_name') or 'Noma\'lum'}\n"
                            f"📞 <b>Telefon:</b> {app.get('client_phone') or '-'}\n"
                            f"📍 <b>Manzil:</b> {app.get('address') or '-'}\n"
                            f"📝 <b>Tavsif:</b> {app.get('description') or '-'}\n"
                            f"📊 <b>Status:</b> {status_text}\n"
                            f"🧑‍🔧 <b>Texnik:</b> {tech}\n"
                            f"🕒 <b>Yaratilgan:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                            f"📅 <b>Biriktirilgan:</b> {app.get('assigned_at').strftime('%d.%m.%Y %H:%M') if app.get('assigned_at') else '-'}\n"
                            f"✅ <b>Yakunlangan:</b> {app.get('completed_at').strftime('%d.%m.%Y %H:%M') if app.get('completed_at') else '-'}\n"
                        )
                    else:
                        status_text = {
                            'new': '🆕 Новая',
                            'confirmed': '✅ Подтверждена',
                            'in_progress': '⏳ В процессе',
                            'completed': '🏁 Выполнена',
                            'cancelled': '❌ Отменена'
                        }.get(app['status'], app['status'])
                        tech = app.get('technician_name') or "🧑‍🔧 Не назначен"
                        info = (
                            f"📄 <b>Номер заявки:</b> #{app['id']} {status_emoji}\n"
                            f"👤 <b>Клиент:</b> {app.get('client_name') or 'Неизвестно'}\n"
                            f"📞 <b>Телефон:</b> {app.get('client_phone') or '-'}\n"
                            f"📍 <b>Адрес:</b> {app.get('address') or '-'}\n"
                            f"📝 <b>Описание:</b> {app.get('description') or '-'}\n"
                            f"📊 <b>Статус:</b> {status_text}\n"
                            f"🧑‍🔧 <b>Техник:</b> {tech}\n"
                            f"🕒 <b>Создано:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                            f"📅 <b>Назначено:</b> {app.get('assigned_at').strftime('%d.%m.%Y %H:%M') if app.get('assigned_at') else '-'}\n"
                            f"✅ <b>Завершено:</b> {app.get('completed_at').strftime('%d.%m.%Y %H:%M') if app.get('completed_at') else '-'}\n"
                        )
                    if app.get('media'):
                        await message.answer_photo(photo=app['media'], caption=info, parse_mode='HTML')
                    else:
                        await message.answer(info, parse_mode='HTML')
                # Pagination buttons
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ Oldingi" if lang == 'uz' else "◀️ Предыдущая",
                        callback_data=f"manager_apps_page_{page-1}"
                    ))
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text="Keyingi ➡️" if lang == 'uz' else "Следующая ▶️",
                        callback_data=f"manager_apps_page_{page+1}"
                    ))
                if buttons:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                    page_text = f"📄 {page*per_page if page*per_page <= total else total}/{total}"
                    await message.answer(page_text, reply_markup=keyboard)
            finally:
                await conn.release()
        except Exception as e:
            logger.error(f"Error in view_applications: {str(e)}", exc_info=True)
            error_text = "❗️ Xatolik yuz berdi" if lang == 'uz' else "❗️ Произошла ошибка"
            await message.answer(error_text)

    # Pagination callback for manager applications
    @router.callback_query(lambda c: c.data.startswith('manager_apps_page_'))
    async def manager_apps_page_callback(callback: CallbackQuery, state: FSMContext):
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            page = int(callback.data.split('_')[-1])
            per_page = 5
            await state.update_data(manager_apps_page=page)
            conn = await bot.db.acquire()
            try:
                total = await conn.fetchval('SELECT COUNT(*) FROM zayavki')
                if not total or total == 0:
                    no_apps_text = "❗️ Hozircha arizalar yo'q." if lang == 'uz' else "❗️ Пока нет заявок."
                    await callback.message.edit_text(no_apps_text)
                    await callback.answer()
                    return
                offset = (page - 1) * per_page
                apps = await conn.fetch(
                    '''SELECT z.*, u.full_name as client_name, u.phone_number as client_phone, t.full_name as technician_name
                       FROM zayavki z
                       LEFT JOIN users u ON z.user_id = u.id
                       LEFT JOIN users t ON z.assigned_to = t.id
                       ORDER BY z.created_at DESC
                       LIMIT $1 OFFSET $2''',
                    per_page, offset
                )
                await callback.message.delete()
                for app in apps:
                    status_emoji = {
                        'new': '🆕',
                        'confirmed': '✅',
                        'in_progress': '⏳',
                        'completed': '🏁',
                        'cancelled': '❌'
                    }.get(app['status'], '📋')
                    if lang == 'uz':
                        status_text = {
                            'new': '🆕 Yangi',
                            'confirmed': '✅ Tasdiqlangan',
                            'in_progress': '⏳ Jarayonda',
                            'completed': '🏁 Bajarilgan',
                            'cancelled': '❌ Bekor qilingan'
                        }.get(app['status'], app['status'])
                        tech = app.get('technician_name') or "🧑‍🔧 Tayinlanmagan"
                        info = (
                            f"📄 <b>Zayavka raqami:</b> #{app['id']} {status_emoji}\n"
                            f"👤 <b>Mijoz:</b> {app.get('client_name') or 'Noma\'lum'}\n"
                            f"📞 <b>Telefon:</b> {app.get('client_phone') or '-'}\n"
                            f"📍 <b>Manzil:</b> {app.get('address') or '-'}\n"
                            f"📝 <b>Tavsif:</b> {app.get('description') or '-'}\n"
                            f"📊 <b>Status:</b> {status_text}\n"
                            f"🧑‍🔧 <b>Texnik:</b> {tech}\n"
                            f"🕒 <b>Yaratilgan:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                            f"📅 <b>Biriktirilgan:</b> {app.get('assigned_at').strftime('%d.%m.%Y %H:%M') if app.get('assigned_at') else '-'}\n"
                            f"✅ <b>Yakunlangan:</b> {app.get('completed_at').strftime('%d.%m.%Y %H:%M') if app.get('completed_at') else '-'}\n"
                        )
                    else:
                        status_text = {
                            'new': '🆕 Новая',
                            'confirmed': '✅ Подтверждена',
                            'in_progress': '⏳ В процессе',
                            'completed': '🏁 Выполнена',
                            'cancelled': '❌ Отменена'
                        }.get(app['status'], app['status'])
                        tech = app.get('technician_name') or "🧑‍🔧 Не назначен"
                        info = (
                            f"📄 <b>Номер заявки:</b> #{app['id']} {status_emoji}\n"
                            f"👤 <b>Клиент:</b> {app.get('client_name') or 'Неизвестно'}\n"
                            f"📞 <b>Телефон:</b> {app.get('client_phone') or '-'}\n"
                            f"📍 <b>Адрес:</b> {app.get('address') or '-'}\n"
                            f"📝 <b>Описание:</b> {app.get('description') or '-'}\n"
                            f"📊 <b>Статус:</b> {status_text}\n"
                            f"🧑‍🔧 <b>Техник:</b> {tech}\n"
                            f"🕒 <b>Создано:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                            f"📅 <b>Назначено:</b> {app.get('assigned_at').strftime('%d.%m.%Y %H:%M') if app.get('assigned_at') else '-'}\n"
                            f"✅ <b>Завершено:</b> {app.get('completed_at').strftime('%d.%m.%Y %H:%M') if app.get('completed_at') else '-'}\n"
                        )
                    if app.get('media'):
                        await callback.message.answer_photo(photo=app['media'], caption=info, parse_mode='HTML')
                    else:
                        await callback.message.answer(info, parse_mode='HTML')
                # Pagination buttons
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ Oldingi" if lang == 'uz' else "◀️ Предыдущая",
                        callback_data=f"manager_apps_page_{page-1}"
                    ))
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text="Keyingi ➡️" if lang == 'uz' else "Следующая ▶️",
                        callback_data=f"manager_apps_page_{page+1}"
                    ))
                if buttons:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                    page_text = f"📄 {page*per_page if page*per_page <= total else total}/{total}"
                    await callback.message.answer(page_text, reply_markup=keyboard)
                await callback.answer()
            finally:
                await conn.release()
        except Exception as e:
            logger.error(f"Error in manager_apps_page_callback: {str(e)}", exc_info=True)
            error_text = "❗️ Xatolik yuz berdi" if lang == 'uz' else "❗️ Произошла ошибка"
            await callback.message.answer(error_text)

    return router
