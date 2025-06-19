from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from database.models import User
from keyboards.client_buttons import (
    get_main_menu_keyboard, get_back_keyboard, get_contact_keyboard,
    get_language_keyboard, zayavka_type_keyboard, media_attachment_keyboard,
    geolocation_keyboard, confirmation_keyboard, get_technician_selection_keyboard,
    get_task_action_keyboard, get_completion_keyboard
)
from states.user_states import UserStates
from loader import bot
from utils.i18n import i18n
from database.queries import get_user_by_telegram_id, create_user
from utils.logger import setup_module_logger
from config import ZAYAVKA_GROUP_ID

# Setup dedicated logger for client module
logger = setup_module_logger('client')

router = Router()

class OrderStates(StatesGroup):
    """Buyurtma holatlari"""
    waiting_for_description = State()
    waiting_for_address = State()
    waiting_for_phone_number = State()

async def get_lang(user_id):
    user = await get_user_by_telegram_id(user_id)
    return user.get('language', 'uz') if user else 'uz'

# --- UNIVERSAL REPLY GUARD ---
MAIN_MENU_BUTTONS = [
    i18n.get_message('uz', 'new_order'), i18n.get_message('ru', 'new_order'),
    i18n.get_message('uz', 'my_orders'), i18n.get_message('ru', 'my_orders'),
    i18n.get_message('uz', 'contact_operator'), i18n.get_message('ru', 'contact_operator'),
    i18n.get_message('uz', 'change_language'), i18n.get_message('ru', 'change_language'),
]

# --- END UNIVERSAL REPLY GUARD ---

async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for clients"""
    try:
        # State ni tozalash
        await state.clear()
        
        # Foydalanuvchini tekshirish
        db_user = await get_user_by_telegram_id(message.from_user.id)
        logger.info(f"Client start - Foydalanuvchi tekshirildi: {message.from_user.id}, natija: {db_user}")
        
        if db_user:
            lang = db_user.get('language', 'uz') 
            if not db_user['phone_number']:
                await message.answer(i18n.get_message(lang, "share_contact"), reply_markup=get_contact_keyboard(lang))
                await state.set_state(UserStates.waiting_for_phone_number)
            else:
                await message.answer(
                    text=i18n.get_message(lang, "welcome_back"),
                    reply_markup=get_main_menu_keyboard(lang)
                )
                await state.set_state(UserStates.main_menu)  # Set main menu state
        else:
            # Yangi foydalanuvchi yaratish
            from database.queries import _pool
            async with _pool.acquire() as conn:
                new_user = await create_user(
                    conn,
                    telegram_id=message.from_user.id,
                    full_name=message.from_user.full_name,
                    role='client'
                )
                logger.info(f"Yangi foydalanuvchi yaratildi: {new_user}")
            
            # Til tanlash menyusini ko'rsatish
            await state.set_state(UserStates.selecting_language)
            await message.answer(text=i18n.get_message("uz", "welcome"), reply_markup=get_language_keyboard())
        
        logger.info(f"Client start buyrug'i muvaffaqiyatli yakunlandi: {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Client start buyrug'ida xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(F.text.in_(["Yangi buyurtma", "Новый заказ"]))
async def new_order(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta ishga tushiring.")
        return
    
    # Technician roli uchun tekshiruv
    if user.get('role') == 'technician':
        await message.answer("Sizda mijoz huquqi yo'q. Iltimos, o'z menyu bo'limingizdan foydalaning.")
        return
    
    lang = user.get('language', 'uz')

    if message.text == i18n.get_message(lang, "back"):
        # Delete previous inline keyboard messages
        async for msg in message.bot.iter_messages(message.chat.id, limit=10):
            if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                await msg.delete()
        
        await message.answer(
            i18n.get_message(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return

    await message.answer(
        i18n.get_message(lang, "leave_your_request"),
        reply_markup=get_back_keyboard(lang)
    )
    
    # Then send zayavka type selection message
    await message.answer(
        i18n.get_message(lang, "select_zayavka_type"),
        reply_markup=zayavka_type_keyboard()
    )
    await state.clear()
    await state.set_state(UserStates.choosing_zayavka_type)

@router.callback_query(F.data.in_(["zayavka_type_b2b", "zayavka_type_b2c"]))
async def choose_zayavka_type(call: CallbackQuery, state: FSMContext):
    await call.answer()
    zayavka_type = "B2B" if call.data == "zayavka_type_b2b" else "B2C"
    await state.update_data(zayavka_type=zayavka_type)
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    await call.message.edit_text(i18n.get_message(lang, "enter_abonent_id"))
    await state.set_state(UserStates.waiting_for_abonent_id)

@router.message(UserStates.waiting_for_abonent_id)
async def get_abonent_id(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')

    # Orqaga tugmasi bosilganini tekshirish
    if message.text in [i18n.get_message('uz', 'back'), i18n.get_message('ru', 'back')]:
        # Delete previous inline keyboard messages
        async for msg in message.bot.iter_messages(message.chat.id, limit=10):
            if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                await msg.delete()
                
        await state.clear()
        await message.answer(
            i18n.get_message(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return

    if message.reply_to_message:
        await state.update_data(reply_candidate={
            'text': message.text,
            'state': 'waiting_for_abonent_id',
        })
        await message.answer("Bu xabar reply orqali yuborildi.", reply_markup=get_back_keyboard(lang))
        return

    abonent_id = message.text
    await state.update_data(abonent_id=abonent_id)
    await message.answer(i18n.get_message(lang, "enter_order_description"), reply_markup=get_back_keyboard(lang))
    await state.set_state(UserStates.waiting_for_description)

@router.message(UserStates.waiting_for_description)
async def get_description(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')

    # Orqaga tugmasi bosilganini tekshirish
    if message.text in [i18n.get_message('uz', 'back'), i18n.get_message('ru', 'back')]:
        # Delete previous inlinelisisь

        async for msg in message.bot.iter_messages(message.chat.id, limit=10):
            if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                await msg.delete()
                
        await state.clear()
        await message.answer(
            i18n.get_message(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return

    if message.reply_to_message:
        await state.update_data(reply_candidate={
            'text': message.text,
            'state': 'waiting_for_description',
        })
        return

    description = message.text
    await state.update_data(description=description)
    await message.answer(i18n.get_message(lang, "ask_for_media"), reply_markup=media_attachment_keyboard())
    await state.set_state(UserStates.asking_for_media)

@router.callback_query(F.data.in_(["attach_media_yes", "attach_media_no"]))
async def ask_for_media(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    
    # Delete the inline keyboard first
    await call.message.delete()
    
    if call.data == "attach_media_yes":
        await call.message.answer("Media faylini yuboring (foto yoki fayl):", reply_markup=get_back_keyboard(lang))
        await state.set_state(UserStates.waiting_for_media)
    else:
        await state.update_data(media=None)
        await call.message.answer(i18n.get_message(lang, "enter_order_address"), reply_markup=get_back_keyboard(lang))
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
        i18n.get_message(lang, "main_menu"),
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
    await message.answer(i18n.get_message(lang, "enter_order_address"), reply_markup=get_back_keyboard(lang))
    await state.set_state(UserStates.waiting_for_address)

@router.message(UserStates.waiting_for_address)
async def get_address(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')

    # Orqaga tugmasi bosilganini tekshirish
    if message.text in [i18n.get_message('uz', 'back'), i18n.get_message('ru', 'back')]:
        # Delete previous inline keyboard messages
        async for msg in message.bot.iter_messages(message.chat.id, limit=10):
            if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                await msg.delete()
                
        await state.clear()
        await message.answer(
            i18n.get_message(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
        return

    if message.reply_to_message:
        await state.update_data(reply_candidate={
            'text': message.text,
            'state': 'waiting_for_address',
        })
        return

    address = message.text.strip()
    if not address or len(address) < 5:
        await message.answer(i18n.get_message(lang, "invalid_address") or "Iltimos, to'g'ri manzil kiriting.")
        return

    await state.update_data(address=address)
    await message.answer(i18n.get_message(lang, "ask_for_location"), reply_markup=geolocation_keyboard())
    await state.set_state(UserStates.asking_for_location)

@router.callback_query(F.data.in_(["reply_confirm_yes", "reply_confirm_no"]))
async def handle_reply_confirmation(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    reply_candidate = data.get('reply_candidate')
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if not reply_candidate:
        await call.message.answer("Hech qanday reply xabar topilmadi.")
        return
    if call.data == "reply_confirm_yes":
        # Qaysi state uchun reply kelganini aniqlash va uni ishlatish
        if reply_candidate['state'] == 'waiting_for_abonent_id':
            await state.update_data(abonent_id=reply_candidate['text'])
            await call.message.answer(i18n.get_message(lang, "enter_order_description"), reply_markup=get_back_keyboard(lang))
            await state.set_state(UserStates.waiting_for_description)
        elif reply_candidate['state'] == 'waiting_for_description':
            await state.update_data(description=reply_candidate['text'])
            await call.message.answer(i18n.get_message(lang, "ask_for_media"), reply_markup=media_attachment_keyboard())
            await state.set_state(UserStates.asking_for_media)
        elif reply_candidate['state'] == 'waiting_for_address':
            address = reply_candidate['text'].strip()
            if not address or len(address) < 5:
                await call.message.answer(i18n.get_message(lang, "invalid_address") or "Iltimos, to'g'ri manzil kiriting.")
                return
            await state.update_data(address=address)
            await call.message.answer(i18n.get_message(lang, "ask_for_location"), reply_markup=geolocation_keyboard())
            await state.set_state(UserStates.asking_for_location)
        await state.update_data(reply_candidate=None)
    else:
        # Yo'q bosilsa, xabarni qabul qilmaslik va foydalanuvchiga davom etishni aytish
        await call.message.answer("Reply xabar bekor qilindi. Davom etish uchun yangi xabar yuboring.")
        await state.update_data(reply_candidate=None)

@router.callback_query(F.data.in_(["send_location_yes", "send_location_no"]))
async def ask_for_location(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    if call.data == "send_location_yes":
        # Show reply keyboard with location request
        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Geolokatsiyani yuborish", request_location=True)]],
            resize_keyboard=True
        )
        await call.message.delete()
        await call.message.answer("Geolokatsiyani yuborish uchun tugmani bosing:", reply_markup=location_keyboard)
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
    await message.answer("Geolokatsiya qabul qilindi.", reply_markup=get_main_menu_keyboard(lang))
    await show_order_confirmation(message, state, lang)
    await state.set_state(UserStates.confirming_zayavka)

async def show_order_confirmation(message_or_call, state, lang):
    data = await state.get_data()
    logger.info(f"Order confirmation data: {data}")  # Ma'lumotlarni logga yozish
    summary = i18n.get_message(
        lang, "order_summary",
        zayavka_type=data.get("zayavka_type", "-"),
        abonent_id=data.get("abonent_id", "-"),
        description=data.get("description", "-"),
        address=data.get("address", "-"),
        media="✅" if data.get("media") else "❌",
        location=data.get("location") if data.get("location") else "❌"
    )
    await message_or_call.answer(
        summary + "\n" + i18n.get_message(lang, "confirm_order"),
        reply_markup=confirmation_keyboard()
    )

@router.callback_query(F.data == "confirm_zayavka")
async def confirm_zayavka(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        async with bot.pool.acquire() as conn:
            db_user = await conn.fetchrow("SELECT id, full_name FROM users WHERE telegram_id = $1", call.from_user.id)
            if not db_user:
                logger.error(f"No user found for telegram_id: {call.from_user.id}")
                await call.message.answer("Foydalanuvchi topilmadi!")
                return

            zayavka = await conn.fetchrow(
                '''INSERT INTO zayavki (user_id, zayavka_type, abonent_id, description, address, media, location, status)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *''',
                db_user['id'],
                data.get("zayavka_type"),
                data.get("abonent_id"),
                data.get("description"),
                data.get("address"),
                data.get("media"),
                data.get("location"),
                'new'
            )
            logger.info(f"New zayavka created: {zayavka['id']}")
            
            user_zayavka_count = await conn.fetchval(
                'SELECT COUNT(*) FROM zayavki WHERE user_id = $1 AND id <= $2',
                db_user['id'], zayavka['id']
            )
            
            zayavka_text = (
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
            
            manager_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="👨‍🔧 Technicianga biriktirish",
                    callback_data=f"assign_zayavka_{zayavka['id']}"
                )]
            ])
            
            if zayavka['media']:
                await bot.send_photo(
                    chat_id=call.from_user.id,
                    photo=zayavka['media'],
                    caption=zayavka_text,
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    chat_id=call.from_user.id,
                    text=zayavka_text,
                    parse_mode='HTML'
                )
            
            if zayavka['media']:
                await bot.send_photo(
                    chat_id=ZAYAVKA_GROUP_ID,
                    photo=zayavka['media'],
                    caption=zayavka_text,
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    chat_id=ZAYAVKA_GROUP_ID,
                    text=zayavka_text,
                    parse_mode='HTML'
                )
            
            managers = await conn.fetch("SELECT telegram_id FROM users WHERE role = 'manager'")
            for manager in managers:
                try:
                    if zayavka['media']:
                        await bot.send_photo(
                            chat_id=manager['telegram_id'],
                            photo=zayavka['media'],
                            caption=f"🆕 Yangi zayavka!\n\n{zayavka_text}",
                            reply_markup=manager_keyboard,
                            parse_mode='HTML'
                        )
                    else:
                        await bot.send_message(
                            chat_id=manager['telegram_id'],
                            text=f"🆕 Yangi zayavka!\n\n{zayavka_text}",
                            reply_markup=manager_keyboard,
                            parse_mode='HTML'
                        )
                except Exception as e:
                    logger.error(f"Menejerga xabar yuborishda xatolik: {str(e)}")
    
    except Exception as e:
        logger.error(f"Zayavka yaratishda xatolik: {str(e)}")
        await call.message.answer("Zayavka yaratishda xatolik yuz berdi!")
        return

    await state.clear()
    await call.message.answer(i18n.get_message(lang, "order_created"), reply_markup=get_main_menu_keyboard(lang))
    await call.message.delete()

@router.callback_query(F.data == "resend_zayavka")
async def resend_zayavka(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    user = await get_user_by_telegram_id(call.from_user.id)
    lang = user.get('language', 'uz')
    await call.message.edit_text(i18n.get_message(lang, "select_zayavka_type"), reply_markup=zayavka_type_keyboard())
    await state.set_state(UserStates.choosing_zayavka_type)

@router.message(F.text.in_(["Mening buyurtmalarim", "Мои заказы"]))
async def my_orders(message: Message, state: FSMContext):
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta ishga tushiring.")
            return
        
        if user.get('role') == 'technician':
            await message.answer("Sizda mijoz huquqi yo'q. Iltimos, o'z menyu bo'limingizdan foydalaning.")
            return
        
        lang = user.get('language', 'uz')
        
        data = await state.get_data()
        page = data.get('page', 1)
        per_page = 10
        offset = (page - 1) * per_page
        
        async with bot.pool.acquire() as conn:
            total = await conn.fetchval('SELECT COUNT(*) FROM zayavki WHERE user_id = $1', user['id'])
            
            if total == 0:
                await message.answer(i18n.get_message(lang, "no_orders"))
                return
                
            zayavki = await conn.fetch(
                '''SELECT * FROM zayavki 
                   WHERE user_id = $1 
                   ORDER BY created_at DESC
                   LIMIT $2 OFFSET $3''',
                user['id'], per_page, offset
            )
            
            for zayavka in zayavki:
                zayavka_text = (
                    f"🆔 Zayavka raqami: {zayavka['id']}\n"
                    f"📅 Sana: {zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"📝 Tavsif: {zayavka['description']}\n"
                    f"📍 Manzil: {zayavka['address']}\n"
                    f"📊 Holat: {zayavka['status']}"
                )
                if zayavka.get('media'):
                    await message.answer_photo(
                        photo=zayavka['media'],
                        caption=zayavka_text
                    )
                else:
                    await message.answer(zayavka_text)
            
            if total > per_page:
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ Orqaga",
                        callback_data=f"orders_page_{page-1}"
                    ))
                    
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text="Oldinga ➡️",
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
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.callback_query(lambda c: c.data.startswith('orders_page_'))
async def process_orders_page(callback: CallbackQuery, state: FSMContext):
    try:
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.message.answer("Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta ishga tushiring.")
            return
        lang = user.get('language', 'uz')
        
        page = int(callback.data.split('_')[-1])
        await state.update_data(page=page)
        per_page = 10
        offset = (page - 1) * per_page
        
        async with bot.pool.acquire() as conn:
            total = await conn.fetchval('SELECT COUNT(*) FROM zayavki WHERE user_id = $1', user['id'])
            
            if total == 0:
                await callback.message.answer(i18n.get_message(lang, "no_orders"))
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
                zayavka_text = (
                    f"🆔 Zayavka raqami: {zayavka['id']}\n"
                    f"📅 Sana: {zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                    f"📝 Tavsif: {zayavka['description']}\n"
                    f"📍 Manzil: {zayavka['address']}\n"
                    f"📊 Holat: {zayavka['status']}"
                )
                if zayavka.get('media'):
                    await callback.message.answer_photo(
                        photo=zayavka['media'],
                        caption=zayavka_text
                    )
                else:
                    await callback.message.answer(zayavka_text)
            
            if total > per_page:
                total_pages = (total + per_page - 1) // per_page
                buttons = []
                
                if page > 1:
                    buttons.append(InlineKeyboardButton(
                        text="⬅️ Orqaga",
                        callback_data=f"orders_page_{page-1}"
                    ))
                    
                if page < total_pages:
                    buttons.append(InlineKeyboardButton(
                        text="Oldinga ➡️",
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
        await callback.message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(F.text.in_(["Operator bilan bog'lanish", "Связаться с оператором"]))
async def contact_operator(message: Message, state: FSMContext):
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta ishga tushiring.")
            return
        lang = user.get('language', 'uz')
        await message.answer(i18n.get_message(lang, "operator_contact"))
    except Exception as e:
        logger.error(f"Operator bilan bog'lanishda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(F.text.in_(["Tilni o'zgartirish", "Изменить язык"]))
async def show_language_keyboard(message: Message, state: FSMContext):
    try:
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("Xatolik yuz berdi. Iltimos, /start buyrug'ini qayta ishga tushiring.")
            return
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "select_language"),
            reply_markup=get_language_keyboard()
        )
        await state.set_state(UserStates.selecting_language)
    except Exception as e:
        logger.error(f"Til tanlashda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@router.message(UserStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    try:
        if message.contact.user_id != message.from_user.id:
            await message.answer("Iltimos, o'zingizning kontaktingizni ulashing.")
            return

        phone_number = message.contact.phone_number
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        async with bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET phone_number = $1 WHERE telegram_id = $2',
                phone_number,
                message.from_user.id
            )

        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            text=i18n.get_message(lang, "welcome_back"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)

    except Exception as e:
        logger.error(f"Kontaktni qayta ishlashda xatolik: {str(e)}", exc_info=True)
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.") 

@router.message(F.text.in_([i18n.get_message('uz', 'back'), i18n.get_message('ru', 'back')]))
async def handle_back(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    role = user.get('role')
    await state.clear()

    if role == 'client':
        await message.answer(
            i18n.get_message(lang, "main_menu"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)
    elif role == 'technician':
        from keyboards.technician_buttons import get_technician_main_menu_keyboard
        from states.technician_states import TechnicianStates
        await message.answer(
            i18n.get_message(lang, "technician_main_menu"),
            reply_markup=get_technician_main_menu_keyboard(lang)
        )
        await state.set_state(TechnicianStates.main_menu)
    elif role == 'admin':
        from keyboards.admin_buttons import admin_main_menu
        from states.admin_states import AdminStates
        await message.answer(
            i18n.get_message(lang, "admin.welcome") or "Admin paneliga xush kelibsiz!",
            reply_markup=admin_main_menu
        )
        await state.set_state(AdminStates.main_menu)
    else:
        await message.answer("Bosh menyu.")

@router.callback_query(F.data.in_(["lang_uz", "lang_ru"]))
async def change_language(call: CallbackQuery, state: FSMContext):
    await call.answer()
    user = await get_user_by_telegram_id(call.from_user.id)
    if not user:
        return
    new_lang = "uz" if call.data == "lang_uz" else "ru"
    role = user.get('role')
    from database.queries import _pool
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET language = $1 WHERE telegram_id = $2",
            new_lang, call.from_user.id
        )
    if role == "client":
        from keyboards.client_buttons import get_main_menu_keyboard
        reply_markup = get_main_menu_keyboard(new_lang)
        menu_text = i18n.get_message(new_lang, "main_menu")
    elif role == "technician":
        from keyboards.technician_buttons import get_technician_main_menu_keyboard
        reply_markup = get_technician_main_menu_keyboard(new_lang)
        menu_text = i18n.get_message(new_lang, "technician_main_menu")
    elif role == "admin":
        from keyboards.admin_buttons import admin_main_menu
        reply_markup = admin_main_menu
        menu_text = i18n.get_message(new_lang, "admin.welcome") or "Admin paneliga xush kelibsiz!"
    else:
        reply_markup = None
        menu_text = "Bosh menyu."
    await call.message.edit_text(i18n.get_message(new_lang, "language_changed"))
    await call.message.answer(
        menu_text,
        reply_markup=reply_markup
    )

# CRM Integration Handlers

@router.callback_query(F.data.startswith("assign_zayavka_"))
async def assign_zayavka_handler(call: CallbackQuery, state: FSMContext):
    """Zayavkani technicianga biriktirish"""
    logger.info(f"assign_zayavka_handler called with callback_data: {call.data}")
    
    await call.answer()
    
    user = await get_user_by_telegram_id(call.from_user.id)
    logger.info(f"User data: {user}")
    
    if not user or user.get('role') != 'manager':
        logger.warning(f"Non-manager user attempted to assign zayavka: {call.from_user.id}")
        await call.message.answer("Sizda bu amalni bajarish huquqi yo'q!")
        return
    
    try:
        zayavka_id = int(call.data.split("_")[-1])
        logger.info(f"Parsed zayavka_id: {zayavka_id}")
    except ValueError as e:
        logger.error(f"Invalid zayavka_id in callback_data: {call.data}, error: {e}")
        await call.message.answer("Xato zayavka ID! Iltimos, qayta urinib ko'ring.")
        return
    
    from database.queries import get_available_technicians, get_zayavka_by_id
    try:
        zayavka = await get_zayavka_by_id(bot.pool, zayavka_id)
        if not zayavka:
            logger.error(f"Zayavka not found: {zayavka_id}")
            await call.message.answer("Zayavka topilmadi!")
            return
        technicians = await get_available_technicians()
        logger.info(f"Available technicians: {technicians}")
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        await call.message.answer("Ma'lumotlarni olishda xatolik yuz berdi!")
        return
    
    if not technicians:
        logger.info("No available technicians found")
        await call.message.answer("Hozirda bo'sh technician yo'q!")
        return
    
    try:
        await call.message.edit_text(
            "Technician tanlang:",
            reply_markup=get_technician_selection_keyboard(technicians)
        )
        logger.info(f"Sent technician selection keyboard for zayavka_id: {zayavka_id}")
        await state.update_data(assigning_zayavka_id=zayavka_id)
    except Exception as e:
        logger.error(f"Error sending technician selection keyboard: {str(e)}")
        await call.message.answer("Klaviaturani yuborishda xatolik yuz berdi!")

@router.callback_query(F.data.startswith("select_tech_"))
async def select_technician_handler(call: CallbackQuery, state: FSMContext):
    """Technician tanlash"""
    logger.info(f"select_technician_handler called with callback_data: {call.data}")
    
    await call.answer()
    
    try:
        technician_id = int(call.data.split("_")[-1])
        logger.info(f"Parsed technician_id: {technician_id}")
    except ValueError as e:
        logger.error(f"Invalid technician_id in callback_data: {call.data}, error: {e}")
        await call.message.answer("Xato technician ID! Iltimos, qayta urinib ko'ring.")
        return
    
    data = await state.get_data()
    zayavka_id = data.get('assigning_zayavka_id')
    logger.info(f"Retrieved zayavka_id from state: {zayavka_id}")
    
    if not zayavka_id:
        logger.error("No zayavka_id found in state")
        await call.message.answer("Xatolik: Zayavka ID topilmadi!")
        return
    
    try:
        from database.queries import assign_zayavka_to_technician, get_zayavka_by_id
        async with bot.pool.acquire() as conn:
            # Get current user (manager) data
            current_user = await conn.fetchrow(
                "SELECT id FROM users WHERE telegram_id = $1",
                call.from_user.id
            )
            if not current_user:
                logger.error(f"Manager not found: {call.from_user.id}")
                await call.message.answer("Manager ma'lumotlari topilmadi!")
                return

            zayavka = await get_zayavka_by_id(conn, zayavka_id)
            if not zayavka:
                logger.error(f"Zayavka not found: {zayavka_id}")
                await call.message.answer("Zayavka topilmadi!")
                return
                
            technician = await conn.fetchrow(
                "SELECT full_name, telegram_id FROM users WHERE id = $1 AND role = 'technician'",
                technician_id
            )
            if not technician:
                logger.error(f"Technician not found: {technician_id}")
                await call.message.answer("Technician topilmadi!")
                return
                
            await assign_zayavka_to_technician(zayavka_id, technician_id, current_user['id'])
            logger.info(f"Zayavka {zayavka_id} assigned to technician {technician_id}")
        
            zayavka_text = (
                f"🆕 Sizga yangi vazifa biriktirildi!\n\n"
                f"🆔 Zayavka ID: {zayavka['id']}\n"
                f"👤 Mijoz: {zayavka['user_name']}\n"
                f"📝 Tavsif: {zayavka['description']}\n"
                f"📍 Manzil: {zayavka['address']}\n"
                f"📅 Sana: {zayavka['created_at'].strftime('%d.%m.%Y %H:%M')}"
            )
            
            try:
                await bot.send_message(
                    chat_id=technician['telegram_id'],
                    text=zayavka_text,
                    reply_markup=get_task_action_keyboard(zayavka_id),
                    parse_mode='HTML'
                )
                logger.info(f"Notification sent to technician: {technician['telegram_id']}")
            except Exception as e:
                logger.error(f"Technicianga xabar yuborishda xatolik: {str(e)}")
            
            await call.message.edit_text(
                f"✅ Zayavka #{zayavka_id} {technician['full_name']}ga biriktirildi!"
            )
            await state.clear()
        
    except Exception as e:
        logger.error(f"Zayavka biriktirishda xatolik: {str(e)}")
        await call.message.answer("Zayavka biriktirishda xatolik yuz berdi!")

@router.callback_query(F.data == "cancel_assignment")
async def cancel_assignment_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("❌ Biriktirish bekor qilindi")
    await state.clear()