from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging

from database.admin_queries import (
    is_admin, get_user_management_stats, search_users_by_criteria,
    update_user_role, block_unblock_user, get_system_logs, log_admin_action
)
from database.base_queries import get_user_by_telegram_id, get_user_lang
from keyboards.admin_buttons import (
    get_user_management_keyboard, roles_keyboard, search_user_method_keyboard
)
from states.admin_states import AdminStates
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
from utils.logger import setup_logger
from utils.role_checks import admin_only

# Setup logger
logger = setup_logger('bot.admin.users')

def get_admin_users_router():
    router = Router()
    
    @router.message(F.text.in_(["👥 Foydalanuvchilar", "👥 Пользователи"]))
    @admin_only
    async def user_management_menu(message: Message, state: FSMContext):
        """User management main menu"""
        try:
            lang = await get_user_lang(message.from_user.id)
            
            # Get user management stats
            stats = await get_user_management_stats()
            
            if lang == 'uz':
                text = (
                    f"👥 <b>Foydalanuvchilar boshqaruvi</b>\n\n"
                    f"📊 <b>Statistika:</b>\n"
                )
                for stat in stats:
                    role_name = {
                        'client': 'Mijozlar',
                        'technician': 'Texniklar',
                        'manager': 'Menejerlar',
                        'admin': 'Adminlar',
                        'call_center': 'Call Center',
                        'controller': 'Kontrolyorlar',
                        'warehouse': 'Sklad'
                    }.get(stat['role'], stat['role'])
                    text += f"• {role_name}: <b>{stat['total']}</b> (faol: <b>{stat['active']}</b>)\n"
                
                text += f"\nKerakli amalni tanlang:"
            else:
                text = (
                    f"👥 <b>Управление пользователями</b>\n\n"
                    f"📊 <b>Статистика:</b>\n"
                )
                for stat in stats:
                    role_name = {
                        'client': 'Клиенты',
                        'technician': 'Техники',
                        'manager': 'Менеджеры',
                        'admin': 'Администраторы',
                        'call_center': 'Колл-центр',
                        'controller': 'Контроллеры',
                        'warehouse': 'Склад'
                    }.get(stat['role'], stat['role'])
                    text += f"• {role_name}: <b>{stat['total']}</b> (активных: <b>{stat['active']}</b>)\n"
                
                text += f"\nВыберите действие:"
            
            # Send message first
            sent_message = await message.answer(
                text,
                reply_markup=get_user_management_keyboard(lang)
            )
            
            # Then cleanup old messages
            await cleanup_user_inline_messages(message.from_user.id)
            
            # Finally set state
            await state.set_state(AdminStates.user_management)
            
            return sent_message
            
        except Exception as e:
            logger.error(f"Error in user management menu: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            
            # Ensure we send an error message
            sent_message = await message.answer(error_text)
            await cleanup_user_inline_messages(message.from_user.id)
            return sent_message

    @router.message(F.text.in_(["👥 Barcha foydalanuvchilar", "👥 Все пользователи"]))
    @admin_only
    async def list_all_users(message: Message):
        """List all users with pagination"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get all users (first 20)
            users = await search_users_by_criteria('role', 'client')
            users.extend(await search_users_by_criteria('role', 'technician'))
            users.extend(await search_users_by_criteria('role', 'manager'))
            users.extend(await search_users_by_criteria('role', 'admin'))
            
            if not users:
                text = "Foydalanuvchilar topilmadi." if lang == 'uz' else "Пользователи не найдены."
                await message.answer(text)
                return
            
            # Show first 10 users
            users_to_show = users[:10]
            
            if lang == 'uz':
                text = f"👥 <b>Foydalanuvchilar ro'yxati</b> (1-{len(users_to_show)} / {len(users)})\n\n"
            else:
                text = f"👥 <b>Список пользователей</b> (1-{len(users_to_show)} / {len(users)})\n\n"
            
            for i, user in enumerate(users_to_show, 1):
                role_name = {
                    'client': 'Mijoz' if lang == 'uz' else 'Клиент',
                    'technician': 'Texnik' if lang == 'uz' else 'Техник',
                    'manager': 'Menejer' if lang == 'uz' else 'Менеджер',
                    'admin': 'Admin' if lang == 'uz' else 'Админ',
                    'call_center': 'Call Center',
                    'controller': 'Kontrolyor' if lang == 'uz' else 'Контроллер',
                    'warehouse': 'Sklad' if lang == 'uz' else 'Склад'
                }.get(user['role'], user['role'])
                
                text += (
                    f"{i}. <b>{user.get('full_name', 'N/A')}</b>\n"
                    f"   📱 {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 {user['telegram_id']}\n"
                    f"   👤 {role_name}\n"
                    f"   📅 {user['created_at'].strftime('%d.%m.%Y')}\n\n"
                )
            
            # Add pagination buttons if needed
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            if len(users) > 10:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text="➡️ Keyingi" if lang == 'uz' else "➡️ Далее",
                        callback_data="users_page_2"
                    )
                ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🔍 Foydalanuvchi qidirish", "🔍 Поиск пользователя"]))
    @admin_only
    async def search_user_menu(message: Message, state: FSMContext):
        """Search user menu"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Qidirish usulini tanlang:" if lang == 'uz' else "Выберите способ поиска:"
            
            await message.answer(
                text,
                reply_markup=search_user_method_keyboard(lang)
            )
            await state.set_state(AdminStates.waiting_for_search_method)
            
        except Exception as e:
            logger.error(f"Error in search user menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("search_by_"))
    @admin_only
    async def search_method_selected(call: CallbackQuery, state: FSMContext):
        """Handle search method selection"""
        try:
            await cleanup_user_inline_messages(call.from_user.id)
            lang = await get_user_lang(call.from_user.id)
            
            search_type = call.data.split("_")[-1]  # telegram_id, phone, name, role
            
            await state.update_data(search_type=search_type)
            
            if search_type == "telegram_id":
                text = "Telegram ID ni kiriting:" if lang == 'uz' else "Введите Telegram ID:"
            elif search_type == "phone":
                text = "Telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона:"
            elif search_type == "name":
                text = "Ism yoki familiyani kiriting:" if lang == 'uz' else "Введите имя или фамилию:"
            elif search_type == "role":
                text = "Rolni tanlang:" if lang == 'uz' else "Выберите роль:"
                # Show role selection keyboard
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Mijoz" if lang == 'uz' else "Клиент", callback_data="role_client"),
                        InlineKeyboardButton(text="Texnik" if lang == 'uz' else "Техник", callback_data="role_technician")
                    ],
                    [
                        InlineKeyboardButton(text="Menejer" if lang == 'uz' else "Менеджер", callback_data="role_manager"),
                        InlineKeyboardButton(text="Admin", callback_data="role_admin")
                    ]
                ])
                await call.message.edit_text(text, reply_markup=keyboard)
                await state.set_state(AdminStates.waiting_for_role_selection)
                return
            
            await call.message.edit_text(text)
            await state.set_state(AdminStates.waiting_for_search_value)
            
        except Exception as e:
            logger.error(f"Error in search method selection: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("role_"), AdminStates.waiting_for_role_selection)
    @admin_only
    async def role_selected_for_search(call: CallbackQuery, state: FSMContext):
        """Handle role selection for search"""
        try:
            lang = await get_user_lang(call.from_user.id)
            role = call.data.split("_")[1]
            
            # Search users by role
            users = await search_users_by_criteria('role', role)
            
            if not users:
                text = f"Bu rolda foydalanuvchilar topilmadi." if lang == 'uz' else f"Пользователи с этой ролью не найдены."
                await call.message.edit_text(text)
                await state.clear()
                return
            
            # Show users
            await show_search_results(call.message, users, lang, edit=True)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error in role selection for search: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.message(AdminStates.waiting_for_search_value)
    @admin_only
    async def process_search_value(message: Message, state: FSMContext):
        """Process search value"""
        try:
            lang = await get_user_lang(message.from_user.id)
            data = await state.get_data()
            search_type = data.get('search_type')
            search_value = message.text.strip()
            
            if not search_value:
                text = "Qidiruv qiymati bo'sh bo'lishi mumkin emas." if lang == 'uz' else "Значение поиска не может быть пустым."
                await message.answer(text)
                return
            
            # Search users
            users = await search_users_by_criteria(search_type, search_value)
            
            if not users:
                text = "Foydalanuvchilar topilmadi." if lang == 'uz' else "Пользователи не найдены."
                await message.answer(text)
                await state.clear()
                return
            
            # Show search results
            await show_search_results(message, users, lang)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing search value: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)
            await state.clear()

    async def show_search_results(message, users, lang, edit=False):
        """Show search results"""
        try:
            if lang == 'uz':
                text = f"�� <b>Qidiruv natijalari</b> ({len(users)} ta topildi)\n\n"
            else:
                text = f"🔍 <b>Результаты поиска</b> (найдено {len(users)})\n\n"
            
            for i, user in enumerate(users[:5], 1):  # Show first 5 results
                role_name = {
                    'client': 'Mijoz' if lang == 'uz' else 'Клиент',
                    'technician': 'Texnik' if lang == 'uz' else 'Техник',
                    'manager': 'Menejer' if lang == 'uz' else 'Менеджер',
                    'admin': 'Admin' if lang == 'uz' else 'Админ',
                    'call_center': 'Call Center',
                    'controller': 'Kontrolyor' if lang == 'uz' else 'Контроллер',
                    'warehouse': 'Sklad' if lang == 'uz' else 'Склад'
                }.get(user['role'], user['role'])
                
                text += (
                    f"{i}. <b>{user.get('full_name', 'N/A')}</b>\n"
                    f"   📱 {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 {user['telegram_id']}\n"
                    f"   👤 {role_name}\n"
                    f"   📅 {user['created_at'].strftime('%d.%m.%Y')}\n"
                )
                
                # Add management buttons for each user
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔧 Boshqarish" if lang == 'uz' else "🔧 Управление",
                            callback_data=f"manage_user_{user['telegram_id']}"
                        )
                    ]
                ])
                text += "\n"
            
            if len(users) > 5:
                text += f"\n... va yana {len(users) - 5} ta natija"
            
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing search results: {e}")

    @router.callback_query(F.data.startswith("manage_user_"))
    @admin_only
    async def manage_user(call: CallbackQuery):
        """Manage specific user"""
        try:
            await cleanup_user_inline_messages(call.from_user.id)
            lang = await get_user_lang(call.from_user.id)
            
            telegram_id = int(call.data.split("_")[-1])
            
            # Get user details
            users = await search_users_by_criteria('telegram_id', str(telegram_id))
            if not users:
                text = "Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден."
                await call.message.edit_text(text)
                return
            
            user = users[0]
            
            if lang == 'uz':
                text = (
                    f"👤 <b>Foydalanuvchi boshqaruvi</b>\n\n"
                    f"📝 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                    f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"👤 <b>Joriy rol:</b> {user['role']}\n"
                    f"📅 <b>Ro'yxatdan o'tgan:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Amalni tanlang:"
                )
            else:
                text = (
                    f"👤 <b>Управление пользователем</b>\n\n"
                    f"📝 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
                    f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"👤 <b>Текущая роль:</b> {user['role']}\n"
                    f"📅 <b>Зарегистрирован:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Выберите действие:"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Rol o'zgartirish" if lang == 'uz' else "🔄 Изменить роль",
                        callback_data=f"change_role_{telegram_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔒 Bloklash" if lang == 'uz' else "🔒 Заблокировать",
                        callback_data=f"block_user_{telegram_id}"
                    ),
                    InlineKeyboardButton(
                        text="🔓 Blokdan chiqarish" if lang == 'uz' else "🔓 Разблокировать",
                        callback_data=f"unblock_user_{telegram_id}"
                    )
                ]
            ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error managing user: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("change_role_"))
    @admin_only
    async def change_user_role(call: CallbackQuery):
        """Change user role"""
        try:
            lang = await get_user_lang(call.from_user.id)
            telegram_id = int(call.data.split("_")[-1])
            
            text = "Yangi rolni tanlang:" if lang == 'uz' else "Выберите новую роль:"
            
            await call.message.edit_text(
                text,
                reply_markup=roles_keyboard(telegram_id, lang)
            )
            
        except Exception as e:
            logger.error(f"Error in change user role: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("set_role:"))
    @admin_only
    async def confirm_role_change(call: CallbackQuery):
        """Confirm role change"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            parts = call.data.split(":")
            new_role = parts[1]
            telegram_id = int(parts[2])
            
            # Get user details for confirmation
            users = await search_users_by_criteria('telegram_id', str(telegram_id))
            if not users:
                text = "Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден."
                await call.message.edit_text(text)
                return
            
            user = users[0]
            
            if lang == 'uz':
                text = (
                    f"🔄 <b>Rol o'zgartirishni tasdiqlash</b>\n\n"
                    f"👤 <b>Foydalanuvchi:</b> {user.get('full_name', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {telegram_id}\n"
                    f"👥 <b>Joriy rol:</b> {user['role']}\n"
                    f"🔄 <b>Yangi rol:</b> {new_role}\n\n"
                    f"Rolni o'zgartirishni tasdiqlaysizmi?"
                )
            else:
                text = (
                    f"🔄 <b>Подтверждение изменения роли</b>\n\n"
                    f"👤 <b>Пользователь:</b> {user.get('full_name', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {telegram_id}\n"
                    f"👥 <b>Текущая роль:</b> {user['role']}\n"
                    f"🔄 <b>Новая роль:</b> {new_role}\n\n"
                    f"Подтвердить изменение роли?"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Tasdiqlash" if lang == 'uz' else "✅ Подтвердить",
                        callback_data=f"confirm_role:{new_role}:{telegram_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Bekor qilish" if lang == 'uz' else "❌ Отменить",
                        callback_data="cancel_role_change"
                    )
                ]
            ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error confirming role change: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("confirm_role:"))
    @admin_only
    async def execute_role_change(call: CallbackQuery):
        """Execute role change"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            parts = call.data.split(":")
            new_role = parts[1]
            telegram_id = int(parts[2])
            
            # Update user role
            success = await update_user_role(telegram_id, new_role, call.from_user.id)
            
            if success:
                # Log admin action
                await log_admin_action(call.from_user.id, "role_change", {
                    "target_user": telegram_id,
                    "new_role": new_role
                })
                
                text = (
                    f"✅ Rol muvaffaqiyatli o'zgartirildi!\n\n"
                    f"👤 Foydalanuvchi: {telegram_id}\n"
                    f"🔄 Yangi rol: {new_role}"
                ) if lang == 'uz' else (
                    f"✅ Роль успешно изменена!\n\n"
                    f"👤 Пользователь: {telegram_id}\n"
                    f"🔄 Новая роль: {new_role}"
                )
                
                await call.message.edit_text(text)
                await call.answer("Rol o'zgartirildi!" if lang == 'uz' else "Роль изменена!")
            else:
                text = "Rolni o'zgartirishda xatolik yuz berdi." if lang == 'uz' else "Ошибка при изменении роли."
                await call.message.edit_text(text)
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
        except Exception as e:
            logger.error(f"Error executing role change: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data == "cancel_role_change")
    @admin_only
    async def cancel_role_change(call: CallbackQuery):
        """Cancel role change"""
        try:
            lang = await get_user_lang(call.from_user.id)
            text = "Rolni o'zgartirish bekor qilindi." if lang == 'uz' else "Изменение роли отменено."
            await call.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error canceling role change: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("block_user_"))
    @admin_only
    async def block_user(call: CallbackQuery):
        """Block user"""
        try:
            lang = await get_user_lang(call.from_user.id)
            telegram_id = int(call.data.split("_")[-1])
            
            success = await block_unblock_user(telegram_id, 'block', call.from_user.id)
            
            if success:
                await log_admin_action(call.from_user.id, "block_user", {"target_user": telegram_id})
                text = f"✅ Foydalanuvchi bloklandi." if lang == 'uz' else f"✅ Пользователь заблокирован."
                await call.answer("Foydalanuvchi bloklandi!" if lang == 'uz' else "Пользователь заблокирован!")
            else:
                text = "Foydalanuvchini bloklashda xatolik." if lang == 'uz' else "Ошибка при блокировке пользователя."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
            await call.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error blocking user: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("unblock_user_"))
    @admin_only
    async def unblock_user(call: CallbackQuery):
        """Unblock user"""
        try:
            lang = await get_user_lang(call.from_user.id)
            telegram_id = int(call.data.split("_")[-1])
            
            success = await block_unblock_user(telegram_id, 'unblock', call.from_user.id)
            
            if success:
                await log_admin_action(call.from_user.id, "unblock_user", {"target_user": telegram_id})
                text = f"✅ Foydalanuvchi blokdan chiqarildi." if lang == 'uz' else f"✅ Пользователь разблокирован."
                await call.answer("Foydalanuvchi blokdan chiqarildi!" if lang == 'uz' else "Пользователь разблокирован!")
            else:
                text = "Foydalanuvchini blokdan chiqarishda xatolik." if lang == 'uz' else "Ошибка при разблокировке пользователя."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
            await call.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error unblocking user: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.message(F.text.in_(["📋 Tizim loglari", "📋 Системные логи"]))
    @admin_only
    async def show_system_logs(message: Message):
        """Show system logs"""
        try:
            await cleanup_user_inline_messages(message.from_user.id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get recent logs
            logs = await get_system_logs('all', 20)
            
            if not logs:
                text = "Loglar topilmadi." if lang == 'uz' else "Логи не найдены."
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"📋 <b>Tizim loglari</b> (oxirgi 20 ta)\n\n"
            else:
                text = f"📋 <b>Системные логи</b> (последние 20)\n\n"
            
            for log in logs:
                log_type_name = {
                    'role_change': '🔄 Rol o\'zgartirish' if lang == 'uz' else '🔄 Изменение роли',
                    'user_action': '👤 Foydalanuvchi amali' if lang == 'uz' else '👤 Действие пользователя'
                }.get(log['log_type'], log['log_type'])
                
                text += (
                    f"{log_type_name}\n"
                    f"🆔 {log['user_telegram_id']}\n"
                    f"📝 {log['details']}\n"
                    f"📅 {log['timestamp'].strftime('%d.%m.%Y %H:%M')}\n\n"
                )
            
            # Split message if too long
            if len(text) > 4000:
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    await message.answer(chunk)
            else:
                await message.answer(text)
            
        except Exception as e:
            logger.error(f"Error showing system logs: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)
            
    # Return the router at the end of the function
    return router
