from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from typing import Dict, Any, List
from datetime import datetime

from keyboards.client_buttons import (
    get_contact_keyboard, get_main_menu_keyboard, get_back_keyboard,
    get_reply_keyboard, get_language_keyboard, zayavka_type_keyboard,
    media_attachment_keyboard, geolocation_keyboard, confirmation_keyboard,
    get_client_profile_menu, get_client_help_menu, get_client_help_back_inline
)
from states.user_states import UserStates
from database.queries import (
    get_user_by_telegram_id, create_user, update_user_language,
    create_zayavka, get_user_zayavki, get_zayavka_by_id, 
    create_feedback, get_client_info, update_client_info, get_zayavka_solutions
)
from utils.logger import setup_logger
from utils.validators import validate_phone_number, validate_address
from handlers.language import show_language_selection, process_language_change, get_user_lang
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from database.queries import db_manager

# Setup logger
logger = setup_logger('bot.client')

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for clients"""
    try:
        await safe_remove_inline(message)
        await state.clear()
        
        # Check if user exists in database
        user = await get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            # Create new user
            user_data = {
                'telegram_id': str(message.from_user.id),
                'username': message.from_user.username,
                'full_name': message.from_user.full_name,
                'role': 'client',
                'language': 'uz'  # Default language
            }
            user_id = await create_user(user_data)
            if user_id:
                user = await get_user_by_telegram_id(message.from_user.id)
                logger.info(f"New client user created: {message.from_user.id}")
        
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            return
        
        lang = user.get('language', 'uz')
        
        # Check if user has shared contact
        if not user.get('phone_number'):
            welcome_text = (
                "Xush kelibsiz! Iltimos, kontaktingizni ulashing."
                if lang == 'uz' else
                "Добро пожаловать! Пожалуйста, поделитесь своим контактом."
            )
            await message.answer(
                welcome_text,
                reply_markup=get_contact_keyboard(lang)
            )
            await state.set_state(UserStates.waiting_for_contact)
        else:
            welcome_text = (
                "Xush kelibsiz! Quyidagi menyudan kerakli bo'limni tanlang."
                if lang == 'uz' else
                "Добро пожаловать! Выберите нужный раздел из меню ниже."
            )
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(lang)
            )
            await state.set_state(UserStates.main_menu)
            
    except Exception as e:
        logger.error(f"Error in cmd_start: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

@router.message(StateFilter(UserStates.waiting_for_contact), F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return
        
        # Update user's phone number
        from database.queries import update_user_phone
        await update_user_phone(user['id'], message.contact.phone_number)
        
        lang = user.get('language', 'uz')
        success_text = (
            "Rahmat! Endi barcha xizmatlardan foydalanishingiz mumkin."
            if lang == 'uz' else
            "Спасибо! Теперь вы можете пользоваться всеми услугами."
        )
        
        await message.answer(
            success_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        
        logger.info(f"Client contact updated: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in process_contact: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
async def new_order(message: Message, state: FSMContext):
    """Start new order process"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return
        
        lang = user.get('language', 'uz')
        
        # Check if user has phone number
        if not user.get('phone_number'):
            contact_required_text = (
                "Buyurtma berish uchun kontaktingizni ulashing."
                if lang == 'uz' else
                "Для оформления заказа поделитесь своим контактом."
            )
            await message.answer(
                contact_required_text,
                reply_markup=get_contact_keyboard(lang)
            )
            await state.set_state(UserStates.waiting_for_contact)
            return
        
        order_type_text = (
            "Buyurtma turini tanlang:"
            if lang == 'uz' else
            "Выберите тип заказа:"
        )
        
        await message.answer(
            order_type_text,
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.set_state(UserStates.selecting_order_type)
        
    except Exception as e:
        logger.error(f"Error in new_order: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("zayavka_type_"))
async def select_order_type(callback: CallbackQuery, state: FSMContext):
    """Select order type"""
    try:
        await safe_remove_inline_call(callback)
        order_type = callback.data.split("_")[2]  # b2b or b2c
        await state.update_data(order_type=order_type)
        
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        description_text = (
            "Buyurtma tavsifini kiriting:"
            if lang == 'uz' else
            "Введите описание заказа:"
        )
        
        await callback.message.edit_text(description_text)
        await state.set_state(UserStates.entering_description)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in select_order_type: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(UserStates.entering_description))
async def get_order_description(message: Message, state: FSMContext):
    """Get order description"""
    try:
        await safe_remove_inline(message)
        await state.update_data(description=message.text)
        
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        address_text = (
            "Manzilni kiriting:"
            if lang == 'uz' else
            "Введите адрес:"
        )
        
        await message.answer(address_text)
        await state.set_state(UserStates.entering_address)
        
    except Exception as e:
        logger.error(f"Error in get_order_description: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(StateFilter(UserStates.entering_address))
async def get_order_address(message: Message, state: FSMContext):
    """Get order address"""
    try:
        await safe_remove_inline(message)
        address = message.text.strip()
        
        # Validate address
        if not validate_address(address):
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            invalid_address_text = (
                "Noto'g'ri manzil. Iltimos, to'liq manzilni kiriting."
                if lang == 'uz' else
                "Неверный адрес. Пожалуйста, введите полный адрес."
            )
            await message.answer(invalid_address_text)
            return
        
        await state.update_data(address=address)
        
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        media_question_text = (
            "Rasm yoki video biriktirmoqchimisiz?"
            if lang == 'uz' else
            "Хотите прикрепить фото или видео?"
        )
        
        await message.answer(
            media_question_text,
            reply_markup=media_attachment_keyboard(lang)
        )
        await state.set_state(UserStates.asking_for_media)
        
    except Exception as e:
        logger.error(f"Error in get_order_address: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data == "attach_media_yes")
async def request_media(callback: CallbackQuery, state: FSMContext):
    """Request media attachment"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        media_request_text = (
            "Rasm yoki videoni yuboring:"
            if lang == 'uz' else
            "Отправьте фото или видео:"
        )
        
        await callback.message.edit_text(media_request_text)
        await state.set_state(UserStates.waiting_for_media)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in request_media: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "attach_media_no")
async def skip_media(callback: CallbackQuery, state: FSMContext):
    """Skip media attachment"""
    try:
        await safe_remove_inline_call(callback)
        await ask_for_location(callback, state)
    except Exception as e:
        logger.error(f"Error in skip_media: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(UserStates.waiting_for_media), F.photo | F.video)
async def process_media(message: Message, state: FSMContext):
    """Process media attachment"""
    try:
        await safe_remove_inline(message)
        # Save media file_id
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
        
        location_question_text = (
            "Geolokatsiya yubormoqchimisiz?"
            if lang == 'uz' else
            "Хотите отправить геолокацию?"
        )
        
        await message.answer(
            location_question_text,
            reply_markup=geolocation_keyboard(lang)
        )
        await state.set_state(UserStates.asking_for_location)
        
    except Exception as e:
        logger.error(f"Error in process_media: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

async def ask_for_location(callback_or_message, state: FSMContext):
    """Ask for location"""
    try:
        if hasattr(callback_or_message, 'message'):
            await safe_remove_inline_call(callback_or_message)
        else:
            await safe_remove_inline(callback_or_message)
        user_id = callback_or_message.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        
        location_question_text = (
            "Geolokatsiya yubormoqchimisiz?"
            if lang == 'uz' else
            "Хотите отправить геолокацию?"
        )
        
        if hasattr(callback_or_message, 'message'):
            # It's a callback query
            await callback_or_message.message.edit_text(
                location_question_text,
                reply_markup=geolocation_keyboard(lang)
            )
            await callback_or_message.answer()
        else:
            # It's a message
            await callback_or_message.answer(
                location_question_text,
                reply_markup=geolocation_keyboard(lang)
            )
        
        await state.set_state(UserStates.asking_for_location)
        
    except Exception as e:
        logger.error(f"Error in ask_for_location: {str(e)}", exc_info=True)

@router.callback_query(F.data == "send_location_yes")
async def request_location(callback: CallbackQuery, state: FSMContext):
    """Request location"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        location_request_text = (
            "Geolokatsiyani yuboring:"
            if lang == 'uz' else
            "Отправьте геолокацию:"
        )
        
        await callback.message.edit_text(location_request_text)
        await state.set_state(UserStates.waiting_for_location)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in request_location: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "send_location_no")
async def skip_location(callback: CallbackQuery, state: FSMContext):
    """Skip location"""
    try:
        await safe_remove_inline_call(callback)
        await show_order_confirmation(callback, state)
    except Exception as e:
        logger.error(f"Error in skip_location: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(UserStates.waiting_for_location), F.location)
async def process_location(message: Message, state: FSMContext):
    """Process location"""
    try:
        await safe_remove_inline(message)
        location = message.location
        await state.update_data(
            latitude=location.latitude,
            longitude=location.longitude
        )
        
        await show_order_confirmation(message, state)
        
    except Exception as e:
        logger.error(f"Error in process_location: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

async def show_order_confirmation(message_or_callback, state: FSMContext):
    """Show order confirmation"""
    try:
        if hasattr(message_or_callback, 'message'):
            await safe_remove_inline_call(message_or_callback)
        else:
            await safe_remove_inline(message_or_callback)
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        
        data = await state.get_data()
        
        # Format order summary
        order_type_text = "Jismoniy shaxs" if data['order_type'] == 'b2c' else "Yuridik shaxs"
        if lang == 'ru':
            order_type_text = "Физическое лицо" if data['order_type'] == 'b2c' else "Юридическое лицо"
        
        summary_text = (
            f"📋 Buyurtma xulosasi:\n\n"
            f"👤 Tur: {order_type_text}\n"
            f"📝 Tavsif: {data['description']}\n"
            f"📍 Manzil: {data['address']}\n"
            if lang == 'uz' else
            f"📋 Сводка заказа:\n\n"
            f"👤 Тип: {order_type_text}\n"
            f"📝 Описание: {data['description']}\n"
            f"📍 Адрес: {data['address']}\n"
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
            # It's a callback query
            await message_or_callback.message.edit_text(
                summary_text,
                reply_markup=confirmation_keyboard(lang)
            )
            await message_or_callback.answer()
        else:
            # It's a message
            await message_or_callback.answer(
                summary_text,
                reply_markup=confirmation_keyboard(lang)
            )
        
        await state.set_state(UserStates.confirming_order)
        
    except Exception as e:
        logger.error(f"Error in show_order_confirmation: {str(e)}", exc_info=True)

@router.callback_query(F.data == "confirm_zayavka")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Confirm and create order"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        # Create zayavka
        zayavka_data = {
            'user_id': user['id'],
            'zayavka_type': data['order_type'],
            'description': data['description'],
            'address': data['address'],
            'media': data.get('media_id'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'status': 'new'
        }
        
        zayavka_id = await create_zayavka(zayavka_data)
        
        if zayavka_id:
            success_text = (
                f"✅ Buyurtma muvaffaqiyatli yaratildi!\n"
                f"Buyurtma raqami: #{zayavka_id}\n\n"
                f"Tez orada siz bilan bog'lanamiz."
                if lang == 'uz' else
                f"✅ Заказ успешно создан!\n"
                f"Номер заказа: #{zayavka_id}\n\n"
                f"Мы скоро с вами свяжемся."
            )
            
            await callback.message.edit_text(success_text)
            
            # Send notification to managers
            await notify_managers_new_order(zayavka_id, user, zayavka_data)
            
            logger.info(f"New order created by client {user['id']}: #{zayavka_id}")
        else:
            error_text = (
                "Buyurtma yaratishda xatolik yuz berdi."
                if lang == 'uz' else
                "Произошла ошибка при создании заказа."
            )
            await callback.message.edit_text(error_text)
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in confirm_order: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

async def notify_managers_new_order(zayavka_id: int, user: dict, zayavka_data: dict):
    """Notify managers about new order"""
    try:
        from database.queries import get_managers_telegram_ids
        from loader import bot
        
        managers = await get_managers_telegram_ids()
        
        for manager in managers:
            try:
                manager_lang = manager.get('language', 'uz')
                
                order_type_text = "Jismoniy shaxs" if zayavka_data['zayavka_type'] == 'b2c' else "Yuridik shaxs"
                if manager_lang == 'ru':
                    order_type_text = "Физическое лицо" if zayavka_data['zayavka_type'] == 'b2c' else "Юридическое лицо"
                
                notification_text = (
                    f"🆕 Yangi buyurtma!\n\n"
                    f"📋 Buyurtma #{zayavka_id}\n"
                    f"👤 Mijoz: {user['full_name']}\n"
                    f"📞 Telefon: {user.get('phone_number', 'Noma\'lum')}\n"
                    f"🏷️ Tur: {order_type_text}\n"
                    f"📝 Tavsif: {zayavka_data['description']}\n"
                    f"📍 Manzil: {zayavka_data['address']}\n"
                    f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    if manager_lang == 'uz' else
                    f"🆕 Новый заказ!\n\n"
                    f"📋 Заказ #{zayavka_id}\n"
                    f"👤 Клиент: {user['full_name']}\n"
                    f"📞 Телефон: {user.get('phone_number', 'Неизвестно')}\n"
                    f"🏷️ Тип: {order_type_text}\n"
                    f"📝 Описание: {zayavka_data['description']}\n"
                    f"📍 Адрес: {zayavka_data['address']}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                
                await bot.send_message(
                    chat_id=manager['telegram_id'],
                    text=notification_text
                )
                
                # Send media if attached
                if zayavka_data.get('media'):
                    await bot.send_photo(
                        chat_id=manager['telegram_id'],
                        photo=zayavka_data['media']
                    )
                
                # Send location if attached
                if zayavka_data.get('latitude'):
                    await bot.send_location(
                        chat_id=manager['telegram_id'],
                        latitude=zayavka_data['latitude'],
                        longitude=zayavka_data['longitude']
                    )
                    
            except Exception as e:
                logger.error(f"Error sending notification to manager {manager['id']}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in notify_managers_new_order: {str(e)}")

@router.callback_query(F.data == "resend_zayavka")
async def resend_order(callback: CallbackQuery, state: FSMContext):
    """Resend order (restart process)"""
    try:
        await state.clear()
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        order_type_text = (
            "Buyurtma turini tanlang:"
            if lang == 'uz' else
            "Выберите тип заказа:"
        )
        
        await callback.message.edit_text(
            order_type_text,
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.set_state(UserStates.selecting_order_type)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in resend_order: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["📋 Mening buyurtmalarim", "📋 Мои заказы"]))
async def my_orders(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            return
        if user.get('role') == 'technician':
            await message.answer("Sizda mijoz huquqi yo'q. Iltimos, o'z menyu bo'limingizdan foydalaning." if lang == "uz" else "У вас нет доступа к этому заказу. Пожалуйста, используйте свой раздел меню.")
            return
        lang = user.get('language', 'uz')
        data = await state.get_data()
        page = data.get('page', 1)
        per_page = 5
        offset = (page - 1) * per_page
        conn = await db_manager.get_connection()
        try:
            total = await conn.fetchval('SELECT COUNT(*) FROM zayavki WHERE user_id = $1', user['id'])
            if total == 0:
                await message.answer("Buyurtmalar yo'q." if lang == "uz" else "Заказов нет.")
                return
            zayavki = await conn.fetch(
                '''SELECT * FROM zayavki 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC
                   LIMIT $2 OFFSET $3''',
                user['id'], per_page, offset
            )
            from database.queries import get_zayavka_solutions
            for zayavka in zayavki:
                if lang == 'uz':
                    order_info = (
                        f"🆔 Buyurtma ID: <b>{zayavka['id']}</b>\n"
                        f"👤 Mijoz: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Telefon: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Manzil: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Tavsif: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}" + "</b>"
                    )
                else:
                    order_info = (
                        f"🆔 ID заказа: <b>{zayavka['id']}</b>\n"
                        f"👤 Клиент: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Телефон: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Адрес: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Описание: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}" + "</b>"
                    )
                # Fetch and append technician solutions as a single block
                solutions = await get_zayavka_solutions(zayavka['id'])
                if solutions:
                    if lang == 'uz':
                        solutions_block = "\n<b>🔧 Texnik(lar) yechimlari:</b>"
                    else:
                        solutions_block = "\n<b>🔧 Решения техника(ов):</b>"
                    for sol in solutions:
                        if lang == 'uz':
                            solution_text = (
                                f"\n\n🛠 Yechim: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Texnik: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Sana: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}" + "</b>"
                            )
                        else:
                            solution_text = (
                                f"\n\n🛠 Решение: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Техник: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Дата: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}" + "</b>"
                            )
                        solutions_block += solution_text
                    order_info += solutions_block
                if zayavka.get('media'):
                    await message.answer_photo(
                        photo=zayavka['media'],
                        caption=order_info
                    )
                else:
                    await message.answer(order_info)
            if total > per_page:
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ " + ("Orqaga" if lang == "uz" else "Назад"),
                        callback_data=f"orders_page_{page-1}"
                    ))
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text=("Oldinga" if lang == "uz" else "Вперёд") + " ➡️",
                        callback_data=f"orders_page_{page+1}"
                    ))
                if buttons:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                    await message.answer(
                        f"{page*per_page if page*per_page <= total else total}/{total}",
                        reply_markup=keyboard
                    )
        finally:
            await db_manager.pool.release(conn)
    except Exception as e:
        logger.error(f"Buyurtmalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(F.text.in_(["📞 Operator bilan bog'lanish", "📞 Связаться с оператором"]))
async def contact_operator(message: Message, state: FSMContext):
    """Contact operator"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        contact_info_text = (
            "📞 Operator bilan bog'lanish:\n\n"
            "📱 Telefon: +998 90 123 45 67\n"
            "🕐 Ish vaqti: 9:00 - 18:00\n"
            "📧 Email: support@company.uz\n\n"
            "Yoki botda xabar qoldiring, tez orada javob beramiz."
            if lang == 'uz' else
            "📞 Связь с оператором:\n\n"
            "📱 Телефон: +998 90 123 45 67\n"
            "🕐 Рабочее время: 9:00 - 18:00\n"
            "📧 Email: support@company.uz\n\n"
            "Или оставьте сообщение в боте, мы скоро ответим."
        )
        
        await message.answer(contact_info_text)
        
    except Exception as e:
        logger.error(f"Error in contact_operator: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.message(F.text.in_(["👤 Profil", "👤 Профиль"]))
async def client_profile_handler(message: Message, state: FSMContext):
    """Handle client profile"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return
        
        lang = user.get('language', 'uz')
        profile_text = "Profil bo'limi" if lang == 'uz' else "Раздел профиля"
        
        await message.answer(
            profile_text,
            reply_markup=get_client_profile_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in client profile: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data == "client_update_contact")
async def client_update_contact_handler(callback: CallbackQuery, state: FSMContext):
    """Update client contact"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        contact_text = "Yangi kontaktni ulashing:" if lang == 'uz' else "Поделитесь новым контактом:"
        await callback.message.edit_text(contact_text)
        await state.set_state(UserStates.updating_contact)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in client update contact: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(UserStates.updating_contact), F.contact)
async def process_contact_update(message: Message, state: FSMContext):
    """Process contact update"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        # Update contact
        from database.queries import update_user_phone
        await update_user_phone(user['id'], message.contact.phone_number)
        
        success_text = "Kontakt muvaffaqiyatli yangilandi!" if lang == 'uz' else "Контакт успешно обновлен!"
        await message.answer(success_text)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing contact update: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data == "client_update_address")
async def client_update_address_handler(callback: CallbackQuery, state: FSMContext):
    """Update client address"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        address_text = "Yangi manzilni kiriting:" if lang == 'uz' else "Введите новый адрес:"
        await callback.message.edit_text(address_text)
        await state.set_state(UserStates.updating_address)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in client update address: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(StateFilter(UserStates.updating_address))
async def process_address_update(message: Message, state: FSMContext):
    """Process address update"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        # Update address
        await update_client_info(user['id'], {'address': message.text})
        
        success_text = "Manzil muvaffaqiyatli yangilandi!" if lang == 'uz' else "Адрес успешно обновлен!"
        await message.answer(success_text)
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error processing address update: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data == "client_view_info")
async def client_view_info_handler(callback: CallbackQuery, state: FSMContext):
    """View client information"""
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        client_info = await get_client_info(user['id'])
        
        if client_info:
            info_text = (
                f"👤 Shaxsiy ma'lumotlar:\n\n"
                f"📝 Ism: {client_info.get('full_name', 'Kiritilmagan')}\n"
                f"📞 Telefon: {client_info.get('phone_number', 'Kiritilmagan')}\n"
                f"📍 Manzil: {client_info.get('address', 'Kiritilmagan')}\n"
                f"🌐 Til: {'O\'zbekcha' if client_info.get('language') == 'uz' else 'Русский'}\n"
                f"📅 Ro'yxatdan o'tgan: {client_info.get('created_at', 'Noma\'lum')}"
                if lang == 'uz' else
                f"👤 Личная информация:\n\n"
                f"📝 Имя: {client_info.get('full_name', 'Не указано')}\n"
                f"📞 Телефон: {client_info.get('phone_number', 'Не указано')}\n"
                f"📍 Адрес: {client_info.get('address', 'Не указано')}\n"
                f"🌐 Язык: {'Узбекский' if client_info.get('language') == 'uz' else 'Русский'}\n"
                f"📅 Зарегистрирован: {client_info.get('created_at', 'Неизвестно')}"
            )
        else:
            info_text = "Ma'lumotlar topilmadi" if lang == 'uz' else "Информация не найдена"
        
        await callback.message.edit_text(info_text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing client info: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["❓ Yordam", "❓ Помощь"]))
async def client_help_handler(message: Message, state: FSMContext):
    """Client uchun yordam bo'limi"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
        await message.answer(
            help_text,
            reply_markup=get_client_help_menu(lang)
        )
    except Exception as e:
        logger.error(f"Error in client help: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data == "client_faq")
async def client_faq_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        faq_text = (
            "❓ Tez-tez so'raladigan savollar:\n\n"
            "1. Qanday buyurtma beraman?\n"
            "   - 'Yangi buyurtma' tugmasini bosing\n\n"
            "2. Buyurtmam qachon bajariladi?\n"
            "   - Odatda 1-3 ish kuni ichida\n\n"
            "3. Narxlar qanday?\n"
            "   - Operator siz bilan bog'lanib narxni aytadi\n\n"
            "4. Bekor qilsam bo'ladimi?\n"
            "   - Ha, operator orqali bekor qilishingiz mumkin"
            if lang == 'uz' else
            "❓ Часто задаваемые вопросы:\n\n"
            "1. Как сделать заказ?\n"
            "   - Нажмите кнопку 'Новый заказ'\n\n"
            "2. Когда выполнят мой заказ?\n"
            "   - Обычно в течение 1-3 рабочих дней\n\n"
            "3. Какие цены?\n"
            "   - Оператор свяжется с вами и сообщит цену\n\n"
            "4. Можно ли отменить?\n"
            "   - Да, можете отменить через оператора"
        )
        await callback.message.edit_text(faq_text, reply_markup=get_client_help_back_inline(lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in client FAQ: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "client_how_to_order")
async def client_how_to_order_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        guide_text = (
            "📝 Qanday buyurtma berish:\n\n"
            "1️⃣ 'Yangi buyurtma' tugmasini bosing\n"
            "2️⃣ Buyurtma turini tanlang\n"
            "3️⃣ Tavsifni kiriting\n"
            "4️⃣ Manzilni kiriting\n"
            "5️⃣ Rasm biriktiring (ixtiyoriy)\n"
            "6️⃣ Geolokatsiya yuboring (ixtiyoriy)\n"
            "7️⃣ Buyurtmani tasdiqlang\n\n"
            "✅ Tayyor! Operator siz bilan bog'lanadi."
            if lang == 'uz' else
            "📝 Как сделать заказ:\n\n"
            "1️⃣ Нажмите 'Новый заказ'\n"
            "2️⃣ Выберите тип заказа\n"
            "3️⃣ Введите описание\n"
            "4️⃣ Введите адрес\n"
            "5️⃣ Прикрепите фото (по желанию)\n"
            "6️⃣ Отправьте геолокацию (по желанию)\n"
            "7️⃣ Подтвердите заказ\n\n"
            "✅ Готово! Оператор свяжется с вами."
        )
        await callback.message.edit_text(guide_text, reply_markup=get_client_help_back_inline(lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in how to order guide: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "client_track_order")
async def client_track_order_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        track_text = (
            "📍 Buyurtmani kuzatish:\n\n"
            "Buyurtmangiz holatini bilish uchun:\n"
            "• 'Mening buyurtmalarim' bo'limiga o'ting\n"
            "• Yoki operator bilan bog'laning\n\n"
            "Buyurtma holatlari:\n"
            "🆕 Yangi - qabul qilindi\n"
            "✅ Tasdiqlangan - ishga olingan\n"
            "⏳ Jarayonda - bajarilmoqda\n"
            "✅ Bajarilgan - tugallangan"
            if lang == 'uz' else
            "📍 Отслеживание заказа:\n\n"
            "Чтобы узнать статус заказа:\n"
            "• Перейдите в 'Мои заказы'\n"
            "• Или свяжитесь с оператором\n\n"
            "Статусы заказа:\n"
            "🆕 Новый - принят\n"
            "✅ Подтвержден - взят в работу\n"
            "⏳ В процессе - выполняется\n"
            "✅ Выполнен - завершен"
        )
        await callback.message.edit_text(track_text, reply_markup=get_client_help_back_inline(lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in track order: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "client_contact_support")
async def client_contact_support_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        support_text = (
            "📞 Qo'llab-quvvatlash xizmati:\n\n"
            "📱 Telefon: +998 90 123 45 67\n"
            "📧 Email: support@company.uz\n"
            "💬 Telegram: @support_bot\n\n"
            "🕐 Ish vaqti:\n"
            "Dushanba - Juma: 9:00 - 18:00\n"
            "Shanba: 9:00 - 14:00\n"
            "Yakshanba: Dam olish kuni\n\n"
            "Yoki botda xabar qoldiring!"
            if lang == 'uz' else
            "📞 Служба поддержки:\n\n"
            "📱 Телефон: +998 90 123 45 67\n"
            "📧 Email: support@company.uz\n"
            "💬 Telegram: @support_bot\n\n"
            "🕐 Рабочее время:\n"
            "Понедельник - Пятница: 9:00 - 18:00\n"
            "Суббота: 9:00 - 14:00\n"
            "Воскресенье: Выходной\n\n"
            "Или оставьте сообщение в боте!"
        )
        await callback.message.edit_text(support_text, reply_markup=get_client_help_back_inline(lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in contact support: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.callback_query(F.data == "client_back_help")
async def client_back_help_handler(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        help_text = "Yordam bo'limi" if lang == 'uz' else "Раздел помощи"
        await callback.message.edit_text(help_text, reply_markup=get_client_help_menu(lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in client back help: {str(e)}", exc_info=True)
        await callback.answer("Xatolik yuz berdi")

@router.message(F.text.in_(["🌐 Til o'zgartirish", "🌐 Изменить язык"]))
async def client_change_language(message: Message, state: FSMContext):
    """Change language for client"""
    try:
        await safe_remove_inline(message)
        success = await show_language_selection(message, "client", state)
        if not success:
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)
    except Exception as e:
        logger.error(f"Error in client change language: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("client_lang_"))
async def process_client_language_change(callback: CallbackQuery, state: FSMContext):
    """Process client language change"""
    try:
        await safe_remove_inline_call(callback)
        await process_language_change(
            call=callback,
            role="client",
            get_main_keyboard_func=get_main_menu_keyboard,
            state=state
        )
        await state.set_state(UserStates.main_menu)
    except Exception as e:
        logger.error(f"Client tilni o'zgartirishda xatolik: {str(e)}")
        lang = await get_user_lang(callback.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await callback.message.answer(error_text)
        await callback.answer()

@router.message(F.text.in_(["🏠 Asosiy menyu", "🏠 Главное меню"]))
async def main_menu_handler(message: Message, state: FSMContext):
    """Handle main menu button"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi.")
            return
        
        lang = user.get('language', 'uz')
        main_menu_text = (
            "Asosiy menyu. Kerakli bo'limni tanlang."
            if lang == 'uz' else
            "Главное меню. Выберите нужный раздел."
        )
        
        await message.answer(
            main_menu_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in main menu handler: {str(e)}", exc_info=True)
        lang = await get_user_lang(message.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

# Handle unknown messages
@router.message()
async def handle_unknown_message(message: Message, state: FSMContext):
    """Handle unknown messages"""
    try:
        await safe_remove_inline(message)
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            return
        
        lang = user.get('language', 'uz')
        unknown_text = (
            "Noma'lum buyruq. Menyudan tanlang."
            if lang == 'uz' else
            "Неизвестная команда. Выберите из меню."
        )
        
        await message.answer(
            unknown_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in handle_unknown_message: {str(e)}", exc_info=True)

@router.callback_query(lambda c: c.data.startswith('orders_page_'))
async def process_orders_page(callback: CallbackQuery, state: FSMContext):
    try:
        await safe_remove_inline_call(callback)
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            return
        lang = user.get('language', 'uz')
        page = int(callback.data.split('_')[-1])
        await state.update_data(page=page)
        per_page = 5
        offset = (page - 1) * per_page
        conn = await db_manager.get_connection()
        try:
            total = await conn.fetchval('SELECT COUNT(*) FROM zayavki WHERE user_id = $1', user['id'])
            if total == 0:
                await callback.message.answer("Buyurtmalar yo'q." if lang == "uz" else "Заказов нет.")
                return
            zayavki = await conn.fetch(
                '''SELECT * FROM zayavki 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC
                   LIMIT $2 OFFSET $3''',
                user['id'], per_page, offset
            )
            await callback.message.delete()
            from database.queries import get_zayavka_solutions
            for zayavka in zayavki:
                if lang == 'uz':
                    order_info = (
                        f"🆔 Buyurtma ID: <b>{zayavka['id']}</b>\n"
                        f"👤 Mijoz: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Telefon: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Manzil: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Tavsif: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}" + "</b>"
                    )
                else:
                    order_info = (
                        f"🆔 ID заказа: <b>{zayavka['id']}</b>\n"
                        f"👤 Клиент: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Телефон: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Адрес: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Описание: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}" + "</b>"
                    )
                # Fetch and append technician solutions as a single block
                solutions = await get_zayavka_solutions(zayavka['id'])
                if solutions:
                    if lang == 'uz':
                        solutions_block = "\n<b>🔧 Texnik(lar) yechimlari:</b>"
                    else:
                        solutions_block = "\n<b>🔧 Решения техника(ов):</b>"
                    for sol in solutions:
                        if lang == 'uz':
                            solution_text = (
                                f"\n\n🛠 Yechim: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Texnik: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Sana: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}" + "</b>"
                            )
                        else:
                            solution_text = (
                                f"\n\n🛠 Решение: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Техник: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Дата: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}" + "</b>"
                            )
                        solutions_block += solution_text
                    order_info += solutions_block
                if zayavka.get('media'):
                    await callback.message.answer_photo(
                        photo=zayavka['media'],
                        caption=order_info
                    )
                else:
                    await callback.message.answer(order_info)
            if total > per_page:
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ " + ("Orqaga" if lang == "uz" else "Назад"),
                        callback_data=f"orders_page_{page-1}"
                    ))
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text=("Oldinga" if lang == "uz" else "Вперёд") + " ➡️",
                        callback_data=f"orders_page_{page+1}"
                    ))
                if buttons:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
                    await callback.message.answer(
                        f"{page*per_page if page*per_page <= total else total}/{total}",
                        reply_markup=keyboard
                    )
        finally:
            await db_manager.pool.release(conn)
        await callback.answer()
    except Exception as e:
        logger.error(f"Sahifalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
        await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
