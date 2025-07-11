from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
from loader import bot
from utils.inline_cleanup import answer_and_cleanup, safe_delete_message
from keyboards.manager_buttons import (
    zayavka_type_keyboard, media_attachment_keyboard, geolocation_keyboard,
    confirmation_keyboard, get_manager_main_keyboard, get_manager_view_applications_keyboard
)
from database.base_queries import get_user_by_telegram_id
from states.manager_states import ManagerApplicationStates
from database.base_queries import get_user_lang, create_zayavka
from utils.logger import setup_logger
from utils.role_router import get_role_router
from database.technician_queries import get_available_technicians
from database.manager_queries import assign_technician_to_order
from keyboards.manager_buttons import get_assign_technician_keyboard

def get_manager_applications_router():
    logger = setup_logger('bot.manager.applications')
    router = get_role_router("manager")

    # safe_delete_message chaqiruvlarini olib tashlaymiz, foydalanuvchi yuborgan xabarlar o'chmaydi
    @router.message(F.text.in_(['🆕 Texnik xizmat', '🆕 Техническая поддержка']))
    async def create_service_order(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        lang = user.get('language', 'uz')
        await message.answer("Klient ismini kiriting:" if lang == 'uz' else "Введите имя клиента:")
        await state.update_data(order_type='service')
        await state.set_state(ManagerApplicationStates.creating_application_client_name)

    @router.message(F.text.in_(['🔌 Ulanish uchun ariza', '🔌 Заявка на подключение']))
    async def create_connection_order(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'manager':
            return
        lang = user.get('language', 'uz')
        await message.answer("Klient ismini kiriting:" if lang == 'uz' else "Введите имя клиента:")
        await state.update_data(order_type='connection')
        await state.set_state(ManagerApplicationStates.creating_application_client_name)

    @router.message(StateFilter(ManagerApplicationStates.creating_application_client_name))
    async def get_client_name(message: Message, state: FSMContext):
        await state.update_data(client_name=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer("Klient manzilini kiriting:" if lang == 'uz' else "Введите адрес клиента:")
        await state.set_state(ManagerApplicationStates.creating_application_address)

    @router.message(StateFilter(ManagerApplicationStates.creating_application_address))
    async def get_client_address(message: Message, state: FSMContext):
        await state.update_data(client_address=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer("Klient telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона клиента:")
        await state.set_state(ManagerApplicationStates.creating_application_phone)

    @router.message(StateFilter(ManagerApplicationStates.creating_application_phone))
    async def get_client_phone(message: Message, state: FSMContext):
        await state.update_data(client_phone=message.text)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            "Ulanish turini tanlang:" if lang == 'uz' else "Выберите тип подключения:",
            reply_markup=zayavka_type_keyboard(lang)
        )
        await state.set_state(ManagerApplicationStates.selecting_connection_type)

    # Ulanish uchun ariza uchun muammo tavsifi bosqichi olib tashlandi!
    # Tarif tanlash, media, geo, tasdiqlash bosqichlari quyidagicha:

    @router.callback_query(F.data.startswith("manager_zayavka_type_"), StateFilter(ManagerApplicationStates.selecting_connection_type))
    async def select_connection_type(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        connection_type = callback.data.split("_")[-1]
        await state.update_data(connection_type=connection_type)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        await callback.message.answer(
            "Tariflardan birini tanlang:" if lang == 'uz' else "Выберите один из тарифов:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Standard", callback_data="tariff_standard"),
                        InlineKeyboardButton(text="Yangi", callback_data="tariff_new")
                    ]
                ]
            )
        )
        await state.set_state(ManagerApplicationStates.selecting_tariff)

    @router.callback_query(F.data.in_(["tariff_standard", "tariff_new"]), StateFilter(ManagerApplicationStates.selecting_tariff))
    async def select_tariff(callback: CallbackQuery, state: FSMContext):
        await answer_and_cleanup(callback, cleanup_after=True)
        tariff = "Standard" if callback.data == "tariff_standard" else "Yangi"
        await state.update_data(selected_tariff=tariff)
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        await callback.message.answer(
            "Foto yoki video yuborasizmi?" if lang == 'uz' else "Отправите фото или видео?",
            reply_markup=media_attachment_keyboard(lang)
        )
        await state.set_state(ManagerApplicationStates.creating_application_media)

    @router.callback_query(F.data.in_(["manager_attach_media_yes", "manager_attach_media_no"]), StateFilter(ManagerApplicationStates.creating_application_media))
    async def ask_for_media(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_reply_markup(reply_markup=None)
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "manager_attach_media_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Foto yoki videoni yuboring:" if lang == 'uz' else "Отправьте фото или видео:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(ManagerApplicationStates.waiting_for_media)
        else:
            await ask_for_address(callback, state)

    @router.message(StateFilter(ManagerApplicationStates.waiting_for_media), F.photo | F.video)
    async def process_media(message: Message, state: FSMContext):
        media_file_id = message.photo[-1].file_id if message.photo else message.video.file_id
        await state.update_data(media=media_file_id)
        await ask_for_address(message, state)

    async def ask_for_address(message_or_callback, state: FSMContext):
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        if hasattr(message_or_callback, "message"):
            sent_message = await message_or_callback.message.answer(
                "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
                reply_markup=geolocation_keyboard(lang)
            )
        else:
            sent_message = await message_or_callback.answer(
                "Geolokatsiya yuborasizmi?" if lang == 'uz' else "Отправите геолокацию?",
                reply_markup=geolocation_keyboard(lang)
            )
        await state.update_data(last_message_id=sent_message.message_id)
        await state.set_state(ManagerApplicationStates.asking_for_location)

    @router.callback_query(F.data.in_(["manager_send_location_yes", "manager_send_location_no"]), StateFilter(ManagerApplicationStates.asking_for_location))
    async def ask_for_geo(callback: CallbackQuery, state: FSMContext):
        await callback.message.edit_reply_markup(reply_markup=None)
        await answer_and_cleanup(callback, cleanup_after=True)
        if callback.data == "manager_send_location_yes":
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            sent_message = await callback.message.answer(
                "Geolokatsiyani yuboring:" if lang == 'uz' else "Отправьте геолокацию:",
            )
            await state.update_data(last_message_id=sent_message.message_id)
            await state.set_state(ManagerApplicationStates.waiting_for_location)
        else:
            await show_connection_confirmation(callback, state)

    @router.message(StateFilter(ManagerApplicationStates.waiting_for_location), F.location)
    async def get_geo(message: Message, state: FSMContext):
        await state.update_data(geo=message.location)
        await show_connection_confirmation(message, state)

    async def show_connection_confirmation(message_or_callback, state: FSMContext):
        data = await state.get_data()
        user_id = message_or_callback.from_user.id
        user = await get_user_by_telegram_id(user_id)
        lang = user.get('language', 'uz')
        text = (
            f"👤 <b>Klient ismi:</b> {data.get('client_name', '-')}\n"
            f"🏠 <b>Klient manzili:</b> {data.get('client_address', '-')}\n"
            f"📞 <b>Klient telefoni:</b> {data.get('client_phone', '-')}\n"
            f"🔌 <b>Ulanish turi:</b> {data.get('connection_type', '-')}\n"
            f"💳 <b>Tarif:</b> {data.get('selected_tariff', '-')}\n"
            f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if data.get('geo') else '❌ Yuborilmagan'}\n"
            f"🖼 <b>Media:</b> {'✅ Yuborilgan' if data.get('media') else '❌ Yuborilmagan'}\n"
            f"<b>Ariza menejer tomonidan yaratildi</b>"
        )
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
        await state.set_state(ManagerApplicationStates.confirming_application)

    @router.callback_query(F.data == "confirm_zayavka", StateFilter(ManagerApplicationStates.confirming_application))
    async def confirm_connection_order(callback: CallbackQuery, state: FSMContext):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await answer_and_cleanup(callback, cleanup_after=True)
        data = await state.get_data()
        user = await get_user_by_telegram_id(callback.from_user.id)
        order_id = await create_zayavka(
            user_id=user['id'],
            description=f"Ulanish turi: {data.get('connection_type', '-')} Tarif: {data.get('selected_tariff', '-')}",
            address=data.get('client_address'),
            phone_number=data.get('client_phone'),
            media=data.get('media'),
            zayavka_type='connection',
            latitude=data.get('geo').latitude if data.get('geo') else None,
            longitude=data.get('geo').longitude if data.get('geo') else None,
            created_by=user['id'],
            created_by_role='manager',
            client_name=data.get('client_name'),
        )
        await bot.send_message(callback.from_user.id, "✅ Ariza qabul qilindi! Operatorlar tez orada bog'lanadi.")
        if order_id:
            group_msg = (
                f"🔌 <b>Yangi ulanish arizasi</b>\n"
                f"👤 <b>Klient ismi:</b> {data.get('client_name', '-')}\n"
                f"🏠 <b>Klient manzili:</b> {data.get('client_address', '-')}\n"
                f"📞 <b>Klient telefoni:</b> {data.get('client_phone', '-')}\n"
                f"🔌 <b>Ulanish turi:</b> {data.get('connection_type', '-')}\n"
                f"💳 <b>Tarif:</b> {data.get('selected_tariff', '-')}\n"
                f"📍 <b>Geolokatsiya:</b> {'✅ Yuborilgan' if data.get('geo') else '❌ Yuborilmagan'}\n"
                f"🖼 <b>Media:</b> {'✅ Yuborilgan' if data.get('media') else '❌ Yuborilmagan'}\n"
                f"<b>Ariza menejer tomonidan yaratildi</b>\n"
                f"⏰ <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            if data.get('media'):
                await bot.send_photo(ZAYAVKA_GROUP_ID, data['media'], caption=group_msg, parse_mode='HTML')
            else:
                await bot.send_message(ZAYAVKA_GROUP_ID, group_msg, parse_mode='HTML')
        await state.clear()
        await callback.answer()

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
            await state.set_state(ManagerApplicationStates.creating_application_type)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in resend_application: {str(e)}", exc_info=True)
            await callback.answer("Xatolik yuz berdi")

    @router.message(F.text.in_(["📋 Arizalarni ko'rish", "📋 Просмотр заявок"]))
    async def view_applications(message: Message, state: FSMContext):
        """Manager: Show view options for applications (all, by ID, back)"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        await message.answer(
            "Arizalarni ko'rish usulini tanlang:" if lang == 'uz' else 'Выберите способ просмотра заявок:',
            reply_markup=get_manager_view_applications_keyboard(lang)
        )
        await state.clear()

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
                await bot.db.release(conn)
        except Exception as e:
            logger.error(f"Error in manager_apps_page_callback: {str(e)}", exc_info=True)
            error_text = "❗️ Xatolik yuz berdi" if lang == 'uz' else "❗️ Произошла ошибка"
            await callback.message.answer(error_text)

    @router.message(F.text.in_(["📋 Hammasini ko'rish", "📋 Посмотреть все"]))
    async def manager_view_all_applications(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        page = 1
        per_page = 5
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
            start = offset + 1
            end = offset + len(apps)
            header = f"📋 Ko'rsatilmoqda: {start}-{end} / {total}" if lang == 'uz' else f"📋 Показывается: {start}-{end} / {total}"
            text = header + "\n\n"
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
                text += info + "\n-----------------------------\n"
            total_pages = (total + per_page - 1) // per_page
            buttons = []
            if total > per_page:
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
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
            sent = await message.answer(text, parse_mode='HTML', reply_markup=reply_markup)
            await state.update_data(last_apps_message_id=sent.message_id)
        finally:
            await bot.db.release(conn)
        await state.set_state(ManagerApplicationStates.viewing_applications)

    @router.message(F.text.in_(["🔎 ID bo'yicha ko'rish", "🔎 По ID"]))
    async def manager_view_by_id_start(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        await message.answer(
            "Ariza raqamini kiriting (masalan, 123 yoki #123):" if lang == 'uz' else "Введите номер заявки (например, 123 или #123):"
        )
        await state.set_state(ManagerApplicationStates.application_details)

    @router.message(StateFilter(ManagerApplicationStates.application_details))
    async def manager_view_by_id_process(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        app_id_text = message.text.strip().replace('#', '')
        if not app_id_text.isdigit():
            await message.answer("❗️ Noto'g'ri format. Faqat raqam kiriting." if lang == 'uz' else "❗️ Неверный формат. Введите только число.")
            return
        app_id = int(app_id_text)
        conn = await bot.db.acquire()
        try:
            app = await conn.fetchrow(
                '''SELECT z.*, u.full_name as client_name, u.phone_number as client_phone, t.full_name as technician_name
                   FROM zayavki z
                   LEFT JOIN users u ON z.user_id = u.id
                   LEFT JOIN users t ON z.assigned_to = t.id
                   WHERE z.id = $1''',
                app_id
            )
            if not app:
                await message.answer(f"❌ #{app_id} raqamli ariza topilmadi." if lang == 'uz' else f"❌ Заявка #{app_id} не найдена.")
                return
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
            await message.answer(info, parse_mode='HTML')
        finally:
            await bot.db.release(conn)
        await state.clear()

    @router.message(F.text.in_(["👨‍🔧 Texnik biriktirish", "👨‍🔧 Назначить техника"]))
    async def manager_assign_technician_start(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        await message.answer(
            "Ariza raqamini kiriting (masalan, 123 yoki #123):" if lang == 'uz' else "Введите номер заявки (например, 123 или #123):"
        )
        await state.set_state(ManagerApplicationStates.entering_application_id_for_assignment)

    @router.message(StateFilter(ManagerApplicationStates.entering_application_id_for_assignment))
    async def manager_assign_technician_id(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        app_id_text = message.text.strip().replace('#', '')
        if not app_id_text.isdigit():
            await message.answer("❗️ Noto'g'ri format. Faqat raqam kiriting." if lang == 'uz' else "❗️ Неверный формат. Введите только число.")
            return
        app_id = int(app_id_text)
        conn = await bot.db.acquire()
        try:
            app = await conn.fetchrow(
                '''SELECT z.*, u.full_name as client_name, u.phone_number as client_phone
                   FROM zayavki z
                   LEFT JOIN users u ON z.user_id = u.id
                   WHERE z.id = $1''',
                app_id
            )
            if not app:
                await message.answer(f"❌ #{app_id} raqamli ariza topilmadi." if lang == 'uz' else f"❌ Заявка #{app_id} не найдена.")
                return
            # Ariza info
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
                info = (
                    f"📄 <b>Zayavka raqami:</b> #{app['id']} {status_emoji}\n"
                    f"👤 <b>Mijoz:</b> {app.get('client_name') or 'Noma\'lum'}\n"
                    f"📞 <b>Telefon:</b> {app.get('client_phone') or '-'}\n"
                    f"📍 <b>Manzil:</b> {app.get('address') or '-'}\n"
                    f"📝 <b>Tavsif:</b> {app.get('description') or '-'}\n"
                    f"📊 <b>Status:</b> {status_text}\n"
                    f"🕒 <b>Yaratilgan:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                )
            else:
                status_text = {
                    'new': '🆕 Новая',
                    'confirmed': '✅ Подтверждена',
                    'in_progress': '⏳ В процессе',
                    'completed': '🏁 Выполнена',
                    'cancelled': '❌ Отменена'
                }.get(app['status'], app['status'])
                info = (
                    f"📄 <b>Номер заявки:</b> #{app['id']} {status_emoji}\n"
                    f"👤 <b>Клиент:</b> {app.get('client_name') or 'Неизвестно'}\n"
                    f"📞 <b>Телефон:</b> {app.get('client_phone') or '-'}\n"
                    f"📍 <b>Адрес:</b> {app.get('address') or '-'}\n"
                    f"📝 <b>Описание:</b> {app.get('description') or '-'}\n"
                    f"📊 <b>Статус:</b> {status_text}\n"
                    f"🕒 <b>Создано:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                )
            # Texniklar ro'yxati
            technicians = await get_available_technicians(conn)
            if not technicians:
                await message.answer("❗️ Texniklar topilmadi." if lang == 'uz' else "❗️ Нет доступных техников.")
                return
            await message.answer(
                info,
                parse_mode='HTML',
                reply_markup=get_assign_technician_keyboard(app_id, technicians, lang)
            )
        finally:
            await bot.db.release(conn)
        await state.clear()

    @router.callback_query(lambda c: c.data.startswith('manager_assign_zayavka_'))
    async def manager_assign_technician_callback(callback: CallbackQuery, state: FSMContext):
        # callback_data: manager_assign_zayavka_{app_id}_{tech_id}
        parts = callback.data.split('_')
        app_id = int(parts[3])
        tech_id = int(parts[4])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        conn = await bot.db.acquire()
        try:
            success = await assign_technician_to_order(app_id, tech_id, bot.db)
            if success:
                app = await conn.fetchrow(
                    '''SELECT z.*, u.full_name as client_name, u.phone_number as client_phone, t.full_name as technician_name
                       FROM zayavki z
                       LEFT JOIN users u ON z.user_id = u.id
                       LEFT JOIN users t ON z.assigned_to = t.id
                       WHERE z.id = $1''',
                    app_id
                )
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
                    info = (
                        f"✅ <b>Texnik biriktirildi!</b>\n"
                        f"📄 <b>Zayavka raqami:</b> #{app['id']} {status_emoji}\n"
                        f"👤 <b>Mijoz:</b> {app.get('client_name') or 'Noma\'lum'}\n"
                        f"📞 <b>Telefon:</b> {app.get('client_phone') or '-'}\n"
                        f"📍 <b>Manzil:</b> {app.get('address') or '-'}\n"
                        f"📝 <b>Tavsif:</b> {app.get('description') or '-'}\n"
                        f"📊 <b>Status:</b> {status_text}\n"
                        f"🧑‍🔧 <b>Texnik:</b> {app.get('technician_name') or '-'}\n"
                        f"🕒 <b>Yaratilgan:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                    )
                else:
                    status_text = {
                        'new': '🆕 Новая',
                        'confirmed': '✅ Подтверждена',
                        'in_progress': '⏳ В процессе',
                        'completed': '🏁 Выполнена',
                        'cancelled': '❌ Отменена'
                    }.get(app['status'], app['status'])
                    info = (
                        f"✅ <b>Техник назначен!</b>\n"
                        f"📄 <b>Номер заявки:</b> #{app['id']} {status_emoji}\n"
                        f"👤 <b>Клиент:</b> {app.get('client_name') or 'Неизвестно'}\n"
                        f"📞 <b>Телефон:</b> {app.get('client_phone') or '-'}\n"
                        f"📍 <b>Адрес:</b> {app.get('address') or '-'}\n"
                        f"📝 <b>Описание:</b> {app.get('description') or '-'}\n"
                        f"📊 <b>Статус:</b> {status_text}\n"
                        f"🧑‍🔧 <b>Техник:</b> {app.get('technician_name') or '-'}\n"
                        f"🕒 <b>Создано:</b> {app.get('created_at').strftime('%d.%m.%Y %H:%M') if app.get('created_at') else '-'}\n"
                    )
                await callback.message.edit_text(info, parse_mode='HTML')
            else:
                await callback.message.answer("❗️ Texnik biriktirishda xatolik." if lang == 'uz' else "❗️ Ошибка при назначении техника.")
        finally:
            await bot.db.release(conn)
        await callback.answer()

    @router.callback_query(F.data == "manager_confirm_zayavka", StateFilter(ManagerApplicationStates.confirming_application))
    async def confirm_connection_order(callback: CallbackQuery, state: FSMContext):
        """Confirm and create connection order"""
        try:
            await answer_and_cleanup(callback, cleanup_after=True)
            
            user = await get_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            data = await state.get_data()
            
            # Create order
            order_data = {
                'user_id': user['id'],
                'zayavka_type': 'connection',
                'description': data.get('description'),
                'address': data.get('address'),
                'phone_number': data.get('phone_number'),
                'status': 'new',
                'created_by_role': 'manager',
                'created_by': user['id'],
                'client_name': data.get('client_name'),
                'connection_type': data.get('connection_type'),
                'arif_photo': data.get('arif_photo')
            }
            
            order_id = await create_zayavka(order_data)
            if order_id:
                success_text = (
                    f"✅ Ariza muvaffaqiyatli yaratildi. Ariza ID: {order_id}"
                    if lang == 'uz' else
                    f"✅ Заявка успешно создана. ID заявки: {order_id}"
                )
                
                await callback.message.edit_text(success_text)
                logger.info(f"Connection order #{order_id} created by manager {user['id']}")
                
                # Send to group using client's format
                group_message = format_group_zayavka_message(
                    order_type='connection',
                    public_id=order_id,
                    user=user,
                    phone=data.get('phone_number'),
                    address=data.get('address'),
                    description=data.get('description'),
                    media=data.get('arif_photo')
                )
                
                # Add manager info
                group_message += f"\n👤 <b>Ariza yaratuvchi:</b> {user.get('full_name', '-') if user else '-'}"
                
                if data.get('arif_photo'):
                    await bot.send_photo(
                        ZAYAVKA_GROUP_ID,
                        photo=data['arif_photo'],
                        caption=group_message,
                        parse_mode="HTML"
                    )
                else:
                    await bot.send_message(
                        ZAYAVKA_GROUP_ID,
                        group_message,
                        parse_mode="HTML"
                    )
            else:
                error_text = "❌ Ariza yaratishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при создании заявки."
                await callback.message.edit_text(error_text)
            
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in confirm_connection_order: {str(e)}", exc_info=True)
            await callback.answer("❌ Xatolik yuz berdi", show_alert=True)

    return router
