from aiogram import Router
from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from keyboards.client_buttons import (
    get_contact_keyboard, zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard, get_main_menu_keyboard
)
from states.user_states import UserStates
from database.client_queries import (
    get_user_zayavki,
    get_zayavka_solutions
)
from database.base_queries import get_user_by_telegram_id, create_zayavka, get_user_lang
from utils.logger import setup_logger
from utils.validators import validate_address
from utils.inline_cleanup import answer_and_cleanup
from loader import bot, ZAYAVKA_GROUP_ID, inline_message_manager

def get_client_order_router():
    logger = setup_logger('bot.client')
    router = Router()

    @router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
    async def new_order(message: Message, state: FSMContext):
        """Start new order process"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                await message.answer("Foydalanuvchi topilmadi.")
                return
            lang = user.get('language', 'uz')
            # Do NOT check for phone_number here; it should be handled at /start
            order_type_text = (
                "Buyurtma turini tanlang:"
                if lang == 'uz' else
                "Выберите тип заказа:"
            )
            sent_message = await message.answer(
                order_type_text,
                reply_markup=zayavka_type_keyboard(lang)
            )
            await state.update_data(last_message_id=sent_message.message_id)  # Message_id saqlash
            await state.set_state(UserStates.selecting_order_type)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"Error in new_order: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("zayavka_type_"))
    async def select_order_type(callback: CallbackQuery, state: FSMContext):
        """Buyurtma turini tanlash"""
        try:
            # Old message ni tozalash
            await answer_and_cleanup(callback, cleanup_after=True)
            
            # Yangi xabar yuborish
            order_type = callback.data.split("_")[2]  # b2b yoki b2c
            await state.update_data(order_type=order_type)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            description_text = (
                "📝 <b>Buyurtma tavsifini kiriting:</b>"
                if lang == 'uz' else
                "📝 <b>Введите описание заказа:</b>"
            )
            
            sent_message = await callback.message.edit_text(
                description_text, 
                parse_mode='HTML',
                reply_markup=None  # Old inline keyboard ni tozalash
            )
            
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(UserStates.entering_description)
            
            # Yangi xabar ni tracking qilish
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"select_order_type da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.answer(error_text, show_alert=True)

    @router.message(StateFilter(UserStates.entering_description))
    async def get_order_description(message: Message, state: FSMContext):
        """Buyurtma tavsifini olish"""
        try:
            # Old message ni tozalash
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                try:
                    await message.bot.edit_message_reply_markup(
                        chat_id=message.chat.id,
                        message_id=last_message_id,
                        reply_markup=None
                    )
                except Exception as e:
                    logger.debug(f"Old message cleanup error: {str(e)}")
            
            # Yangi ma'lumotlarni saqlash
            await state.update_data(description=message.text)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            address_text = (
                "📍 <b>Manzilni kiriting:</b>"
                if lang == 'uz' else
                "📍 <b>Введите адрес:</b>"
            )
            
            # Yangi xabar yuborish
            sent_message = await message.answer(address_text, parse_mode='HTML')
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(UserStates.entering_address)
            
            # Yangi xabar ni tracking qilish
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"get_order_description da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text, reply_markup=get_main_menu_keyboard(lang))

    @router.message(StateFilter(UserStates.entering_address))
    async def get_order_address(message: Message, state: FSMContext):
        """Buyurtma manzilini olish"""
        try:
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            address = message.text.strip()
            
            # Manzilni tekshirish
            if not validate_address(address):
                user = await get_user_by_telegram_id(message.from_user.id)
                lang = user.get('language', 'uz')
                invalid_address_text = (
                    "Noto'g'ri manzil. Iltimos, to'liq manzilni kiriting."
                    if lang == 'uz' else
                    "Неверный адрес. Пожалуйста, введите полный адрес."
                )
                sent_message = await message.answer(invalid_address_text)
                await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
                return
            
            await state.update_data(address=address)
            
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            media_question_text = (
                "📎 <b>Rasm yoki video biriktirmoqchimisiz?</b>"
                if lang == 'uz' else
                "📎 <b>Хотите прикрепить фото или видео?</b>"
            )
            
            sent_message = await message.answer(
                media_question_text,
                reply_markup=media_attachment_keyboard(lang),
                parse_mode='HTML'
            )
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.asking_for_media)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"get_order_address da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data == "attach_media_yes")
    async def request_media(callback: CallbackQuery, state: FSMContext):
        """Media biriktirishni so'rash"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            media_request_text = (
                "Rasm yoki videoni yuboring:"
                if lang == 'uz' else
                "Отправьте фото или видео:"
            )
            
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            sent_message = await callback.message.edit_text(media_request_text)
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.waiting_for_media)
            inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"request_media da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "attach_media_no")
    async def skip_media(callback: CallbackQuery, state: FSMContext):
        """Media biriktirishni o'tkazib yuborish"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            await ask_for_location(callback, state)
        except Exception as e:
            logger.error(f"skip_media da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(UserStates.waiting_for_media), F.photo | F.video)
    async def process_media(message: Message, state: FSMContext):
        """Media biriktirishni qayta ishlash"""
        try:
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            # Media file_id ni saqlash
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
                "📍 <b>Geolokatsiya yubormoqchimisiz?</b>"
                if lang == 'uz' else
                "📍 <b>Хотите отправить геолокацию?</b>"
            )
            
            sent_message = await message.answer(
                location_question_text,
                reply_markup=geolocation_keyboard(lang),
                parse_mode='HTML'
            )
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.asking_for_location)
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"process_media da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def ask_for_location(callback_or_message, state: FSMContext):
        """Geolokatsiya so'rash"""
        try:
            if hasattr(callback_or_message, 'message'):
                await answer_and_cleanup(callback_or_message, cleanup_after=True)
            else:
                data = await state.get_data()
                last_message_id = data.get('last_message_id')
                if last_message_id:
                    await callback_or_message.bot.edit_message_reply_markup(
                        chat_id=callback_or_message.chat.id,
                        message_id=last_message_id,
                        reply_markup=None
                    )
            
            user_id = callback_or_message.from_user.id
            user = await get_user_by_telegram_id(user_id)
            lang = user.get('language', 'uz')
            
            location_question_text = (
                "📍 <b>Geolokatsiya yubormoqchimisiz?</b>"
                if lang == 'uz' else
                "📍 <b>Хотите отправить геолокацию?</b>"
            )
            
            if hasattr(callback_or_message, 'message'):
                sent_message = await callback_or_message.message.edit_text(
                    location_question_text,
                    reply_markup=geolocation_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                sent_message = await callback_or_message.answer(
                    location_question_text,
                    reply_markup=geolocation_keyboard(lang),
                    parse_mode='HTML'
                )
            
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.asking_for_location)
            inline_message_manager.track(callback_or_message.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"ask_for_location da xatolik: {str(e)}", exc_info=True)

    @router.callback_query(F.data == "send_location_yes")
    async def request_location(callback: CallbackQuery, state: FSMContext):
        """Geolokatsiya so'rash"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            location_request_text = (
                "Geolokatsiyani yuboring:"
                if lang == 'uz' else
                "Отправьте геолокацию:"
            )
            
            sent_message = await callback.message.edit_text(location_request_text)
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.waiting_for_location)
            inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"request_location da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "send_location_no")
    async def skip_location(callback: CallbackQuery, state: FSMContext):
        """Geolokatsiyani o'tkazib yuborish"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            await show_order_confirmation(callback, state)
        except Exception as e:
            logger.error(f"skip_location da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(StateFilter(UserStates.waiting_for_location), F.location)
    async def process_location(message: Message, state: FSMContext):
        """Geolokatsiyani qayta ishlash"""
        try:
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await message.bot.edit_message_reply_markup(
                    chat_id=message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            location = message.location
            await state.update_data(
                latitude=location.latitude,
                longitude=location.longitude
            )
            
            await show_order_confirmation(message, state)
            
        except Exception as e:
            logger.error(f"process_location da xatolik: {str(e)}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    async def show_order_confirmation(message_or_callback, state: FSMContext):
        """Buyurtma tasdiqlanishini ko'rsatish"""
        try:
            if hasattr(message_or_callback, 'message'):
                await answer_and_cleanup(message_or_callback, cleanup_after=True)
            else:
                data = await state.get_data()
                last_message_id = data.get('last_message_id')
                if last_message_id:
                    await message_or_callback.bot.edit_message_reply_markup(
                        chat_id=message_or_callback.chat.id,
                        message_id=last_message_id,
                        reply_markup=None
                    )
            
            user_id = message_or_callback.from_user.id
            user = await get_user_by_telegram_id(user_id)
            lang = user.get('language', 'uz')
            data = await state.get_data()

            # Buyurtma xulosasini formatlash (improved, with more details and emojis)
            order_type_text = "👤 Jismoniy shaxs" if data['order_type'] == 'b2c' else "🏢 Yuridik shaxs"
            if lang == 'ru':
                order_type_text = "👤 Физическое лицо" if data['order_type'] == 'b2c' else "🏢 Юридическое лицо"
            summary_text = (
                ("<b>📋 Buyurtma xulosasi</b>\n"
                 "━━━━━━━━━━━━━━━━━━━━\n"
                 f"{order_type_text}\n"
                 f"📝 <b>Tavsif:</b> {data.get('description', '-')}\n"
                 f"📍 <b>Manzil:</b> {data.get('address', '-')}\n"
                 f"👤 <b>Ism:</b> {user.get('full_name', '-') if user else '-'}\n"
                 f"📞 <b>Telefon:</b> {user.get('phone_number', '-') if user else '-'}\n"
                 f"🕒 <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                ) if lang == 'uz' else
                ("<b>📋 Сводка заказа</b>\n"
                 "━━━━━━━━━━━━━━━━━━━━\n"
                 f"{order_type_text}\n"
                 f"📝 <b>Описание:</b> {data.get('description', '-')}\n"
                 f"📍 <b>Адрес:</b> {data.get('address', '-')}\n"
                 f"👤 <b>Имя:</b> {user.get('full_name', '-') if user else '-'}\n"
                 f"📞 <b>Телефон:</b> {user.get('phone_number', '-') if user else '-'}\n"
                 f"🕒 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                )
            )
            if data.get('media_id'):
                media_text = "📎 <b>Rasm/video biriktirilgan</b>" if lang == 'uz' else "📎 <b>Фото/видео прикреплено</b>"
                summary_text += f"\n{media_text}"
            if data.get('latitude'):
                location_text = "📍 <b>Geolokatsiya biriktirilgan</b>" if lang == 'uz' else "📍 <b>Геолокация прикреплена</b>"
                summary_text += f"\n{location_text}"
            summary_text += "\n━━━━━━━━━━━━━━━━━━━━"
            confirm_text = "\n\n✅ <b>Tasdiqlaysizmi?</b>" if lang == 'uz' else "\n\n✅ <b>Подтверждаете?</b>"
            summary_text += confirm_text

            if hasattr(message_or_callback, 'message'):
                sent_message = await message_or_callback.message.edit_text(
                    summary_text,
                    reply_markup=confirmation_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                sent_message = await message_or_callback.answer(
                    summary_text,
                    reply_markup=confirmation_keyboard(lang),
                    parse_mode='HTML'
                )
            
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.confirming_order)
            inline_message_manager.track(message_or_callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"show_order_confirmation da xatolik: {str(e)}", exc_info=True)

    @router.callback_query(F.data == "confirm_zayavka")
    async def confirm_order(callback: CallbackQuery, state: FSMContext):
        """Buyurtmani tasdiqlash va yaratish"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            data = await state.get_data()
            
            # Zayavka yaratish
            zayavka_data = {
                'user_id': user['id'],
                'zayavka_type': data['order_type'],
                'description': data['description'],
                'address': data['address'],
                'media': data.get('media_id'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }
            
            zayavka_id = await create_zayavka(**zayavka_data)
            
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
                data = await state.get_data()
                last_message_id = data.get('last_message_id')
                if last_message_id:
                    await callback.bot.edit_message_reply_markup(
                        chat_id=callback.message.chat.id,
                        message_id=last_message_id,
                        reply_markup=None
                    )
                
                await callback.message.edit_text(success_text)

                # GROUP NOTIFICATION LOGIC (exactly as in previous_code)
                group_lang = lang
                order_type_text = "Jismoniy shaxs" if data['order_type'] == 'b2c' else "Yuridik shaxs"
                if group_lang == 'ru':
                    order_type_text = "Физическое лицо" if data['order_type'] == 'b2c' else "Юридическое лицо"
                group_text = (
                    f"🆕 Yangi buyurtma!\n\n"
                    f"📋 Buyurtma #{zayavka_id}\n"
                    f"👤 Mijoz: {user.get('full_name', '-') if user else '-'}\n"
                    f"📞 Telefon: {user.get('phone_number', 'Noma\'lum') if user else 'Noma\'lum'}\n"
                    f"🏷️ Tur: {order_type_text}\n"
                    f"📝 Tavsif: {data.get('description', '-')}\n"
                    f"📍 Manzil: {data.get('address', '-')}\n"
                    f"⏰ Vaqt: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                    if group_lang == 'uz' else
                    f"🆕 Новый заказ!\n\n"
                    f"📋 Заказ #{zayavka_id}\n"
                    f"👤 Клиент: {user.get('full_name', '-') if user else '-'}\n"
                    f"📞 Телефон: {user.get('phone_number', 'Неизвестно') if user else 'Неизвестно'}\n"
                    f"🏷️ Тип: {order_type_text}\n"
                    f"📝 Описание: {data.get('description', '-')}\n"
                    f"📍 Адрес: {data.get('address', '-')}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await bot.send_message(
                    chat_id=ZAYAVKA_GROUP_ID,
                    text=group_text
                )
                # Send media if attached
                if data.get('media_id'):
                    await bot.send_photo(
                        chat_id=ZAYAVKA_GROUP_ID,
                        photo=data['media_id']
                    )
                # Send location if attached
                if data.get('latitude'):
                    await bot.send_location(
                        chat_id=ZAYAVKA_GROUP_ID,
                        latitude=data['latitude'],
                        longitude=data['longitude']
                    )
                # END GROUP NOTIFICATION

                logger.info(f"Mijoz {user['id']} tomonidan yangi buyurtma yaratildi: #{zayavka_id}")
            else:
                error_text = (
                    "Buyurtma yaratishda xatolik yuz berdi."
                    if lang == 'uz' else
                    "Произошла ошибка при создании заказа."
                )
                await callback.message.edit_text(error_text)
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"confirm_order da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.callback_query(F.data == "resend_zayavka")
    async def resend_order(callback: CallbackQuery, state: FSMContext):
        """Buyurtmani qayta yuborish (jarayonni qayta boshlash)"""
        try:
            await state.clear()
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            order_type_text = (
                "📦 <b>Buyurtma turini tanlang:</b>"
                if lang == 'uz' else
                "📦 <b>Выберите тип заказа:</b>"
            )
            
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            if last_message_id:
                await callback.bot.edit_message_reply_markup(
                    chat_id=callback.message.chat.id,
                    message_id=last_message_id,
                    reply_markup=None
                )
            
            sent_message = await callback.message.edit_text(
                order_type_text,
                reply_markup=zayavka_type_keyboard(lang),
                parse_mode='HTML'
            )
            await state.update_data(last_message_id=sent_message.message_id)  # Yangi message_id saqlash
            await state.set_state(UserStates.selecting_order_type)
            inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        except Exception as e:
            logger.error(f"resend_order da xatolik: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(F.text.in_(["📋 Mening buyurtmalarim", "📋 Мои заказы"]))
    async def my_orders(message: Message, state: FSMContext):
        """Mijozning buyurtmalarini ko'rsatish"""
        try:
            user = await get_user_by_telegram_id(message.from_user.id)
            if not user:
                lang = "uz"
                await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
                return
            if user.get('role') == 'technician':
                lang = user.get('language', 'uz')
                await message.answer("Sizda mijoz huquqi yo'q. Iltimos, o'z menyu bo'limingizdan foydalaning." if lang == "uz" else "У вас нет доступа к этому заказу. Пожалуйста, используйте свой раздел меню.")
                return
            lang = user.get('language', 'uz')
            data = await state.get_data()
            page = data.get('page', 1)
            per_page = 5
            offset = (page - 1) * per_page
            # Use bot.db.acquire() for connection acquisition
            async with bot.db.acquire() as conn:
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
                        await message.answer(order_info, parse_mode='HTML')
        except Exception as e:
            logger.error(f"my_orders: Buyurtmalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
            await message.answer("Buyurtmalarni ko'rsatishda xatolik yuz berdi.")

    @router.callback_query(lambda c: c.data.startswith('orders_page_'))
    async def process_orders_page(callback: CallbackQuery, state: FSMContext):
        """Buyurtmalar sahifalarini qayta ishlash"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            user = await get_user_by_telegram_id(callback.from_user.id)
            if not user:
                lang = "uz"
                await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
                return
            
            lang = user.get('language', 'uz')
            page = int(callback.data.split('_')[-1])
            await state.update_data(page=page)
            per_page = 5
            offset = (page - 1) * per_page
            
            conn = await bot.db.acquire()
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
                
                # Eski sahifadagi tugmalarni tozalash
                data = await state.get_data()
                last_message_id = data.get('last_message_id')
                if last_message_id:
                    try:
                        await callback.bot.edit_message_reply_markup(
                            chat_id=callback.message.chat.id,
                            message_id=last_message_id,
                            reply_markup=None
                        )
                    except Exception:
                        pass  # Xabar o'chirilgan bo'lishi mumkin, xatoni e'tiborsiz qoldiramiz
                
                new_last_message_id = None
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
                    
                    # Texnik yechimlarini olish va bitta blok sifatida qo'shish
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
                        sent_message = await callback.message.answer_photo(
                            photo=zayavka['media'],
                            caption=order_info
                        )
                    else:
                        sent_message = await callback.message.answer(order_info, parse_mode='HTML')
                    # Faqat oxirgi yuborilgan xabarni last_message_id sifatida saqlaymiz
                    new_last_message_id = sent_message.message_id
                
                # Sahifalash tugmalari
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
                        sent_message = await callback.message.answer(
                            f"{page*per_page if page*per_page <= total else total}/{total}",
                            reply_markup=keyboard
                        )
                        new_last_message_id = sent_message.message_id
                # Yangi last_message_id ni saqlaymiz
                if new_last_message_id:
                    await state.update_data(last_message_id=new_last_message_id)
            finally:
                await bot.db.release(conn)
            await callback.answer()
        except Exception as e:
            logger.error(f"Sahifalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
            lang = "uz"
            await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

    return router