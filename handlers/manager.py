from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import Dict, Any, List
from datetime import datetime, timedelta, date
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call

from keyboards.manager_buttons import (
    get_manager_main_keyboard, get_status_keyboard, get_report_type_keyboard,
    get_equipment_keyboard, get_assign_technician_keyboard, get_back_inline_keyboard,
    get_filter_keyboard, get_filtered_applications_keyboard, get_filter_results_keyboard,
    get_confirmation_keyboard, get_application_actions_keyboard, get_manager_language_keyboard,
    get_manager_back_keyboard, zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard, get_staff_activity_menu,
    get_notifications_settings_menu
)
from states.manager_states import ManagerStates
from database.queries import (
    db_manager,get_filtered_applications,
    get_user_by_telegram_id, get_all_zayavki, get_zayavka_by_id, update_zayavka_status,
    get_available_technicians, assign_zayavka_to_technician, genere_report,
    get_equipment_list, issue_equipment, mark_ready_for_installation,
    get_filtered_zayavki, create_zayavka, get_staff_activity_stats,
    get_notification_settings, update_notification_settings
)
from utils.logger import setup_logger
from handlers.language import show_language_selection, process_language_change, get_user_lang

# Setup logger
logger = setup_logger('bot.manager')

router = Router()

async def manager_menu(message):
    """Compatibility wrapper for manager main menu"""
    await manager_main_menu_handler(message, None)


@router.message(F.text.in_(["👨‍💼 Manager", "👨‍💼 Менеджер", "👨‍💼 Menejer"]))
async def manager_start(message: Message, state: FSMContext):
    """Manager main menu"""
    try:
        await safe_remove_inline(message)
        await state.clear()
        user = await get_user_by_telegram_id(message.from_user.id)
        
        if not user or user['role'] != 'manager':
            lang = user.get('language', 'uz')
            text = "Sizda menejer huquqi yo'q." if lang == 'uz' else "У вас нет прав менеджера."
            await message.answer(text)
            return
        
        lang = user.get('language', 'uz')
        welcome_text = "Menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель менеджера!"
        
        await message.answer(
            welcome_text,
            reply_markup=get_manager_main_keyboard(lang)
        )
        await state.set_state(ManagerStates.main_menu)
        
        logger.info(f"Manager {user['id']} accessed main menu")
        
    except Exception as e:
        logger.error(f"Error in manager_start: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

@router.message(F.text.in_(["📝 Ariza yaratish", "📝 Создать заявку"]))
async def create_application(message: Message, state: FSMContext):
    """Start creating new application"""
    try:
        await safe_remove_inline(message)
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
        await safe_remove_inline_call(callback)
        app_type = callback.data.split("_")[3]  # b2b or b2c
        await state.update_data(application_type=app_type)
        
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        description_text = "Ariza tavsifini kiriting:" if lang == 'uz' else "Введите описание заявки:"
        await callback.message.edit_text(description_text)
        await state.set_state(ManagerStates.creating_application_description)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in select_application_type: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(ManagerStates.creating_application_description))
async def get_application_description(message: Message, state: FSMContext):
    """Get application description"""
    try:
        await safe_remove_inline(message)
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
        await safe_remove_inline(message)
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
        await safe_remove_inline(message)
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
        await safe_remove_inline(message)
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
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        media_request_text = "Rasm yoki videoni yuboring:" if lang == 'uz' else "Отправьте фото или видео:"
        await callback.message.edit_text(media_request_text)
        await state.set_state(ManagerStates.creating_application_waiting_media)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in request_application_media: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "manager_attach_media_no")
async def skip_application_media(callback: CallbackQuery, state: FSMContext):
    """Skip media for application"""
    try:
        await safe_remove_inline_call(callback)
        await ask_for_application_location(callback, state)
    except Exception as e:
        logger.error(f"Error in skip_application_media: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(ManagerStates.creating_application_waiting_media), F.photo | F.video)
async def process_application_media(message: Message, state: FSMContext):
    """Process application media"""
    try:
        await safe_remove_inline(message)
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
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        location_request_text = "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:"
        await callback.message.edit_text(location_request_text)
        await state.set_state(ManagerStates.creating_application_waiting_location)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in request_application_location: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "manager_send_location_no")
async def skip_application_location(callback: CallbackQuery, state: FSMContext):
    """Skip location for application"""
    try:
        await show_application_confirmation(callback, state)
    except Exception as e:
        logger.error(f"Error in skip_application_location: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(ManagerStates.creating_application_waiting_location), F.location)
async def process_application_location(message: Message, state: FSMContext):
    """Process application location"""
    try:
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
            'status': 'new'
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
    """Manager: View all applications with pagination and full info (single language)"""
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        lang = user.get('language', 'uz')
        page = 1
        per_page = 5
        await state.update_data(manager_apps_page=page)
        conn = await db_manager.get_connection()
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
            await db_manager.pool.release(conn)
    except Exception as e:
        logger.error(f"Error in view_applications: {str(e)}", exc_info=True)
        error_text = "❗️ Xatolik yuz berdi" if lang == 'uz' else "❗️ Произошла ошибка"
        await message.answer(error_text)

# Pagination callback for manager applications
@router.callback_query(lambda c: c.data.startswith('manager_apps_page_'))
async def manager_apps_page_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        page = int(callback.data.split('_')[-1])
        per_page = 5
        await state.update_data(manager_apps_page=page)
        conn = await db_manager.get_connection()
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
            await db_manager.pool.release(conn)
    except Exception as e:
        logger.error(f"Error in manager_apps_page_callback: {str(e)}", exc_info=True)
        error_text = "❗️ Xatolik yuz berdi" if lang == 'uz' else "❗️ Произошла ошибка"
        await callback.message.answer(error_text)

@router.message(lambda m: m.text in ["🔍 Filtrlar", "🔍 Фильтры"])
async def show_filter_menu(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    # Delete previous menu message if exists
    data = await state.get_data()
    last_msg_id = data.get('last_menu_msg_id')
    if last_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_msg_id)
        except Exception:
            pass
    lang = await get_user_lang(message.from_user.id)
    try:
        filter_text = f"🔍 {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
        sent_msg = await message.answer(filter_text, reply_markup=get_filter_keyboard(lang))
        await state.update_data(last_menu_msg_id=sent_msg.message_id)
    except Exception as e:
        logger.error(f"Filter menu error: {str(e)}", exc_info=True)
        await message.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}")

@router.callback_query(F.data.startswith("filter_"))
async def process_filter(callback: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    lang = await get_user_lang(callback.from_user.id)
    try:
        parts = callback.data.split('_')
        filter_type = parts[1]
        page = 1
        if len(parts) > 2 and parts[-1].isdigit():
            page = int(parts[-1])
        result = None
        filter_kwargs = {'page': page, 'limit': 5}
        # --- Filter label logic ---
        filter_label = ""
        if filter_type == 'status':
            status = '_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])
            if status == 'all':
                filter_label = f"📋 {'Barcha statuslar' if lang == 'uz' else 'Все статусы'}"
                result = await get_filtered_applications(**filter_kwargs)
            else:
                status_emoji = {
                    'new': '🆕',
                    'in_progress': '⏳',
                    'completed': '✅',
                    'cancelled': '❌'
                }.get(status, '📋')
                status_label = {
                    'new': 'Yangi' if lang == 'uz' else 'Новый',
                    'in_progress': 'Jarayonda' if lang == 'uz' else 'В процессе',
                    'completed': 'Yakunlandi' if lang == 'uz' else 'Завершено',
                    'cancelled': 'Bekor qilindi' if lang == 'uz' else 'Отменено'
                }.get(status, status)
                filter_label = f"{status_emoji} {'Status:' if lang == 'uz' else 'Статус:'} {status_label}"
                result = await get_filtered_applications(statuses=[status], **filter_kwargs)
        elif filter_type == 'date':
            date_type = parts[2]
            today = date.today()
            # 2ta tilda (uz va ru) date_labels lug'ati va ishlatishda to'g'ri tilni tanlash
            date_labels = {
                'today': {
                    'uz': "📅 Bugun",
                    'ru': "📅 Сегодня"
                },
                'yesterday': {
                    'uz': "📅 Kecha",
                    'ru': "📅 Вчера"
                },
                'week': {
                    'uz': "📅 Bu hafta",
                    'ru': "📅 На этой неделе"
                },
                'month': {
                    'uz': "📅 Bu oy",
                    'ru': "📅 В этом месяце"
                }
            }
            filter_label = date_labels.get(date_type, {}).get(lang, f"📅 {date_type}")
            if date_type == 'today':
                date_from = date_to = today
            elif date_type == 'yesterday':
                date_from = date_to = today - timedelta(days=1)
            elif date_type == 'week':
                date_from = today - timedelta(days=today.weekday())
                date_to = today
            elif date_type == 'month':
                date_from = today.replace(day=1)
                date_to = today
            else:
                date_from = date_to = today
            result = await get_filtered_applications(date_from=date_from, date_to=date_to, **filter_kwargs)
        elif filter_type == 'tech':
            tech_type = parts[2]
            if tech_type == 'assigned':
                filter_label = f"👨‍🔧 {'Biriktirilgan' if lang == 'uz' else 'Назначенные'}"
                result = await get_filtered_applications(assigned_only=True, **filter_kwargs)
            elif tech_type == 'unassigned':
                filter_label = f"👨‍🔧 {'Biriktirilmagan' if lang == 'uz' else 'Не назначенные'}"
                result = await get_filtered_applications(technician_id=0, **filter_kwargs)
        elif filter_type == 'clear':
            filter_text = f"🔍 {'Kerakli filtrlarni tanlang:' if lang == 'uz' else 'Выберите нужные фильтры:'}"
            try:
                await callback.message.edit_text(
                    filter_text,
                    reply_markup=get_filter_keyboard(lang)
                )
            except Exception as e:
                logger.error(f"Edit text error (clear): {str(e)}", exc_info=True)
                await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
                return
            await callback.answer()
            return
        applications = result['applications'] if result and result.get('applications') else []
        total_pages = result.get('total_pages', 1) if result else 1
        current_page = result.get('page', 1) if result else 1
        status_emojis = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }
        # 2ta tilda, emojilar bilan
        labels_uz = {
            'status': "🆕 Status:",
            'client': "👤 Mijoz:",
            'address': "📍 Manzil:",
            'description': "📝 Izoh:",
            'technician': "👨‍🔧 Texnik:",
            'created': "🕒 Yaratilgan:",
            'no_technician': "❌ Texnik biriktirilmagan",
            'no_address': "❌ Manzil ko'rsatilmagan",
            'filtered': "🔍 Filtrlangan arizalar",
            'no_applications': "❌ Arizalar topilmadi",
            'clear_filter': "🔄 Filterni tozalash",
        }
        labels_ru = {
            'status': "🆕 Статус:",
            'client': "👤 Клиент:",
            'address': "📍 Адрес:",
            'description': "📝 Описание:",
            'technician': "👨‍🔧 Техник:",
            'created': "🕒 Создано:",
            'no_technician': "❌ Не назначен",
            'no_address': "❌ Адрес не указан",
            'filtered': "🔍 Отфильтрованные заявки",
            'no_applications': "❌ Заявки не найдены",
            'clear_filter': "🔄 Сбросить фильтр",
        }
        labels = labels_uz if lang == 'uz' else labels_ru
        applications_text = f"{filter_label} ({current_page}/{total_pages}):\n\n"
        if applications:
            for app in applications:
                status = app.get('status', 'new')
                status_emoji = status_emojis.get(status, '📋')
                # 2 tilda, emoji bilan chiroyli formatda chiqaramiz
                if lang == 'uz':
                    applications_text += (
                        f"{status_emoji} <b>Status:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                        f"👤 <b>Mijoz:</b> <i>{app.get('user_name',)}</i> | 📞 <b>Tel:</b> <i>{app.get('client_phone', '-')}</i>\n"
                        f"📍 <b>Manzil:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                        f"📝 <b>Izoh:</b> <i>{app.get('description', '')[:100]}</i>\n"
                        f"👨‍🔧 <b>Texnik:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> | 📞 <i>{app.get('technician_phone', '-')}</i>\n"
                        f"🕒 <b>Yaratilgan:</b> <i>{app.get('created_at', '')}</i>\n"
                        f"🔎 <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                    )
                else:
                    applications_text += (
                        f"{status_emoji} <b>Статус:</b> <i>{status_label if 'status_label' in locals() else status}</i>\n"
                        f"👤 <b>Клиент:</b> <i>{app.get('user_name')}</i> | 📞 <b>Тел:</b> <i>{app.get('client_phone', '-')}</i>\n"
                        f"📍 <b>Адрес:</b> <i>{app.get('address') or labels['no_address']}</i>\n"
                        f"📝 <b>Описание:</b> <i>{app.get('description', '')[:100]}</i>\n"
                        f"👨‍🔧 <b>Техник:</b> <i>{app.get('technician_name', labels['no_technician'])}</i> | 📞 <i>{app.get('technician_phone', '-')}</i>\n"
                        f"🕒 <b>Создано:</b> <i>{app.get('created_at', '')}</i>\n"
                        f"🔎 <b>ID:</b> <code>{app.get('id', '-')}</code>\n"
                        "━━━━━━━━━━━━━━━━━━━━━━\n"
                    )
        else:
            applications_text += f"❌ {labels['no_applications']}\n\n"
        # Pagination buttons
        inline_keyboard = []
        if total_pages > 1:
            nav_buttons = []
            if current_page > 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="⬅️", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page-1}"
                ))
            nav_buttons.append(InlineKeyboardButton(
                text=f"{current_page}/{total_pages}", callback_data="noop"
            ))
            if current_page < total_pages:
                nav_buttons.append(InlineKeyboardButton(
                    text="➡️", callback_data=f"filter_{filter_type}_{'_'.join(parts[2:-1]) if parts[-1].isdigit() else '_'.join(parts[2:])}_{current_page+1}"
                ))
            inline_keyboard.append(nav_buttons)
        # Always show clear button
        inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🔄 {labels['clear_filter']}",
                callback_data="filter_clear"
            )
        ])
        keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        try:
            await callback.message.edit_text(applications_text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Edit text error: {str(e)}", exc_info=True)
            await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
            return
        await callback.answer()
    except Exception as e:
        logger.error(f"Error processing filter: {str(e)}", exc_info=True)
        await callback.answer(
            f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}",
            show_alert=True
        )

@router.callback_query(F.data.startswith("view_application_"))
async def view_filtered_application(callback: CallbackQuery):
    await safe_remove_inline_call(callback)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    """Show detailed information about filtered application"""
    lang = await get_user_lang(callback.from_user.id)
    
    try:
        app_id = int(callback.data.replace("view_application_", ""))
        app = await get_zayavka_by_id(app_id)
        
        if not app:
            await callback.answer(f"❌ {'Ariza topilmadi.' if lang == 'uz' else 'Заявка не найдена.'}", show_alert=True)
            return
        
        status_emoji = {
            'new': '🆕',
            'in_progress': '⏳',
            'completed': '✅',
            'cancelled': '❌'
        }.get(app.get('status', 'new'), '📋')
        
        # 2ta tilda app_text_uz va app_text_ru chiroyli formatda

        app_text_uz = (
            f"📋 <b>Ariza ma'lumotlari</b>\n\n"
            f"🆔 <b>ID:</b> {app['id']}\n"
            f"👤 <b>Mijoz:</b> {app.get('user_name', '-')}\n"
            f"📞 <b>Telefon:</b> {app.get('phone_number', '-')}\n"
            f"📝 <b>Tavsif:</b> {app.get('description', '-')}\n"
            f"📍 <b>Manzil:</b> {app.get('address', '-')}\n"
            f"📅 <b>Sana:</b> {app.get('created_at', '-')}\n"
            f"📊 <b>Status:</b> {status_emoji} {app.get('status', '-')}"
        )

        app_text_ru = (
            f"📋 <b>Информация о заявке</b>\n\n"
            f"🆔 <b>ID:</b> {app['id']}\n"
            f"👤 <b>Клиент:</b> {app.get('user_name', '-')}\n"
            f"📞 <b>Телефон:</b> {app.get('phone_number', '-')}\n"
            f"📝 <b>Описание:</b> {app.get('description', '-')}\n"
            f"📍 Адрес: {app.get('address', '-')}\n"
            f"📅 Дата: {app.get('created_at', '-')}\n"
            f"📊 Статус: {status_emoji} {app.get('status', '-')}"
        )

        app_text = app_text_uz if lang == 'uz' else app_text_ru
        
        # Show application info with back to filter button
        await callback.message.edit_text(
            app_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=f"🔍 {'Filtrlashga qaytish' if lang == 'uz' else 'Вернуться к фильтрам'}", 
                    callback_data="filter_clear"
                )
            ]])
        )
        
    except Exception as e:
        logger.error(f"Error viewing filtered application: {str(e)}", exc_info=True)
        await callback.answer(f"❌ {'Xatolik yuz berdi' if lang == 'uz' else 'Произошла ошибка'}", show_alert=True)
    
    await callback.answer()

@router.message(F.text.in_(["🔄 Status o'zgartirish", "🔄 Изменить статус"]))
async def change_status_menu(message: Message, state: FSMContext):
    """Show status change menu (localized, emoji, more info)"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return

        lang = user.get('language', 'uz')
        if lang == 'uz':
            status_text = "🔢 Ariza raqamini kiriting (masalan, 123 yoki #123):"
        else:
            status_text = "🔢 Введите номер заявки (например, 123 или #123):"

        await message.answer(status_text)
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
        await safe_remove_inline(message)
        app_id = int(message.text.strip().replace('#', ''))
        application = await get_zayavka_by_id(app_id)

        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')

        if not application:
            not_found_text = "❌ Ariza topilmadi." if lang == 'uz' else "❌ Заявка не найдена."
            await message.answer(not_found_text)
            return

        await state.update_data(selected_application_id=app_id)

        # Status and emoji mapping
        status_emoji = {
            'new': '🆕',
            'confirmed': '✅',
            'in_progress': '⏳',
            'completed': '🏁',
            'cancelled': '❌'
        }
        status_texts = {
            'uz': {
                'new': "🆕 Yangi",
                'confirmed': "✅ Tasdiqlangan",
                'in_progress': "⏳ Jarayonda",
                'completed': "🏁 Bajarilgan",
                'cancelled': "❌ Bekor qilingan"
            },
            'ru': {
                'new': "🆕 Новая",
                'confirmed': "✅ Подтверждена",
                'in_progress': "⏳ В процессе",
                'completed': "🏁 Выполнена",
                'cancelled': "❌ Отменена"
            }
        }
        # Fallback for status
        status_val = application.get('status', 'new')
        status_str = status_texts['uz' if lang == 'uz' else 'ru'].get(status_val, status_val)
        status_ico = status_emoji.get(status_val, '📋')

        # Technician info
        tech_name = application.get('technician_name')
        if lang == 'uz':
            tech_str = f"🧑‍🔧 <b>Texnik:</b> {tech_name if tech_name else 'Tayinlanmagan'}"
        else:
            tech_str = f"🧑‍🔧 <b>Техник:</b> {tech_name if tech_name else 'Не назначен'}"

        # Build info message
        if lang == 'uz':
            info = (
                f"📄 <b>Zayavka raqami:</b> #{app_id} {status_ico}\n"
                f"👤 <b>Mijoz:</b> {application.get('client_name') or 'Noma\'lum'}\n"
                f"📞 <b>Telefon:</b> {application.get('client_phone') or '-'}\n"
                f"📍 <b>Manzil:</b> {application.get('address') or '-'}\n"
                f"📝 <b>Tavsif:</b> {application.get('description') or '-'}\n"
                f"{tech_str}\n"
                f"📊 <b>Status:</b> {status_str}\n"
                f"🕒 <b>Yaratilgan:</b> {application.get('created_at').strftime('%Y-%m-%d %H:%M') if application.get('created_at') else '-'}\n\n"
                f"⬇️ Yangi statusni tanlang:"
            )
        else:
            info = (
                f"📄 <b>Номер заявки:</b> #{app_id} {status_ico}\n"
                f"👤 <b>Клиент:</b> {application.get('client_name') or 'Неизвестно'}\n"
                f"📞 <b>Телефон:</b> {application.get('client_phone') or '-'}\n"
                f"📍 <b>Адрес:</b> {application.get('address') or '-'}\n"
                f"📝 <b>Описание:</b> {application.get('description') or '-'}\n"
                f"{tech_str}\n"
                f"📊 <b>Статус:</b> {status_str}\n"
                f"🕒 <b>Создана:</b> {application.get('created_at').strftime('%Y-%m-%d %H:%M') if application.get('created_at') else '-'}\n\n"
                f"⬇️ Выберите новый статус:"
            )

        available_statuses = ['new', 'confirmed', 'in_progress', 'completed', 'cancelled']

        await message.answer(
            info,
            reply_markup=get_status_keyboard(available_statuses, app_id, lang)
        )
        await state.set_state(ManagerStates.changing_status)

    except ValueError:
        lang = await get_user_lang(message.from_user.id)
        invalid_id_text = "❗️ Noto'g'ri ariza raqami." if lang == 'uz' else "❗️ Неверный номер заявки."
        await message.answer(invalid_id_text)
    except Exception as e:
        logger.error(f"Error in get_application_for_status_change: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("status_"))
async def change_application_status(callback: CallbackQuery, state: FSMContext):
    """Change application status, show result in user's language with emoji"""
    try:
        await safe_remove_inline_call(callback)
        parts = callback.data.split("_")
        new_status = parts[1]
        app_id = int(parts[2])

        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')

        # Update status
        success = await update_zayavka_status(app_id, new_status)

        # Status and emoji mapping
        status_emoji = {
            'new': '🆕',
            'confirmed': '✅',
            'in_progress': '⏳',
            'completed': '🏁',
            'cancelled': '❌'
        }
        status_texts = {
            'uz': {
                'new': "🆕 Yangi",
                'confirmed': "✅ Tasdiqlangan",
                'in_progress': "⏳ Jarayonda",
                'completed': "🏁 Bajarilgan",
                'cancelled': "❌ Bekor qilingan"
            },
            'ru': {
                'new': "🆕 Новая",
                'confirmed': "✅ Подтверждена",
                'in_progress': "⏳ В процессе",
                'completed': "🏁 Выполнена",
                'cancelled': "❌ Отменена"
            }
        }
        status_str = status_texts['uz' if lang == 'uz' else 'ru'].get(new_status, new_status)
        status_ico = status_emoji.get(new_status, '📋')

        if success:
            if lang == 'uz':
                success_text = f"✅ Ariza #{app_id} statusi yangilandi: {status_str} {status_ico}"
            else:
                success_text = f"✅ Статус заявки #{app_id} обновлен: {status_str} {status_ico}"
            await callback.message.edit_text(success_text)
            logger.info(f"Application {app_id} status changed to {new_status} by manager {user['id']}")
        else:
            error_text = "❌ Status yangilashda xatolik." if lang == 'uz' else "❌ Ошибка при обновлении статуса."
            await callback.message.edit_text(error_text)

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in change_application_status: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["👨‍🔧 Texnik biriktirish", "👨‍🔧 Назначить техника"]))
async def assign_technician_menu(message: Message, state: FSMContext):
    """Show technician assignment menu"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        app_id_text = "Ariza raqamini kiriting:" if lang == 'uz' else "Введите номер заявки:"
        
        await message.answer(app_id_text)
        await state.set_state(ManagerStates.entering_application_id_for_assignment)
        
    except Exception as e:
        logger.error(f"Error in assign_technician_menu: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(StateFilter(ManagerStates.entering_application_id_for_assignment))
async def get_application_for_assignment(message: Message, state: FSMContext):
    """Get application ID for technician assignment"""
    try:
        await safe_remove_inline(message)
        app_id = int(message.text.strip().replace('#', ''))
        application = await get_zayavka_by_id(app_id)
        
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        if not application:
            not_found_text = "Ariza topilmadi." if lang == 'uz' else "Заявка не найдена."
            await message.answer(not_found_text)
            return
        
        # Get available technicians
        technicians = await get_available_technicians()
        
        if not technicians:
            no_techs_text = "Hozirda bo'sh texniklar yo'q." if lang == 'uz' else "Сейчас нет доступных техников."
            await message.answer(no_techs_text)
            return
        
        await state.update_data(selected_application_id=app_id)
        
        select_tech_text = f"Ariza #{app_id} uchun texnikni tanlang:" if lang == 'uz' else f"Выберите техника для заявки #{app_id}:"
        
        await message.answer(
            select_tech_text,
            reply_markup=get_assign_technician_keyboard(app_id, technicians, lang)
        )
        await state.set_state(ManagerStates.assigning_technician)
        
    except ValueError:
        invalid_id_text = "Noto'g'ri ariza raqami." if lang == 'uz' else "Неверный номер заявки."
        await message.answer(invalid_id_text)
    except Exception as e:
        logger.error(f"Error in get_application_for_assignment: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("manager_assign_zayavka_"))
async def assign_technician_to_application(callback: CallbackQuery, state: FSMContext):
    """Assign technician to application"""
    try:
        await safe_remove_inline_call(callback)
        parts = callback.data.split("_")
        app_id = int(parts[3])
        tech_id = int(parts[4])
        
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Assign technician
        success = await assign_zayavka_to_technician(app_id, tech_id)
        
        if success:
            success_text = f"✅ Ariza #{app_id} texnikga biriktirildi!" if lang == 'uz' else f"✅ Заявка #{app_id} назначена технику!"
            await callback.message.edit_text(success_text)
            logger.info(f"Application {app_id} assigned to technician {tech_id} by manager {user['id']}")
        else:
            error_text = "Texnik biriktirshda xatolik." if lang == 'uz' else "Ошибка при назначении техника."
            await callback.message.edit_text(error_text)
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in assign_technician_to_application: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["📊 Hisobot yaratish", "📊 Создать отчет"]))
async def generate_report_menu(message: Message, state: FSMContext):
    """Show report generation menu"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        report_type_text = "Hisobot turini tanlang:" if lang == 'uz' else "Выберите тип отчета:"
        
        await message.answer(
            report_type_text,
            reply_markup=get_report_type_keyboard(lang)
        )
        await state.set_state(ManagerStates.selecting_report_type)
        
    except Exception as e:
        logger.error(f"Error in generate_report_menu: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("report_"))
async def generate_report_handler(callback: CallbackQuery, state: FSMContext):
    """Generate report"""
    try:
        await safe_remove_inline_call(callback)
        report_format = callback.data.split("_")[1]  
        
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        generating_text = "Hisobot yaratilmoqda..." if lang == 'uz' else "Создается отчет..."
        await callback.message.edit_text(generating_text)
        
        # Generate report
        report_file = await generate_report(report_format, lang)
        
        if report_file:
            # Send report file
            with open(report_file, 'rb') as file:
                await callback.message.answer_document(
                    document=file,
                    caption=f"Hisobot ({report_format.upper()})" if lang == 'uz' else f"Отчет ({report_format.upper()})"
                )
            
            success_text = "Hisobot muvaffaqiyatli yaratildi!" if lang == 'uz' else "Отчет успешно создан!"
            await callback.message.edit_text(success_text)
            
            logger.info(f"Report generated by manager {user['id']} in {report_format} format")
        else:
            error_text = "Hisobot yaratishda xatolik." if lang == 'uz' else "Ошибка при создании отчета."
            await callback.message.edit_text(error_text)
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in generate_report_handler: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["📦 Jihozlar berish", "📦 Выдача оборудования"]))
async def equipment_issuance_menu(message: Message, state: FSMContext):
    """Show equipment issuance menu"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        equipment_list = await get_equipment_list()
        
        if not equipment_list:
            no_equipment_text = "Hozirda jihozlar yo'q." if lang == 'uz' else "Сейчас нет оборудования."
            await message.answer(no_equipment_text)
            return
        
        select_equipment_text = "Beriladigan jihozni tanlang:" if lang == 'uz' else "Выберите оборудование для выдачи:"
        
        await message.answer(
            select_equipment_text,
            reply_markup=get_equipment_keyboard(equipment_list, lang)
        )
        await state.set_state(ManagerStates.selecting_equipment)
        
    except Exception as e:
        logger.error(f"Error in equipment_issuance_menu: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("equipment_"))
async def issue_equipment_handler(callback: CallbackQuery, state: FSMContext):
    """Issue equipment"""
    try:
        await safe_remove_inline_call(callback)
        equipment_id = int(callback.data.split("_")[1])
        
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Issue equipment
        success = await issue_equipment(equipment_id, user['id'])
        
        if success:
            success_text = "✅ Jihoz muvaffaqiyatli berildi!" if lang == 'uz' else "✅ Оборудование успешно выдано!"
            await callback.message.edit_text(success_text)
            logger.info(f"Equipment {equipment_id} issued by manager {user['id']}")
        else:
            error_text = "Jihoz berishda xatolik." if lang == 'uz' else "Ошибка при выдаче оборудования."
            await callback.message.edit_text(error_text)
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in issue_equipment_handler: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["✅ O'rnatishga tayyor", "✅ Готов к установке"]))
async def ready_for_installation_menu(message: Message, state: FSMContext):
    """Mark application as ready for installation"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        app_id_text = "O'rnatishga tayyor ariza raqamini kiriting:" if lang == 'uz' else "Введите номер заявки готовой к установке:"
        
        await message.answer(app_id_text)
        await state.set_state(ManagerStates.marking_ready_for_installation)
        
    except Exception as e:
        logger.error(f"Error in ready_for_installation_menu: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(StateFilter(ManagerStates.marking_ready_for_installation))
async def mark_ready_for_installation_handler(message: Message, state: FSMContext):
    """Mark application as ready for installation"""
    try:
        await safe_remove_inline(message)
        app_id = int(message.text.strip().replace('#', ''))
        
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        # Mark as ready for installation
        success = await mark_ready_for_installation(app_id)
        
        if success:
            success_text = f"✅ Ariza #{app_id} o'rnatishga tayyor deb belgilandi!" if lang == 'uz' else f"✅ Заявка #{app_id} отмечена как готовая к установке!"
            await message.answer(success_text)
            logger.info(f"Application {app_id} marked as ready for installation by manager {user['id']}")
        else:
            error_text = "Belgilashda xatolik." if lang == 'uz' else "Ошибка при отметке."
            await message.answer(error_text)
        
        await state.clear()
        
    except ValueError:
        invalid_id_text = "Noto'g'ri ariza raqami." if lang == 'uz' else "Неверный номер заявки."
        await message.answer(invalid_id_text)
    except Exception as e:
        logger.error(f"Error in mark_ready_for_installation_handler: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(F.text.in_(["👥 Xodimlar faoliyati", "👥 Активность сотрудников"]))
async def staff_activity_handler(message: Message, state: FSMContext):
    """Handle staff activity monitoring"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        activity_text = "Xodimlar faoliyati bo'limi" if lang == 'uz' else "Раздел активности сотрудников"
        
        await message.answer(
            activity_text,
            reply_markup=get_staff_activity_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in staff activity: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("staff_"))
async def handle_staff_activity_requests(callback: CallbackQuery, state: FSMContext):
    """Handle staff activity requests"""
    activity_type = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        if activity_type == "technician_performance":
            stats = await get_staff_activity_stats('technician_performance')
            title = "Texniklar samaradorligi" if lang == 'uz' else "Производительность техников"
        elif activity_type == "daily_activity":
            stats = await get_staff_activity_stats('daily_activity')
            title = "Kunlik faollik" if lang == 'uz' else "Ежедневная активность"
        elif activity_type == "weekly_summary":
            stats = await get_staff_activity_stats('weekly_summary')
            title = "Haftalik xulosalar" if lang == 'uz' else "Недельная сводка"
        elif activity_type == "individual_reports":
            stats = await get_staff_activity_stats('individual_reports')
            title = "Shaxsiy hisobotlar" if lang == 'uz' else "Индивидуальные отчеты"
        elif activity_type == "team_comparison":
            stats = await get_staff_activity_stats('team_comparison')
            title = "Jamoa taqqoslash" if lang == 'uz' else "Сравнение команды"
        
        # Format statistics text
        active_staff_text = "Faol xodimlar" if lang == 'uz' else "Активные сотрудники"
        completed_tasks_text = "Bajarilgan vazifalar" if lang == 'uz' else "Выполненные задачи"
        avg_performance_text = "O'rtacha samaradorlik" if lang == 'uz' else "Средняя производительность"
        
        text = f"📊 {title}\n\n"
        text += f"👥 {active_staff_text}: {stats.get('active_staff', 0)}\n"
        text += f"✅ {completed_tasks_text}: {stats.get('completed_tasks', 0)}\n"
        text += f"📈 {avg_performance_text}: {stats.get('avg_performance', 0)}%\n"
        
        if activity_type == "technician_performance":
            top_performers_text = "Eng yaxshi texniklar:" if lang == 'uz' else "Лучшие техники:"
            text += f"\n{top_performers_text}\n"
            for performer in stats.get('top_performers', []):
                text += f"🏆 {performer['name']}: {performer['score']}%\n"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in staff activity requests: {str(e)}")
        error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.message(F.text.in_(["🔔 Bildirishnomalar", "🔔 Уведомления"]))
async def notifications_settings_handler(message: Message, state: FSMContext):
    """Handle notifications settings"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        notifications_text = "Bildirishnomalar sozlamalari" if lang == 'uz' else "Настройки уведомлений"
        
        await message.answer(
            notifications_text,
            reply_markup=get_notifications_settings_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in notifications settings: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("notif_"))
async def handle_notification_settings(callback: CallbackQuery, state: FSMContext):
    """Handle notification settings"""
    try:
        await safe_remove_inline_call(callback)
        setting_type = callback.data.split("_")[1]
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        # Get current settings
        current_settings = await get_notification_settings(user['id'])
        
        # Toggle setting
        new_value = not current_settings.get(setting_type, False)
        await update_notification_settings(user['id'], {setting_type: new_value})
        
        status_text = "yoqildi" if new_value else "o'chirildi"
        if lang == 'ru':
            status_text = "включено" if new_value else "выключено"
        
        setting_names = {
            'new_orders': 'Yangi buyurtmalar' if lang == 'uz' else 'Новые заказы',
            'status_changes': 'Status o\'zgarishlari' if lang == 'uz' else 'Изменения статуса',
            'urgent_issues': 'Shoshilinch masalalar' if lang == 'uz' else 'Срочные вопросы',
            'daily_summary': 'Kunlik xulosalar' if lang == 'uz' else 'Ежедневная сводка',
            'system_alerts': 'Tizim ogohlantirishlari' if lang == 'uz' else 'Системные предупреждения'
        }
        
        setting_name = setting_names.get(setting_type, setting_type)
        success_text = f"✅ {setting_name} {status_text}"
        
        await callback.answer(success_text)
        
    except Exception as e:
        logger.error(f"Error in notification settings: {str(e)}")
        error_text = "Sozlamalarni yangilashda xatolik" if lang == 'uz' else "Ошибка при обновлении настроек"
        await callback.answer(error_text)

@router.callback_query(F.data == "manager_back_main")
async def manager_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Go back to manager main menu"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.set_state(ManagerStates.main_menu)
        welcome_text = "Menejer paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель менеджера!"
        await callback.message.edit_text(
            welcome_text,
            reply_markup=get_manager_main_keyboard(lang)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error going back to main: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]))
async def manager_change_language(message: Message, state: FSMContext):
    """Change language for manager"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        success = await show_language_selection(message, "manager", state)
        if not success:
            lang = user.get('language', 'uz')
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
    except Exception as e:
        logger.error(f"Error in manager change language: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("manager_lang_"))
async def process_manager_language_change(callback: CallbackQuery, state: FSMContext):
    """Process manager language change"""
    try:
        await safe_remove_inline_call(callback)
        await process_language_change(
            call=callback,
            role="manager",
            get_main_keyboard_func=get_manager_main_keyboard,
            state=state
        )
        await state.set_state(ManagerStates.main_menu)
    except Exception as e:
        logger.error(f"Manager tilni o'zgartirishda xatolik: {str(e)}")
        lang = await get_user_lang(callback.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await callback.message.answer(error_text)
        await callback.answer()

@router.message(F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def manager_main_menu_handler(message: Message, state: FSMContext):
    """Handle manager main menu button"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        main_menu_text = "Asosiy menyu" if lang == 'uz' else "Главное меню"
        
        await message.answer(
            main_menu_text,
            reply_markup=get_manager_main_keyboard(lang)
        )
        if state is not None:
            await state.set_state(ManagerStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in manager main menu handler: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

# Handle unknown messages for managers
@router.message()
async def handle_manager_unknown_message(message: Message, state: FSMContext):
    """Handle unknown messages for managers"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        
        lang = user.get('language', 'uz')
        unknown_text = "Noma'lum buyruq. Menyudan tanlang." if lang == 'uz' else "Неизвестная команда. Выберите из меню."
        
        await message.answer(
            unknown_text,
            reply_markup=get_manager_main_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in handle_manager_unknown_message: {str(e)}", exc_info=True)
