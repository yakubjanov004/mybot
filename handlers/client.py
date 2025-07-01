from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from typing import Optional, Dict, Any
from database.models import User
from keyboards.client_buttons import (
    get_language_keyboard, get_main_menu_keyboard, get_back_keyboard, get_contact_keyboard,
    zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard
)
from states.user_states import UserStates
from loader import bot
from database.queries import get_user_by_telegram_id, create_user, get_zayavka_solutions, update_user_language, update_user_phone, db_manager
from utils.logger import setup_logger, log_user_action, log_error
from config import config
from handlers.technician import get_task_inline_keyboard
from utils.inline_cleanup import safe_remove_inline, safe_remove_inline_call
from utils.get_lang import get_user_lang
from utils.get_role import get_user_role
from handlers.language import show_language_selection, process_language_change

# Setup dedicated logger for client module
logger = setup_logger('bot.client')

router = Router()

async def get_lang(user_id):
    user = await get_user_by_telegram_id(user_id)
    return user.get('language', 'uz') if user else 'uz'

# --- UNIVERSAL REPLY GUARD ---
MAIN_MENU_BUTTONS = [
    "Yangi buyurtma", "Новый заказ",
    "Mening buyurtmalarim", "Мои заказы", 
    "Operator bilan bog'lanish", "Связаться с оператором",
    "Tilni o'zgartirish", "Изменить язык",
]

# --- END UNIVERSAL REPLY GUARD ---

# --- UNIVERSAL BACK/MAIN MENU HANDLER ---
BACK_MAIN_MENU_TEXTS = [
    "Asosiy menyu",
    "Главное меню"
]

@router.message(F.text.in_(BACK_MAIN_MENU_TEXTS))
async def handle_back_or_main_menu(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    role = await get_user_role(message.from_user.id)
    await state.clear()

    if role == 'client':
        welcome_text = "Xush kelibsiz! Qanday yordam bera olaman?" if lang == "uz" else "Добро пожаловать! Как я могу помочь?"
        await message.answer(
            text=welcome_text,
            reply_markup=get_main_menu_keyboard(lang)
        )
        from states.user_states import UserStates
        await state.set_state(UserStates.main_menu)
    elif role == 'technician':
        await message.answer("Iltimos, /start buyrug'ini ishlatib, o'z menyu bo'limingizga o'ting." if lang == "uz" else "Пожалуйста, используйте команду /start, чтобы перейти в свой раздел меню.")
    elif role == 'admin':
        await message.answer("Iltimos, /start buyrug'ini ishlatib, o'z menyu bo'limingizga o'ting." if lang == "uz" else "Пожалуйста, используйте команду /start, чтобы перейти в свой раздел меню.")
    elif role == 'manager':
        await message.answer("Iltimos, /start buyrug'ini ishlatib, o'z menyu bo'limingizga o'ting." if lang == "uz" else "Пожалуйста, используйте команду /start, чтобы перейти в свой раздел меню.")
    else:
        await message.answer("Bosh menyu." if lang == "uz" else "Главное меню.")

async def get_user_safely(user_id: int) -> Optional[Dict[str, Any]]:
    """Safely get user with error handling"""
    try:
        return await get_user_by_telegram_id(user_id)
    except Exception as e:
        log_error(e, {'context': 'get_user_safely', 'user_id': user_id})
        return None

async def validate_user_role(user: Dict[str, Any], allowed_roles: list) -> bool:
    """Validate user role"""
    if not user:
        return False
    return user.get('role') in allowed_roles

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    return text.strip()[:max_length]

async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for clients"""
    try:
        await state.clear()
        log_user_action(message.from_user.id, "start_command")
        db_user = await get_user_safely(message.from_user.id)
        if db_user:
            await handle_existing_user(message, state, db_user)
        else:
            await handle_new_user(message, state)
    except Exception as e:
        log_error(e, {'context': 'cmd_start', 'user_id': message.from_user.id})
        lang = await get_user_lang(message.from_user.id)
        await safe_remove_inline(message)
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

async def handle_existing_user(message: Message, state: FSMContext, user: Dict[str, Any]):
    """Handle existing user logic"""
    lang = await get_user_lang(message.from_user.id)
    if not user['phone_number']:
        await safe_remove_inline(message)
        text = "Iltimos, kontaktingizni ulashing." if lang == "uz" else "Пожалуйста, предоставьте свой контактный номер."
        await message.answer(
            text,
            reply_markup=get_contact_keyboard(lang)
        )
        await state.set_state(UserStates.waiting_for_phone_number)
    else:
        await safe_remove_inline(message)
        text = "Xush kelibsiz! Qanday yordam bera olaman?" if lang == "uz" else "Добро пожаловать! Как я могу помочь?"
        await message.answer(
            text=text,
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)

async def handle_new_user(message: Message, state: FSMContext):
    """Handle new user registration"""
    try:
        new_user = await create_user(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name or "Unknown",
            role='client'
        )
        log_user_action(message.from_user.id, "user_created", user_id=new_user['id'])
        await state.set_state(UserStates.selecting_language)
        await safe_remove_inline(message)
        text = "Xush kelibsiz! Qanday yordam bera olaman?"
        await message.answer(
            text=text,
            reply_markup=get_language_keyboard()
        )
    except Exception as e:
        log_error(e, {'context': 'handle_new_user', 'telegram_id': message.from_user.id})
        raise

@router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
async def new_order(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
        return
    lang = await get_user_lang(message.from_user.id)
    if message.text == "Orqaga":
        await safe_remove_inline(message)
        await message.answer(
            "Asosiy menyu" if lang == "uz" else "Главное меню",
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return
    await safe_remove_inline(message)
    await message.answer(
        "Iltimos, buyurtmangiz haqida ma'lumot bering:" if lang == "uz" else "Пожалуйста, предоставьте информацию о вашем заказе:",
        reply_markup=get_back_keyboard(lang)
    )
    await message.answer(
        "Zayavka turini tanlang:" if lang == "uz" else "Выберите тип заявки:",
        reply_markup=zayavka_type_keyboard(lang)
    )
    await state.clear()
    await state.set_state(UserStates.choosing_zayavka_type)

@router.callback_query(F.data.in_(["zayavka_type_b2b", "zayavka_type_b2c"]))
async def choose_zayavka_type(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = await get_user_lang(call.from_user.id)
    zayavka_type = "Jismoniy shaxs" if call.data == "zayavka_type_b2b" else "Yuridik shaxs" if lang == "uz" else ("Физическое лицо" if call.data == "zayavka_type_b2b" else "Юридическое лицо")
    await state.update_data(zayavka_type=zayavka_type)
    await call.message.edit_text("Abonent ID ni kiriting:" if lang == "uz" else "Введите ID абонента:", reply_markup=None)
    await state.set_state(UserStates.waiting_for_abonent_id)

@router.message(UserStates.waiting_for_abonent_id)
async def get_abonent_id(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = await get_user_lang(message.from_user.id)

    # Orqaga tugmasi bosilganini tekshirish
    if message.text in ["Orqaga", "Назад"]:
        # Delete previous inline keyboard messages
        async for msg in message.bot.iter_messages(message.chat.id, limit=10):
            if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                await msg.delete()
        await state.clear()
        
        await message.answer(
            "Asosiy menyu" if lang == "uz" else "Главное меню",
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return

    if message.reply_to_message:
        await state.update_data(reply_candidate={
            'text': message.text,
            'state': 'waiting_for_abonent_id',
        })
        await message.answer("Reply received:" if lang == "uz" else "Ответ получен:", reply_markup=get_back_keyboard(lang))
        return

    abonent_id = message.text
    await state.update_data(abonent_id=abonent_id)
    
    await message.answer("Tavsifini kiriting:" if lang == "uz" else "Введите описание:", reply_markup=get_back_keyboard(lang))
    await state.set_state(UserStates.waiting_for_description)

@router.message(UserStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = await get_user_lang(message.from_user.id)
    description = message.text
    await state.update_data(description=description)
    await message.answer("Media yuborishni istaysizmi?" if lang == "uz" else "Хотите отправить медиа?", reply_markup=media_attachment_keyboard(lang))
    await state.set_state(UserStates.asking_for_media)

@router.callback_query(F.data.in_(["attach_media_yes", "attach_media_no"]))
async def ask_for_media(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    
    # Delete the inline keyboard first
    await call.message.delete()
    
    if call.data == "attach_media_yes":
        await call.message.answer("Media yuborishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка при отправке медиа. Пожалуйста, попробуйте еще раз.", reply_markup=get_back_keyboard(lang))
        await state.set_state(UserStates.waiting_for_media)
    else:
        await state.update_data(media=None)
        await call.message.answer("Manzilni kiriting:" if lang == "uz" else "Введите адрес:", reply_markup=get_back_keyboard(lang))
        await state.set_state(UserStates.waiting_for_address)

@router.callback_query(F.data == "back_to_main")
async def handle_back_button(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    
    # Delete previous inline keyboard messages
    async for msg in call.message.bot.iter_messages(call.message.chat.id, limit=10):
        if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
            await msg.delete()
            
    await state.clear()
    await call.message.answer(
        "Asosiy menyu" if lang == "uz" else "Главное меню",
        reply_markup=get_main_menu_keyboard(lang)
    )
    await call.message.delete()
    await state.set_state(UserStates.main_menu)

@router.message(UserStates.waiting_for_media, F.photo | F.document)
async def receive_media(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    await state.update_data(media=file_id)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    await message.answer("Manzilni kiriting:" if lang == "uz" else "Введите адрес:", reply_markup=get_back_keyboard(lang))
    await state.set_state(UserStates.waiting_for_address)

@router.message(UserStates.waiting_for_address)
async def get_address(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = await get_user_lang(message.from_user.id)
    address = message.text.strip()
    if not address or len(address) < 5:
        await message.answer("Iltimos, to'g'ri manzil kiriting." if lang == "uz" else "Пожалуйста, введите правильный адрес.")
        return
    await state.update_data(address=address)
    await message.answer("Geolokatsiya yuborishni istaysizmi?" if lang == "uz" else "Хотите отправить геолокацию?", reply_markup=geolocation_keyboard(lang))
    await state.set_state(UserStates.asking_for_location)

@router.callback_query(F.data.in_(["reply_confirm_yes", "reply_confirm_no"]))
async def handle_reply_confirmation(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    data = await state.get_data()
    reply_candidate = data.get('reply_candidate')
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if not reply_candidate:
        await call.message.answer("No reply found" if lang == "uz" else "Ответ не найден")
        return
    if call.data == "reply_confirm_yes":
        # Qaysi state uchun reply kelganini aniqlash va uni ishlatish
        if reply_candidate['state'] == 'waiting_for_abonent_id':
            await state.update_data(abonent_id=reply_candidate['text'])
            await call.message.answer("Iltimos, buyurtmangiz haqida ma'lumot bering:" if lang == "uz" else "Пожалуйста, предоставьте информацию о вашем заказе:", reply_markup=get_back_keyboard(lang))
            await state.set_state(UserStates.waiting_for_description)
        elif reply_candidate['state'] == 'waiting_for_description':
            await state.update_data(description=reply_candidate['text'])
            await call.message.answer("Media yuborishni istaysizmi?" if lang == "uz" else "Хотите отправить медиа?", reply_markup=media_attachment_keyboard(lang))
            await state.set_state(UserStates.asking_for_media)
        elif reply_candidate['state'] == 'waiting_for_address':
            address = reply_candidate['text'].strip()
            if not address or len(address) < 5:
                await call.message.answer("Iltimos, to'g'ri manzil kiriting." if lang == "uz" else "Пожалуйста, введите правильный адрес.")
                return
            await state.update_data(address=address)
            await call.message.answer("Geolokatsiya yuborishni istaysizmi?" if lang == "uz" else "Хотите отправить геолокацию?", reply_markup=geolocation_keyboard(lang))
            await state.set_state(UserStates.asking_for_location)
        await state.update_data(reply_candidate=None)
    else:
        # Yo'q bosilsa, xabarni qabul qilmaslik va foydalanuvchiga davom etishni aytish
        await call.message.answer("Continue with new message" if lang == "uz" else "Продолжайте с новым сообщением")
        await state.update_data(reply_candidate=None)

@router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]))
async def ask_for_location(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if call.data == "send_location_yes":
        # Show reply keyboard with location request
        location_text = "Geolokatsiya yuborish" if lang == "uz" else "Отправить геолокацию"
        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=location_text, request_location=True)]],
            resize_keyboard=True
        )
        await call.message.delete()
        await call.message.answer(location_text, reply_markup=location_keyboard)
        await state.set_state(UserStates.waiting_for_location)
    else:
        await state.update_data(location=None)
        await call.message.delete()
        await show_order_confirmation(call.message, state, lang)
        await state.set_state(UserStates.confirming_zayavka)

@router.message(UserStates.waiting_for_location, F.location)
async def receive_location(message: Message, state: FSMContext):
    location = f"{message.location.latitude},{message.location.longitude}"
    await state.update_data(location=location)
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    # Remove location keyboard after receiving location
    location_confirmed_text = "Geolokatsiya qabul qilindi." if lang == "uz" else "Геолокация получена."
    await message.answer(location_confirmed_text, reply_markup=get_main_menu_keyboard(lang))
    await show_order_confirmation(message, state, lang)
    await state.set_state(UserStates.confirming_zayavka)

async def show_order_confirmation(message_or_call, state, lang):
    data = await state.get_data()
    # Hardcoded templates for Uzbek and Russian
    confirmation_text_uz = (
        f"📝 Buyurtma tafsilotlari:\n"
        f"📦 Zayavka turi: <b>{data.get('zayavka_type', '-')}</b>\n"
        f"#️⃣ Abonent ID: <b>{data.get('abonent_id', '-')}</b>\n"
        f"📝 Tavsif: <b>{data.get('description', '-')}</b>\n"
        f"📍 Manzil: <b>{data.get('address', '-')}</b>\n"
        f"📎 Media: {'✅' if data.get('media') else '❌'}\n"
        f"🌐 Geolokatsiya: <b>{'✅' if data.get('location') else '❌'}</b>\n"
        f"\nBuyurtmani tasdiqlaysizmi?"
    )
    confirmation_text_ru = (
        f"📝 Детали заказа:\n"
        f"📦 Тип заявки: <b>{data.get('zayavka_type', '-')}</b>\n"
        f"#️⃣ Абонент ID: <b>{data.get('abonent_id', '-')}</b>\n"
        f"📝 Описание: <b>{data.get('description', '-')}</b>\n"
        f"📍 Адрес: <b>{data.get('address', '-')}</b>\n"
        f"📎 Медиа: {'✅' if data.get('media') else '❌'}\n"
        f"🌐 Геолокация: <b>{'✅' if data.get('location') else '❌'}</b>\n"
        f"\nПодтвердить заказ?"
    )
    text = confirmation_text_uz if lang == 'uz' else confirmation_text_ru
    await message_or_call.answer(
        text,
        reply_markup=confirmation_keyboard(lang),
        parse_mode='HTML'
    )

@router.callback_query(F.data == "confirm_zayavka")
async def confirm_zayavka(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    data = await state.get_data()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')

    try:
        async with db_manager.get_connection() as conn:
            db_user = await conn.fetchrow("SELECT id, full_name FROM users WHERE telegram_id = $1", call.from_user.id)
            if not db_user:
                logger.error(f"No user found for telegram_id: {call.from_user.id}")
                await call.message.answer("Foydalanuvchi topilmadi!")
                return

            zayavka = await conn.fetchrow(
                '''INSERT INTO zayavki (user_id, zayavka_type, abonent_id, description, address, media, location, status, created_by_role)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *''',
                db_user['id'],
                data.get("zayavka_type"),
                data.get("abonent_id"),
                data.get("description"),
                data.get("address"),
                data.get("media"),
                data.get("location"),
                'new',
                'client'
            )
            logger.info(f"New zayavka created: {zayavka['id']}")

            user_zayavka_count = await conn.fetchval(
                'SELECT COUNT(*) FROM zayavki WHERE user_id = $1 AND id <= $2',
                db_user['id'], zayavka['id']
            )

            # Prepare texts in both languages
            zayavka_text_uz = (
                f"🆔 Umumiy zayavka ID: <b>{zayavka['id']}</b>\n"
                f"👤 Foydalanuvchi: <b>{db_user['full_name']}</b>\n"
                f"🔢 Sizning zayavka raqamingiz: <b>{user_zayavka_count}</b>\n"
                f"📦 Zayavka turi: <b>{zayavka['zayavka_type']}</b>\n"
                f"#️⃣ Abonent ID: <b>{zayavka['abonent_id']}</b>\n"
                f"📝 Tavsif: <b>{zayavka['description']}</b>\n"
                f"📍 Manzil: <b>{zayavka['address']}</b>\n"
                f"📎 Media: {'✅' if zayavka['media'] else '❌'}\n"
                f"🌐 Geolokatsiya: <b>{zayavka['location'] if zayavka['location'] else '❌'}</b>\n"
                f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}</b>"
            )
            zayavka_text_ru = (
                f"🆔 Общий ID заявки: <b>{zayavka['id']}</b>\n"
                f"👤 Пользователь: <b>{db_user['full_name']}</b>\n"
                f"🔢 Ваш номер заявки: <b>{user_zayavka_count}</b>\n"
                f"📦 Тип заявки: <b>{zayavka['zayavka_type']}</b>\n"
                f"#️⃣ Абонент ID: <b>{zayavka['abonent_id']}</b>\n"
                f"📝 Описание: <b>{zayavka['description']}</b>\n"
                f"📍 Адрес: <b>{zayavka['address']}</b>\n"
                f"📎 Медиа: {'✅' if zayavka['media'] else '❌'}\n"
                f"🌐 Геолокация: <b>{zayavka['location'] if zayavka['location'] else '❌'}</b>\n"
                f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}</b>"
            )

            manager_keyboard_uz = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="👨‍🔧 Technicianga biriktirish",
                    callback_data=f"assign_zayavka_{zayavka['id']}"
                )]
            ])
            manager_keyboard_ru = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="👨‍🔧 Назначить технику",
                    callback_data=f"assign_zayavka_{zayavka['id']}"
                )]
            ])

            # Send to user (in their language)
            user_text = zayavka_text_uz if lang == 'uz' else zayavka_text_ru
            if zayavka['media']:
                await bot.send_photo(
                    chat_id=call.from_user.id,
                    photo=zayavka['media'],
                    caption=user_text,
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    chat_id=call.from_user.id,
                    text=user_text,
                    parse_mode='HTML'
                )

            # Send to group (only in Uzbek)
            if zayavka['media']:
                await bot.send_photo(
                    chat_id=config.ZAYAVKA_GROUP_ID,
                    photo=zayavka['media'],
                    caption=zayavka_text_uz,
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    chat_id=config.ZAYAVKA_GROUP_ID,
                    text=zayavka_text_uz,
                    parse_mode='HTML'
                )

            # Send to all managers in their language (Uzbek or Russian)
            managers = await conn.fetch("SELECT telegram_id, language FROM users WHERE role = 'manager'")
            for manager in managers:
                try:
                    # Menejerning tilini to'g'ri aniqlash
                    manager_lang = manager.get('language')
                    if not manager_lang or manager_lang not in ['uz', 'ru']:
                        manager_lang = 'uz'  # Default o'zbekcha
                    
                    # Menejerning tiliga qarab xabarni tayyorlash
                    if manager_lang == 'uz':
                        manager_text = (
                            f"🆕 Yangi buyurtma!\n"
                            f"🆔 Buyurtma ID: <b>{zayavka['id']}</b>\n"
                            f"👤 Mijoz: <b>{db_user['full_name']}</b>\n"
                            f"#️⃣ Abonent ID: <b>{zayavka['abonent_id']}</b>\n"
                            f"📝 Tavsif: <b>{zayavka['description']}</b>\n"
                            f"📍 Manzil: <b>{zayavka['address']}</b>\n"
                            f"📎 Media: {'✅' if zayavka['media'] else '❌'}\n"
                            f"🌐 Geolokatsiya: <b>{'✅' if zayavka['location'] else '❌'}</b>\n"
                            f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}</b>"
                        )
                        manager_keyboard = manager_keyboard_uz
                    else:
                        manager_text = (
                            f"🆕 Новый заказ!\n"
                            f"🆔 ID заказа: <b>{zayavka['id']}</b>\n"
                            f"👤 Клиент: <b>{db_user['full_name']}</b>\n"
                            f"#️⃣ Абонент ID: <b>{zayavka['abonent_id']}</b>\n"
                            f"📝 Описание: <b>{zayavka['description']}</b>\n"
                            f"📍 Адрес: <b>{zayavka['address']}</b>\n"
                            f"📎 Медиа: {'✅' if zayavka['media'] else '❌'}\n"
                            f"🌐 Геолокация: <b>{'✅' if zayavka['location'] else '❌'}</b>\n"
                            f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}</b>"
                        )
                        manager_keyboard = manager_keyboard_ru

                    if zayavka['media']:
                        await bot.send_photo(
                            chat_id=manager['telegram_id'],
                            photo=zayavka['media'],
                            caption=manager_text,
                            reply_markup=manager_keyboard,
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_message(
                            chat_id=manager['telegram_id'],
                            text=manager_text,
                            reply_markup=manager_keyboard,
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logger.error(f"Menejerga xabar yuborishda xatolik: {str(e)}")

    except Exception as e:
        logger.error(f"Zayavka yaratishda xatolik: {str(e)}")
        await call.message.answer("Zayavka yaratishda xatolik yuz berdi!" if lang == "uz" else "Произошла ошибка при создании заказа!")
        return

    await state.clear()
    await call.message.answer("Buyurtma yaratildi!" if lang == "uz" else "Заказ создан!", reply_markup=get_main_menu_keyboard(lang))
    await call.message.delete()

@router.callback_query(F.data == "resend_zayavka")
async def resend_zayavka(call: CallbackQuery, state: FSMContext):
    await safe_remove_inline_call(call)
    await state.clear()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    await call.message.edit_text("Zayavka turini tanlang:" if lang == "uz" else "Выберите тип заявки:", reply_markup=zayavka_type_keyboard(lang))
    await state.set_state(UserStates.choosing_zayavka_type)

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
        async with db_manager.get_connection() as conn:
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
                        f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}</b>"
                    )
                else:
                    order_info = (
                        f"🆔 ID заказа: <b>{zayavka['id']}</b>\n"
                        f"👤 Клиент: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Телефон: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Адрес: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Описание: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}</b>"
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
                                f"⏰ Sana: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}</b>"
                            )
                        else:
                            solution_text = (
                                f"\n\n🛠 Решение: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Техник: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Дата: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}</b>"
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
    except Exception as e:
        logger.error(f"Buyurtmalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.callback_query(lambda c: c.data.startswith('orders_page_'))
async def process_orders_page(callback: CallbackQuery, state: FSMContext):
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            return
        lang = user.get('language', 'uz')
        page = int(callback.data.split('_')[-1])
        await state.update_data(page=page)
        per_page = 5
        offset = (page - 1) * per_page
        async with db_manager.get_connection() as conn:
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
            for zayavka in zayavki:
                if lang == 'uz':
                    order_info = (
                        f"🆔 Buyurtma ID: <b>{zayavka['id']}</b>\n"
                        f"👤 Mijoz: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Telefon: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Manzil: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Tavsif: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Sana: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}</b>"
                    )
                else:
                    order_info = (
                        f"🆔 ID заказа: <b>{zayavka['id']}</b>\n"
                        f"👤 Клиент: <b>{user.get('full_name', '-')}</b>\n"
                        f"📞 Телефон: <b>{user.get('phone_number', '-')}</b>\n"
                        f"📍 Адрес: <b>{zayavka.get('address', '-')}</b>\n"
                        f"📝 Описание: <b>{zayavka.get('description', '-')}</b>\n"
                        f"⏰ Дата: <b>{zayavka['created_at'].strftime('%d.%m.%Y %H:%M') if zayavka.get('created_at') else '-'}</b>"
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
                                f"⏰ Sana: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}</b>"
                            )
                        else:
                            solution_text = (
                                f"\n\n🛠 Решение: <b>{sol.get('solution_text', '-')}</b>\n"
                                f"👨‍🔧 Техник: <b>{sol.get('instander_name', '-')}</b>\n"
                                f"⏰ Дата: <b>{sol.get('created_at').strftime('%d.%m.%Y %H:%M') if sol.get('created_at') else '-'}</b>"
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
        await callback.answer()
    except Exception as e:
        logger.error(f"Sahifalarni ko'rsatishda xatolik: {str(e)}", exc_info=True)
        await callback.message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(F.text.in_(["📞 Operator bilan bog'lanish", "📞 Связаться с оператором"]))
async def contact_operator(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
            return
        lang = user.get('language', 'uz')
        await message.answer("Operator bilan bog'lanish: +998 90 123 45 67" if lang == "uz" else "Контакт с оператором: +998 90 123 45 67")
    except Exception as e:
        logger.error(f"Operator bilan bog'lanishda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(F.text.in_(["🌐 Изменить язык", "🌐 Изменить язык"]))
async def show_language_keyboard(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    lang = await get_user_lang(message.from_user.id)
    success = await show_language_selection(message, "client", state)
    if success:
        await state.set_state(UserStates.selecting_language)
    else:
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(UserStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    await safe_remove_inline(message)
    try:
        if message.contact.user_id != message.from_user.id:
            await message.answer("Iltimos, o'zingizning kontaktingizni ulashing." if lang == "uz" else "Пожалуйста, используйте свой контактный номер.")
            return

        phone_number = message.contact.phone_number
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Foydalanuvchi topilmadi. Iltimos, qaytadan urinib ko'ring." if lang == "uz" else "Пользователь не найден. Пожалуйста, попробуйте еще раз.")
            return
            
        await update_user_phone(user['id'], phone_number)
        lang = user.get('language', 'uz')
        role = user.get('role', 'client')
        
        # Foydalanuvchi o'z ro'lida qoladi, boshqa ro'lga o'tmaydi
        if role == "client":
            from keyboards.client_buttons import get_main_menu_keyboard
            await message.answer(
                text="Xush kelibsiz! Qanday yordam bera olaman?" if lang == "uz" else "Добро пожаловать! Как я могу помочь?",
                reply_markup=get_main_menu_keyboard(lang)
            )
            await state.set_state(UserStates.main_menu)
        elif role == "technician":
            from keyboards.technician_buttons import get_technician_main_menu_keyboard
            from states.technician_states import TechnicianStates
            await message.answer(
                text="Technician.welcome" if lang == "uz" else "Добро пожаловать!",
                reply_markup=get_technician_main_menu_keyboard(lang)
            )
            await state.set_state(TechnicianStates.main_menu)
        # Add other roles here if needed
            
    except Exception as e:
        logger.error(f"Error in process_contact: {str(e)}")
        lang = (await state.get_data()).get('language', 'uz')
        await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.")

async def change_language(call: CallbackQuery, state: FSMContext):
    """
    Handle language change for client role.
    """
    try:
        # Get user data
        user_data = await state.get_data()
        user = user_data.get('user')
        
        if not user:
            logger.warning(f"User not found in state for change_language: {call.from_user.id}")
            return
            
        # Get new language from callback data
        new_lang = "uz" if call.data == "client_lang_uz" else "ru"
        role = user.get('role')
        
        # Check if user has client role
        if role != "client":
            await call.answer("Bu funksiya faqat mijozlar uchun.", show_alert=True)
            return
            
        # Update language in database
        await update_user_language(user['id'], new_lang)
        
        # Update user data in state (faqat language ni o'zgartirish)
        user['language'] = new_lang
        await state.update_data(user=user, language=new_lang)
        
        # Get appropriate keyboard based on role
        keyboard = get_main_menu_keyboard(new_lang)
        lang = user.get('language', 'uz')
        # Update message with new language
        await call.message.edit_text(
            "Til o'zgartirildi" if lang == "uz" else "Язык изменен",
            reply_markup=keyboard
        )
        
        logger.info(f"Language changed to {new_lang} for user {user['id']}")
        
    except Exception as e:
        logger.error(f"Error in change_language: {str(e)}")
        lang = user.get('language', 'uz') if 'user' in locals() and user else 'uz'
        await call.answer(
            "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring." if lang == "uz" else "Произошла ошибка. Пожалуйста, попробуйте еще раз.",
            show_alert=True
        )
        
    from database.queries import db_manager
    async with db_manager.get_connection() as conn:
        await conn.execute(
            "UPDATE users SET language = $1 WHERE telegram_id = $2",
            new_lang, call.from_user.id
        )
    
    # Client uchun asosiy menyu
    reply_markup = get_main_menu_keyboard(new_lang)
    menu_text = "Asosiy menyu" if lang == "uz" else "Главное меню"
    await call.message.edit_text("Til o'zgartirildi" if lang == "uz" else "Язык изменен")
    await call.message.answer(
        menu_text,
        reply_markup=reply_markup
    )
    await state.set_state(UserStates.main_menu)

# CRM Integration Handlers

@router.callback_query(F.data.startswith("assign_zayavka_"))
async def assign_zayavka_handler(call: CallbackQuery, state: FSMContext):
    """Zayavkani technicianga biriktirish"""
    logger.info(f"assign_zayavka_handler called with callback_data: {call.data}")
    
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    logger.info(f"User data: {user}")
    
    if not user or user.get('role') != 'manager':
        logger.warning(f"Non-manager user attempted to assign zayavka: {call.from_user.id}")
        await call.message.answer("Sizda bu amalni bajarish huquqi yo'q!" if lang == "uz" else "У вас нет доступа к этому действию!")
        return
    
    try:
        zayavka_id = int(call.data.split("_")[-1])
        logger.info(f"Parsed zayavka_id: {zayavka_id}")
    except ValueError as e:
        logger.error(f"Invalid zayavka_id in callback_data: {call.data}, error: {e}")
        lang = user.get('language', 'uz')
        await call.message.answer("Xato zayavka ID! Iltimos, qayta urinib ko'ring." if lang == "uz" else "Неверный ID заказа! Пожалуйста, попробуйте еще раз.")
        return
    
    from database.queries import get_available_technicians, get_zayavka_by_id
    try:
        zayavka = await get_zayavka_by_id(zayavka_id)
        if not zayavka:
            logger.error(f"Zayavka not found: {zayavka_id}")
            lang = user.get('language', 'uz')
            await call.message.answer("Zayavka topilmadi!" if lang == "uz" else "Заказ не найден!")
            return
        technicians = await get_available_technicians()
        logger.info(f"Available technicians: {technicians}")
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        lang = user.get('language', 'uz')
        await call.message.answer("Ma'lumotlarni olishda xatolik yuz berdi!" if lang == "uz" else "Произошла ошибка при получении данных!")
        return
    
    if not technicians:
        logger.info("No available technicians found")
        lang = user.get('language', 'uz')
        await call.message.answer("Hozirda bo'sh technician yo'q!" if lang == "uz" else "Нет доступных техников!")
        return
    
    try:
        # Always try to update the existing inline keyboard
        # Create technician selection keyboard inline
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard_buttons = []
        for tech in technicians:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👨‍🔧 {tech['full_name']}",
                    callback_data=f"select_tech_{tech['id']}"
                )
            ])
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="❌ Bekor qilish",
                callback_data="cancel_assignment"
            )
        ])
        technician_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        try:
            await call.message.edit_reply_markup(reply_markup=technician_keyboard)
        except Exception:
            lang = user.get('language', 'uz')
            await call.message.answer(
                "Technician tanlang:" if lang == "uz" else "Выберите техника:",
                reply_markup=technician_keyboard
            )
        logger.info(f"Sent technician selection keyboard for zayavka_id: {zayavka_id}")
        await state.update_data(assigning_zayavka_id=zayavka_id)
    except Exception as e:
        logger.error(f"Error sending technician selection keyboard: {str(e)}")
        lang = user.get('language', 'uz')
        await call.message.answer("Klaviaturani yuborishda xatolik yuz berdi!" if lang == "uz" else "Произошла ошибка при отправке клавиатуры!")

@router.callback_query(F.data.startswith("select_tech_"))
async def select_technician_handler(call: CallbackQuery, state: FSMContext):
    """Technician tanlash"""
    logger.info(f"select_technician_handler called with callback_data: {call.data}")
    
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    try:
        technician_id = int(call.data.split("_")[-1])
        logger.info(f"Parsed technician_id: {technician_id}")
    except ValueError as e:
        logger.error(f"Invalid technician_id in callback_data: {call.data}, error: {e}")
        await call.message.answer("Xato technician ID! Iltimos, qayta urinib ko'ring." if lang == "uz" else "Неверный ID техника! Пожалуйста, попробуйте еще раз.")
        return
    
    data = await state.get_data()
    zayavka_id = data.get('assigning_zayavka_id')
    logger.info(f"Retrieved zayavka_id from state: {zayavka_id}")
    
    if not zayavka_id:
        logger.error("No zayavka_id found in state")
        await call.message.answer("Xatolik: Zayavka ID topilmadi!" if lang == "uz" else "Ошибка: ID заказа не найден!")
        return
    
    try:
        from database.queries import assign_zayavka_to_technician, get_zayavka_by_id
        async with db_manager.get_connection() as conn:
            # Get current user (manager) data
            current_user = await conn.fetchrow(
                "SELECT id FROM users WHERE telegram_id = $1",
                call.from_user.id
            )
            if not current_user:
                logger.error(f"Manager not found: {call.from_user.id}")
                lang = user.get('language', 'uz')
                await call.message.answer("Manager ma'lumotlari topilmadi!" if lang == "uz" else "Данные менеджера не найдены!")
                return

            zayavka = await get_zayavka_by_id(zayavka_id)
            if not zayavka:
                logger.error(f"Zayavka not found: {zayavka_id}")
                lang = user.get('language', 'uz')
                await call.message.answer("Zayavka topilmadi!" if lang == "uz" else "Заказ не найден!")
                return
                
            technician = await conn.fetchrow(
                "SELECT full_name, telegram_id, language FROM users WHERE id = $1 AND role = 'technician'",
                technician_id
            )
            if not technician:
                logger.error(f"Technician not found: {technician_id}")
                lang = user.get('language', 'uz')
                await call.message.answer("Technician topilmadi!" if lang == "uz" else "Техник не найден!")
                return
                
            await assign_zayavka_to_technician(zayavka_id, technician_id, current_user['id'])
            logger.info(f"Zayavka {zayavka_id} assigned to technician {technician_id}")
        
            tech_lang = technician.get('language', 'uz') or 'uz'
            if tech_lang == 'uz':
                tech_text = f"🆕 Yangi buyurtma!\n🆔 Buyurtma ID: {zayavka['id']}\nIltimos, buyurtmani ko'rib chiqing."
            else:
                tech_text = f"🆕 Новый заказ!\n🆔 ID заказа: {zayavka['id']}\nПожалуйста, рассмотрите заказ."
            try:
                await bot.send_message(
                    chat_id=technician['telegram_id'],
                    text=tech_text,
                    reply_markup=get_task_inline_keyboard(zayavka_id, 'assigned'),
                    parse_mode='HTML'
                )
                logger.info(f"Notification sent to technician: {technician['telegram_id']}")
            except Exception as e:
                logger.error(f"Technicianga xabar yuborishda xatolik: {str(e)}")
            
            # Xabarni tahrirlashdan oldin reply_markup holatini tekshirish
            try:
                if call.message.reply_markup:  # Agar reply_markup mavjud bo'lsa
                    await call.message.edit_reply_markup(reply_markup=None)
            except Exception as e:
                if 'message is not modified' not in str(e):
                    logger.error(f"edit_reply_markup error: {str(e)}")
                    lang = user.get('language', 'uz')
                    await call.message.answer("Zayavka biriktirishda xatolik yuz berdi!" if lang == "uz" else "Ошибка при привязке заказа!")
            
            await state.clear()
        
    except Exception as e:
        logger.error(f"Zayavka biriktirishda xatolik: {str(e)}")
        lang = user.get('language', 'uz')
        await call.message.answer("Zayavka biriktirishda xatolik yuz berdi!" if lang == "uz" else "Ошибка при привязке заказа!")

@router.callback_query(F.data == "cancel_assignment")
async def cancel_assignment_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    await call.message.edit_text("❌ Biriktirish bekor qilindi" if lang == "uz" else "❌ Привязка отменена")
    await state.clear()

@router.callback_query(F.data.startswith("client_lang_"))
async def change_language(call: CallbackQuery, state: FSMContext):
    """Handle language change callback for client role"""
    await process_language_change(
        call=call,
        role="client",
        get_main_keyboard_func=get_main_menu_keyboard,
        state=state
    )
    await state.set_state(UserStates.main_menu)
