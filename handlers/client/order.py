from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from keyboards.client_buttons import (
    get_contact_keyboard, zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard, get_main_menu_keyboard
)
from states.client_states import OrderStates, ConnectionOrderStates
from aiogram.fsm.state import StatesGroup, State
from database.client_queries import (
    get_user_zayavki,
    get_zayavka_solutions
)
from database.base_queries import get_user_by_telegram_id, create_zayavka, get_user_lang
from utils.logger import setup_logger
from utils.validators import validate_address
from utils.inline_cleanup import answer_and_cleanup
from loader import bot, ZAYAVKA_GROUP_ID, inline_message_manager
from utils.role_router import get_role_router
from database.manager_queries import get_users_by_role
from config import ZAYAVKA_GROUP_ID

def format_group_zayavka_message(order_type, public_id, user, phone, address, description, tariff=None, abonent_type=None, abonent_id=None, geo=None, media=None):
    if order_type == 'service':
        title = '🛠️ <b>Yangi texnik xizmat arizasi</b>'
        type_line = '🛠️ <b>Ariza turi:</b> Texnik xizmat'
    else:
        title = '🔌 <b>Yangi ulanish arizasi</b>'
        type_line = '🔌 <b>Ariza turi:</b> Ulanish'
    abonent_block = ''
    if abonent_type or abonent_id:
        abonent_block = f"\n👤 <b>Abonent turi:</b> {abonent_type or '-'}\n🆔 <b>Abonent ID:</b> {abonent_id or '-'}"
    tariff_block = f"\n💳 <b>Tarif:</b> {tariff}" if tariff else ''
    geo_block = f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if geo else '❌ Yuborilmagan'}"
    media_block = f"🖼 <b>Media:</b> {'✅ Yuborilgan' if media else '❌ Yuborilmagan'}"
    msg = (
        f"{title}\n"
        f"{type_line}\n"
        f"🆔 <b>ID:</b> {public_id or '-'}"
        f"\n👤 <b>Foydalanuvchi:</b> {user.get('full_name', '-') if user else '-'}"
        f"\n📞 <b>Telefon:</b> {phone or '-'}"
        f"\n🏠 <b>Manzil:</b> {address or '-'}"
        f"\n📝 <b>Tavsif:</b> {description or '-'}"
        f"{tariff_block}"
        f"{abonent_block}"
        f"\n{geo_block}"
        f"\n{media_block}"
        f"\n⏰ <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    return msg

def get_client_order_router():
    logger = setup_logger('bot.client')
    router = get_role_router("client")

    @router.message(F.text.in_(["🆕 Texnik xizmat", "🆕 Техническая поддержка"]))
    async def new_service_request(message: Message, state: FSMContext):
        """Texnik xizmat uchun ariza jarayonini boshlash"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Abonent turini tanlang:" if lang == 'uz' else "Выберите тип абонента:",
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.selecting_order_type)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.startswith("zayavka_type_"), StateFilter(OrderStates.selecting_order_type))
    async def select_abonent_type(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        abonent_type = callback.data.split("_")[-1]  # b2b yoki b2c
        await state.update_data(abonent_type=abonent_type)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await callback.message.answer(
            "Abonent ID raqamini kiriting:" if lang == 'uz' else "Введите ID абонента:",
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.waiting_for_contact)
        await inline_message_manager.track(callback.from_user.id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.waiting_for_contact))
    async def get_abonent_id(message: Message, state: FSMContext):
        await state.update_data(abonent_id=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Muammo tavsifini kiriting:" if lang == 'uz' else "Опишите проблему:",
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.entering_description)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.entering_description))
    async def get_service_description(message: Message, state: FSMContext):
        await state.update_data(description=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Foto yoki video yuborasizmi?" if lang == 'uz' else "Отправите фото или видео?",
            reply_markup=media_attachment_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.asking_for_media)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.in_(["attach_media_yes", "attach_media_no"]), StateFilter(OrderStates.asking_for_media))
    async def ask_for_media(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "attach_media_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Foto yoki videoni yuboring:" if lang == 'uz' else "Отправьте фото или видео:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(OrderStates.waiting_for_media)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        else:
            await ask_for_address(callback, state)

    @router.message(StateFilter(OrderStates.waiting_for_media), F.photo | F.video)
    async def process_media(message: Message, state: FSMContext):
        # Save media file ID
        media_file_id = message.photo[-1].file_id if message.photo else message.video.file_id
        await state.update_data(media=media_file_id)
        await ask_for_address(message, state)

    async def ask_for_address(message_or_callback, state: FSMContext):
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        # CallbackQuery bo‘lsa, yangi xabar yuborish uchun .message.answer ishlatamiz
        if hasattr(message_or_callback, "message"):
            sent_message = await message_or_callback.message.answer(
                "Xizmat ko‘rsatiladigan manzilni kiriting:" if lang == 'uz' else "Введите адрес обслуживания:",
            )
        else:
            sent_message = await message_or_callback.answer(
                "Xizmat ko‘rsatiladigan manzilni kiriting:" if lang == 'uz' else "Введите адрес обслуживания:",
            )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.entering_address)
        await inline_message_manager.track(user_id, sent_message.message_id)

    @router.message(StateFilter(OrderStates.entering_address))
    async def get_service_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        sent_message = await message.answer(
            "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
            reply_markup=geolocation_keyboard(lang)
        )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.asking_for_location)
        await inline_message_manager.track(message.from_user.id, sent_message.message_id)

    @router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]), StateFilter(OrderStates.asking_for_location))
    async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "send_location_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(OrderStates.waiting_for_location)
            await inline_message_manager.track(callback.from_user.id, sent_message.message_id)
        else:
            await show_service_confirmation(callback, state)

    @router.message(StateFilter(OrderStates.waiting_for_location), F.location)
    async def get_geo(message: Message, state: FSMContext):
        await state.update_data(geo=message.location)
        await show_service_confirmation(message, state)

    async def show_service_confirmation(message_or_callback, state: FSMContext):
        data = await state.get_data()
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        abonent_type = data.get('abonent_type', '-')
        abonent_id = data.get('abonent_id', '-')
        description = data.get('description', '-')
        address = data.get('address', '-')
        geo = data.get('geo', None)
        media = data.get('media', None)
        text = (
            f"👤 <b>Abonent turi:</b> {abonent_type}\n"
            f"🆔 <b>Abonent ID:</b> {abonent_id}\n"
            f"📝 <b>Muammo tavsifi:</b> {description}\n"
            f"🏠 <b>Manzil:</b> {address}\n"
            f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if geo else '❌ Yuborilmagan'}\n"
            f"🖼 <b>Media:</b> {'✅ Yuborilgan' if media else '❌ Yuborilmagan'}"
        )
        # CallbackQuery bo‘lsa, yangi xabar yuborish uchun .message.answer ishlatamiz
        if hasattr(message_or_callback, "message"):
            sent_message = await message_or_callback.message.answer(
                text,
                parse_mode='HTML',
                reply_markup=confirmation_keyboard(lang)
            )
        else:
            sent_message = await message_or_callback.answer(
                text,
                parse_mode='HTML',
                reply_markup=confirmation_keyboard(lang)
            )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(OrderStates.confirming_order)
        await inline_message_manager.track(user_id, sent_message.message_id)

    @router.callback_query(F.data == "confirm_zayavka", StateFilter(OrderStates.confirming_order))
    async def confirm_service_order(callback: CallbackQuery, state: FSMContext):
        # Remove inline keyboard after press
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await answer_and_cleanup(callback, cleanup_after=True)
        data = await state.get_data()
        user = await get_user_by_telegram_id(callback.from_user.id)
        description = data.get('description', '-')
        address = data.get('address', '-')
        geo = data.get('geo', None)
        media = data.get('media', None)
        abonent_type = data.get('abonent_type', '-')
        abonent_id = data.get('abonent_id', '-')
        zayavka_id, public_id = await create_zayavka(
            user_id=user['id'],
            description=description,
            address=address,
            phone_number=None,
            media=media,
            zayavka_type='service',
            latitude=geo.latitude if geo else None,
            longitude=geo.longitude if geo else None,
            created_by=user['id'],
            created_by_role=user.get('role')
        )
        # Always send confirmation to client as a real message
        user_id = callback.from_user.id
        await bot.send_message(user_id, "✅ Arizangiz qabul qilindi! Operatorlar tez orada siz bilan bog'lanadi.")
        if zayavka_id and public_id:
            group_msg = format_group_zayavka_message(
                order_type='service',
                public_id=public_id,
                user=user,
                phone=user.get('phone_number'),
                address=address,
                description=description,
                abonent_type=abonent_type,
                abonent_id=abonent_id,
                geo=geo,
                media=media
            )
            if ZAYAVKA_GROUP_ID:
                try:
                    if media:
                        await bot.send_photo(ZAYAVKA_GROUP_ID, media, caption=group_msg, parse_mode='HTML')
                    else:
                        await bot.send_message(ZAYAVKA_GROUP_ID, group_msg, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Group notification error: {str(e)}")
            # Send short notification to managers and controllers
            short_msg = f"🛠️ Yangi texnik xizmat arizasi! ID: {public_id}"
            pool = bot.db
            managers = await get_users_by_role(pool, 'manager')
            controllers = await get_users_by_role(pool, 'controller')
            for m in managers + controllers:
                if m.get('telegram_id'):
                    try:
                        await bot.send_message(m['telegram_id'], short_msg)
                    except Exception:
                        pass
        await state.clear()

    @router.callback_query(F.data == "resend_zayavka")
    async def resend_order(callback: CallbackQuery, state: FSMContext):
        # Remove inline keyboard after press
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
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
            await state.set_state(OrderStates.selecting_order_type)
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

    # 🔌 Ulanish uchun ariza tugmasi uchun yangi handler
    @router.message(F.text.in_(["🔌 Ulanish uchun ariza", "🔌 Заявка на подключение"]))
    async def start_connection_order(message: Message, state: FSMContext):
        """Yangi ulanish uchun ariza jarayonini boshlash"""
        lang = (await get_user_by_telegram_id(message.from_user.id)).get('language', 'uz')
        await message.answer(
            "Ulanish turini tanlang:" if lang == 'uz' else "Выберите тип подключения:",
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.set_state(ConnectionOrderStates.selecting_connection_type)

    @router.callback_query(F.data.startswith("zayavka_type_"), StateFilter(ConnectionOrderStates.selecting_connection_type))
    async def select_connection_type(callback: CallbackQuery, state: FSMContext):
        # Remove inline keyboard after press
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        order_type = callback.data.split("_")[-1]  
        await state.update_data(connection_type=order_type)
        lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
        tariff_image_path = "static/image.png" 
        photo = FSInputFile(tariff_image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=("Tariflardan birini tanlang:" if lang == 'uz' else "Выберите один из тарифов:"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Standard", callback_data="tariff_standard"),
                        InlineKeyboardButton(text="Yangi", callback_data="tariff_new")
                    ]
                ]
            )
        )
        await state.set_state(ConnectionOrderStates.selecting_tariff)

    @router.callback_query(F.data.in_(["tariff_standard", "tariff_new"]), StateFilter(ConnectionOrderStates.selecting_tariff))
    async def select_tariff(callback: CallbackQuery, state: FSMContext):
        # Remove inline keyboard after press
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        tariff = "Standard" if callback.data == "tariff_standard" else "Yangi"
        await state.update_data(selected_tariff=tariff)
        lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
        await callback.message.answer(
            "Manzilingizni kiriting:" if lang == 'uz' else "Введите ваш адрес:",
        )
        await state.set_state(ConnectionOrderStates.entering_address)

    @router.message(StateFilter(ConnectionOrderStates.entering_address))
    async def get_connection_address(message: Message, state: FSMContext):
        await state.update_data(address=message.text)
        lang = (await get_user_by_telegram_id(message.from_user.id)).get('language', 'uz')
        await message.answer(
            "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
            reply_markup=geolocation_keyboard(lang)
        )
        await state.set_state(ConnectionOrderStates.asking_for_geo)

    @router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]), StateFilter(ConnectionOrderStates.asking_for_geo))
    async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
        # Remove inline keyboard after press
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        if callback.data == "send_location_yes":
            lang = (await get_user_by_telegram_id(callback.from_user.id)).get('language', 'uz')
            await callback.message.edit_text(
                "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:",
                reply_markup=None
            )
            await state.set_state(ConnectionOrderStates.waiting_for_geo)
        else:
            await finish_connection_order(callback, state, geo=None)

    @router.message(StateFilter(ConnectionOrderStates.waiting_for_geo), F.location)
    async def get_geo(message: Message, state: FSMContext):
        await state.update_data(geo=message.location)
        await finish_connection_order(message, state, geo=message.location)

    async def finish_connection_order(message_or_callback, state: FSMContext, geo=None):
        data = await state.get_data()
        user = await get_user_by_telegram_id(message_or_callback.from_user.id)
        description = data.get('description') or ""
        tariff = data.get('selected_tariff')
        if tariff:
            description = f"{description}\nTarif: {tariff}" if description else f"Tarif: {tariff}"
        zayavka_id, public_id = await create_zayavka(
            user_id=user['id'],
            description=description,
            address=data.get('address'),
            phone_number=None,
            media=None,
            zayavka_type='connection',
            latitude=geo.latitude if geo else None,
            longitude=geo.longitude if geo else None,
            created_by=user['id'],
            created_by_role=user.get('role'),
            tariff=tariff
        )
        # Always send confirmation to client as a real message
        user_id = message_or_callback.from_user.id if hasattr(message_or_callback, 'from_user') else message_or_callback.message.from_user.id
        await bot.send_message(user_id, "✅ Arizangiz qabul qilindi! Operatorlar tez orada siz bilan bog'lanadi.")
        if zayavka_id and public_id:
            group_msg = format_group_zayavka_message(
                order_type='connection',
                public_id=public_id,
                user=user,
                phone=user.get('phone_number'),
                address=data.get('address'),
                description=description,
                tariff=tariff,
                geo=geo,
                media=None
            )
            if ZAYAVKA_GROUP_ID:
                try:
                    await bot.send_message(ZAYAVKA_GROUP_ID, group_msg, parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Group notification error: {str(e)}")
            # Send short notification to managers and controllers
            short_msg = f"🔌 Yangi ulanish arizasi! ID: {public_id}"
            pool = bot.db
            managers = await get_users_by_role(pool, 'manager')
            controllers = await get_users_by_role(pool, 'controller')
            for m in managers + controllers:
                if m.get('telegram_id'):
                    try:
                        await bot.send_message(m['telegram_id'], short_msg)
                    except Exception:
                        pass
        await state.clear()

    return router