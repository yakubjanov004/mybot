from asyncio.log import logger
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.client_buttons import get_contact_keyboard, get_language_keyboard, get_main_menu_keyboard
from loader import bot
from keyboards.admin_buttons import (
    admin_main_menu, zayavka_management_keyboard, user_management_keyboard,
    statistics_keyboard, settings_keyboard, zayavka_status_keyboard,
    assign_zayavka_keyboard, zayavka_filter_keyboard, roles_keyboard,
    search_user_method_keyboard
)
from states.admin_states import AdminStates
from database.queries import (
    create_user, get_user_by_telegram_id, get_zayavki_by_status, get_zayavka_by_id,
    update_zayavka_status, assign_zayavka, get_staff_members
)
from states.user_states import UserStates
from utils.i18n import i18n
from datetime import datetime, timedelta
import asyncio

router = Router()

async def is_admin(user_id: int) -> bool:
    pool = bot.pool
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT role FROM users WHERE telegram_id = $1',
            user_id
        )
        return user and user['role'] == 'admin'

async def cmd_start(message: Message, state: FSMContext):
    """Start command handler for admins"""
    try:
        # Check if user is admin
        if await is_admin(message.from_user.id):
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            welcome_text = i18n.get_message(lang, "admin.welcome")
            if not welcome_text:
                welcome_text = "Admin paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель администратора!"
            
            await message.answer(
                welcome_text,
                reply_markup=admin_main_menu
            )
            await state.set_state(AdminStates.main_menu)
            return
        else:
            await message.answer("Sizda admin huquqlari yo'q.")
            
    except Exception as e:
        logger.error(f"Admin start buyrug'ida xatolik: {str(e)}", exc_info=True)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz') if user else 'uz'
        await message.answer(i18n.get_message(lang, "error_occurred"))

@router.message(F.text == "📋 Zayavkalar")
async def zayavka_management(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Zayavkalar boshqaruvi:", reply_markup=zayavka_management_keyboard)
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.message(F.text == "🆕 Yangi zayavkalar")
async def new_zayavki(message: Message):
    if await is_admin(message.from_user.id):
        async with bot.pool.acquire() as conn:
            zayavki = await get_zayavki_by_status(conn, 'new')
            if zayavki:
                for zayavka in zayavki:
                    text = f"Zayavka #{zayavka['id']}\n"
                    text += f"Foydalanuvchi: {zayavka['user_name']}\n"
                    text += f"Tavsif: {zayavka['description']}\n"
                    text += f"Manzil: {zayavka['address']}\n"
                    text += f"Vaqt: {zayavka['created_at'].strftime('%Y-%m-%d %H:%M')}"
                    
                    await message.answer(text, reply_markup=zayavka_status_keyboard(zayavka['id']))
            else:
                await message.answer("Yangi zayavkalar yo'q.")
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.callback_query(F.data.startswith("status_"))
async def change_zayavka_status(call: CallbackQuery):
    if await is_admin(call.from_user.id):
        _, zayavka_id, new_status = call.data.split("_")
        zayavka_id = int(zayavka_id)
        
        async with bot.pool.acquire() as conn:
            await update_zayavka_status(conn, zayavka_id, new_status, call.from_user.id)
            zayavka = await get_zayavka_by_id(conn, zayavka_id)
            
            status_text = {
                'in_progress': '⏳ Jarayonda',
                'completed': '✅ Bajarildi',
                'cancelled': '❌ Bekor qilindi'
            }.get(new_status, new_status)
            
            await call.message.edit_text(
                f"{call.message.text}\n\nStatus: {status_text}",
                reply_markup=None
            )
            await call.answer(f"Status {status_text} ga o'zgartirildi")
    else:
        await call.answer("Sizda admin huquqlari yo'q.")

@router.callback_query(F.data.startswith("admin_assign_"))
async def assign_zayavka_handler(call: CallbackQuery):
    user = await get_user_by_telegram_id(call.from_user.id)
    if user and user.get('role') in ['admin', 'manager']:
        _, _, zayavka_id, staff_id = call.data.split("_")
        zayavka_id, staff_id = int(zayavka_id), int(staff_id)
        
        async with bot.pool.acquire() as conn:
            await assign_zayavka(conn, zayavka_id, staff_id)
            staff = await conn.fetchrow("SELECT full_name FROM users WHERE id = $1", staff_id)
            
            await call.message.edit_text(
                f"{call.message.text}\n\nVazifalandirildi: {staff['full_name']}",
                reply_markup=None
            )
            await call.answer("Zayavka vazifalandirildi")
    else:
        await call.answer("Sizda admin yoki menejer huquqlari yo'q.")

@router.message(F.text == "👥 Foydalanuvchilar")
async def user_management(message: Message):
    if await is_admin(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "admin.user_management"),
            reply_markup=user_management_keyboard
        )
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(F.text == "👥 Barcha foydalanuvchilar")
async def list_all_users(message: Message):
    if await is_admin(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        async with bot.pool.acquire() as conn:
            users = await conn.fetch("SELECT * FROM users ORDER BY created_at DESC")
            if users:
                text = i18n.get_message(lang, "admin.user_list") + "\n\n"
                for user in users:
                    text += f"ID: {user['id']}\n"
                    text += f"Ism: {user['full_name']}\n"
                    text += f"Rol: {user['role']}\n"
                    text += f"Telegram ID: {user['telegram_id']}\n"
                    text += f"Telefon: {user['phone_number']}\n"
                    text += f"Ro'yxatdan o'tgan: {user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                    text += "-------------------\n"
                
                # Split message if too long
                if len(text) > 4000:
                    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                    for chunk in chunks:
                        await message.answer(chunk)
                else:
                    await message.answer(text)
            else:
                await message.answer(i18n.get_message(lang, "admin.no_users"))
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(F.text == "👨‍💼 Xodimlar")
async def list_staff(message: Message):
    if await is_admin(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        async with bot.pool.acquire() as conn:
            staff = await get_staff_members(conn)
            if staff:
                text = i18n.get_message(lang, "admin.staff_list") + "\n\n"
                for member in staff:
                    text += f"Ism: {member['full_name']}\n"
                    text += f"Rol: {member['role']}\n"
                    text += f"Telegram ID: {member['telegram_id']}\n"
                    text += "-------------------\n"
                await message.answer(text)
            else:
                await message.answer(i18n.get_message(lang, "admin.no_staff"))
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(F.text == "🔄 Rol o'zgartirish")
async def change_role(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "admin.search_method"),
            reply_markup=search_user_method_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_user_id_or_username)
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.callback_query(F.data == "search_by_telegram_id", AdminStates.waiting_for_user_id_or_username)
async def search_by_telegram_id_callback(call: CallbackQuery, state: FSMContext):
    if await is_admin(call.from_user.id):
        user = await get_user_by_telegram_id(call.from_user.id)
        lang = user.get('language', 'uz')
        await call.message.edit_text(i18n.get_message(lang, "admin.enter_telegram_id"))
        await state.set_state(AdminStates.waiting_for_telegram_id)
    else:
        await call.answer(i18n.get_message("uz", "admin.no_access"))

@router.callback_query(F.data == "search_by_phone", AdminStates.waiting_for_user_id_or_username)
async def search_by_phone_callback(call: CallbackQuery, state: FSMContext):
    if await is_admin(call.from_user.id):
        user = await get_user_by_telegram_id(call.from_user.id)
        lang = user.get('language', 'uz')
        await call.message.edit_text(i18n.get_message(lang, "admin.enter_phone"))
        await state.set_state(AdminStates.waiting_for_phone)
    else:
        await call.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(AdminStates.waiting_for_telegram_id)
async def process_telegram_id(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        try:
            target_telegram_id = int(message.text)
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            
            async with bot.pool.acquire() as conn:
                target_user = await conn.fetchrow(
                    """
                    SELECT full_name, role, phone_number, created_at, abonent_id 
                    FROM users 
                    WHERE telegram_id = $1
                    """,
                    target_telegram_id
                )
                
                if target_user:
                    user_info = (
                        f"👤 Foydalanuvchi ma'lumotlari:\n\n"
                        f"📝 Ism: {target_user['full_name']}\n"
                        f"📱 Telefon: {target_user['phone_number']}\n"
                        f"🆔 Telegram ID: {target_telegram_id}\n"
                        f"🔑 Abonent ID: {target_user['abonent_id'] or 'Mavjud emas'}\n"
                        f"📅 Ro'yxatdan o'tgan: {target_user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                        f"👥 Joriy rol: {target_user['role']}\n\n"
                        f"Yangi rolni tanlang:"
                    )
                    await message.answer(
                        user_info,
                        reply_markup=roles_keyboard(target_telegram_id)
                    )
                    await state.clear()
                else:
                    await message.answer(i18n.get_message(lang, "admin.user_not_found"))
        except ValueError:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            await message.answer(i18n.get_message(lang, "admin.invalid_format"))
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(AdminStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    if await is_admin(message.from_user.id):
        phone = message.text
        if not phone.startswith('+'):
            phone = '+' + phone
            
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        async with bot.pool.acquire() as conn:
            target_user = await conn.fetchrow(
                """
                SELECT telegram_id, full_name, role, phone_number, created_at, abonent_id 
                FROM users 
                WHERE phone_number = $1
                """,
                phone
            )
            
            if target_user:
                user_info = (
                    f"👤 Foydalanuvchi ma'lumotlari:\n\n"
                    f"📝 Ism: {target_user['full_name']}\n"
                    f"📱 Telefon: {target_user['phone_number']}\n"
                    f"🆔 Telegram ID: {target_user['telegram_id']}\n"
                    f"🔑 Abonent ID: {target_user['abonent_id'] or 'Mavjud emas'}\n"
                    f"📅 Ro'yxatdan o'tgan: {target_user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                    f"👥 Joriy rol: {target_user['role']}\n\n"
                    f"Yangi rolni tanlang:"
                )
                await message.answer(
                    user_info,
                    reply_markup=roles_keyboard(target_user['telegram_id'])
                )
                await state.clear()
            else:
                await message.answer(i18n.get_message(lang, "admin.user_not_found"))
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.callback_query(F.data.startswith("set_role_"))
async def set_role_callback(call: CallbackQuery):
    if await is_admin(call.from_user.id):
        try:
            parts = call.data.split("_")
            telegram_id = int(parts[-2])
            new_role = parts[-1]
            
            user = await get_user_by_telegram_id(call.from_user.id)
            lang = user.get('language', 'uz')
            
            async with bot.pool.acquire() as conn:
                target_user = await conn.fetchrow(
                    """
                    SELECT full_name, role, phone_number, created_at, abonent_id 
                    FROM users 
                    WHERE telegram_id = $1
                    """,
                    telegram_id
                )
                
                if target_user:
                    user_info = (
                        f"👤 Foydalanuvchi ma'lumotlari:\n\n"
                        f"📝 Ism: {target_user['full_name']}\n"
                        f"📱 Telefon: {target_user['phone_number']}\n"
                        f"🆔 Telegram ID: {telegram_id}\n"
                        f"🔑 Abonent ID: {target_user['abonent_id'] or 'Mavjud emas'}\n"
                        f"📅 Ro'yxatdan o'tgan: {target_user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                        f"👥 Joriy rol: {target_user['role']}\n"
                        f"🔄 Yangi rol: {new_role}\n\n"
                        f"Rolni o'zgartirishni tasdiqlaysizmi?"
                    )
                    
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="✅ Tasdiqlash", 
                                    callback_data=f"confirm_role_{telegram_id}_{new_role}"
                                ),
                                InlineKeyboardButton(
                                    text="❌ Bekor qilish", 
                                    callback_data="cancel_role_change"
                                )
                            ]
                        ]
                    )
                    
                    await call.message.edit_text(user_info, reply_markup=keyboard)
                else:
                    await call.message.edit_text(i18n.get_message(lang, "admin.user_not_found"))
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error in set_role_callback: {e}")
            await call.answer(i18n.get_message("uz", "admin.error_occurred"))
    else:
        await call.answer(i18n.get_message("uz", "admin.no_access"))

@router.callback_query(F.data.startswith("confirm_role_"))
async def confirm_role_change(call: CallbackQuery):
    if await is_admin(call.from_user.id):
        try:
            parts = call.data.split("_")
            telegram_id = int(parts[-2])
            new_role = parts[-1]
            
            user = await get_user_by_telegram_id(call.from_user.id)
            lang = user.get('language', 'uz')
            
            async with bot.pool.acquire() as conn:
                # Valid roles list - must match database constraint
                valid_roles = ['admin', 'operator', 'technician', 'manager', 'controller', 'warehouse', 'client', 'blocked']
                
                # Check if role is valid
                if new_role not in valid_roles:
                    await call.answer("Noto'g'ri rol turi!", show_alert=True)
                    return

                # Get current user role before update
                current_user = await conn.fetchrow(
                    'SELECT role FROM users WHERE telegram_id = $1',
                    telegram_id
                )

                if not current_user:
                    await call.answer("Foydalanuvchi topilmadi!", show_alert=True)
                    return

                if current_user['role'] == 'admin' and new_role != 'admin':
                    # Check if there's at least one other admin
                    admin_count = await conn.fetchval(
                        'SELECT COUNT(*) FROM users WHERE role = $1 AND telegram_id != $2',
                        'admin',
                        telegram_id
                    )
                    if admin_count < 1:
                        await call.answer("Kamida bitta admin bo'lishi kerak!", show_alert=True)
                        return

                try:
                    # Update role
                    await conn.execute(
                        'UPDATE users SET role = $1 WHERE telegram_id = $2',
                        new_role,
                        telegram_id
                    )
                except Exception as e:
                    logger.error(f"Database error in role update: {str(e)}")
                    await call.answer("Rolni o'zgartirishda xatolik yuz berdi!", show_alert=True)
                    return
                
                # Get updated user info
                target_user = await conn.fetchrow(
                    """
                    SELECT full_name, role, phone_number, created_at, abonent_id 
                    FROM users 
                    WHERE telegram_id = $1
                    """,
                    telegram_id
                )
                
                if target_user:
                    updated_info = (
                        f"✅ Rol muvaffaqiyatli o'zgartirildi!\n\n"
                        f"👤 Foydalanuvchi ma'lumotlari:\n\n"
                        f"📝 Ism: {target_user['full_name']}\n"
                        f"📱 Telefon: {target_user['phone_number']}\n"
                        f"🆔 Telegram ID: {telegram_id}\n"
                        f"🔑 Abonent ID: {target_user['abonent_id'] or 'Mavjud emas'}\n"
                        f"📅 Ro'yxatdan o'tgan: {target_user['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
                        f"👥 Yangi rol: {target_user['role']}"
                    )
                    
                    await call.message.edit_text(updated_info)
                else:
                    await call.message.edit_text(i18n.get_message(lang, "admin.user_not_found"))
            
        except Exception as e:
            logger.error(f"Error in confirm_role_change: {str(e)}")
            await call.answer(i18n.get_message("uz", "admin.error_occurred"), show_alert=True)
    else:
        await call.answer(i18n.get_message("uz", "admin.no_access"), show_alert=True)

@router.callback_query(F.data == "cancel_role_change")
async def cancel_role_change(call: CallbackQuery):
    if await is_admin(call.from_user.id):
        user = await get_user_by_telegram_id(call.from_user.id)
        lang = user.get('language', 'uz')
        await call.message.edit_text(i18n.get_message(lang, "admin.role_change_cancelled"))
    else:
        await call.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Statistika:", reply_markup=statistics_keyboard)
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.message(F.text == "📊 Umumiy statistika")
async def show_general_statistics(message: Message):
    if await is_admin(message.from_user.id):
        async with bot.pool.acquire() as conn:
            # Get total users
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            
            # Get total zayavki
            total_zayavki = await conn.fetchval("SELECT COUNT(*) FROM zayavki")
            
            # Get zayavki by status
            status_counts = await conn.fetch("""
                SELECT status, COUNT(*) as count 
                FROM zayavki 
                GROUP BY status
            """)
            
            # Get today's statistics
            today = datetime.now().date()
            today_zayavki = await conn.fetchval("""
                SELECT COUNT(*) FROM zayavki 
                WHERE DATE(created_at) = $1
            """, today)
            
            text = "📊 Umumiy statistika:\n\n"
            text += f"👥 Jami foydalanuvchilar: {total_users}\n"
            text += f"📋 Jami zayavkalar: {total_zayavki}\n"
            text += f"📅 Bugungi zayavkalar: {today_zayavki}\n\n"
            text += "Zayavkalar holati bo'yicha:\n"
            
            for status in status_counts:
                status_text = {
                    'new': '🆕 Yangi',
                    'in_progress': '⏳ Jarayonda',
                    'completed': '✅ Bajarilgan',
                    'cancelled': '❌ Bekor qilingan'
                }.get(status['status'], status['status'])
                text += f"{status_text}: {status['count']}\n"
            
            await message.answer(text)
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    if await is_admin(message.from_user.id):
        await message.answer("Sozlamalar:", reply_markup=settings_keyboard)
    else:
        await message.answer("Sizda admin huquqlari yo'q.")

@router.message(F.text == "◀️ Orqaga")
async def go_back(message: Message):
    if await is_admin(message.from_user.id):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(
            i18n.get_message(lang, "admin.main_menu"),
            reply_markup=admin_main_menu
        )
    else:
        await message.answer(i18n.get_message("uz", "admin.no_access"))

@router.message(UserStates.waiting_for_phone_number, F.contact)
async def process_contact(message: Message, state: FSMContext):
    """Process shared contact"""
    try:
        if message.contact.user_id != message.from_user.id:
            user = await get_user_by_telegram_id(message.from_user.id)
            lang = user.get('language', 'uz')
            await message.answer(i18n.get_message(lang, "admin.own_contact"))
            return

        phone_number = message.contact.phone_number
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        # Update user's phone number in database
        async with bot.pool.acquire() as conn:
            await conn.execute(
                'UPDATE users SET phone_number = $1 WHERE telegram_id = $2',
                phone_number,
                message.from_user.id
            )

        # Get user's language
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')

        # Show main menu
        await message.answer(
            text=i18n.get_message(lang, "welcome_back"),
            reply_markup=get_main_menu_keyboard(lang)
        )
        await state.set_state(UserStates.main_menu)

    except Exception as e:
        logger.error(f"Kontaktni qayta ishlashda xatolik: {str(e)}", exc_info=True)
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        await message.answer(i18n.get_message(lang, "error_occurred")) 