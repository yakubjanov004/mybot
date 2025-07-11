from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database.admin_queries import (
    get_user_management_stats, search_users_by_criteria, update_user_role,
    block_unblock_user, get_system_logs, log_admin_action
)
from database.base_queries import get_user_by_telegram_id, get_user_lang
from keyboards.admin_buttons import get_user_management_keyboard, roles_keyboard, search_user_method_keyboard, get_admin_main_menu
from states.admin_states import AdminUserStates, AdminMainMenuStates
from utils.inline_cleanup import cleanup_user_inline_messages, answer_and_cleanup
from utils.logger import setup_logger
from utils.role_checks import admin_only
from loader import inline_message_manager
from aiogram.filters import StateFilter
from utils.role_router import get_role_router

logger = setup_logger('bot.admin.users')

def get_admin_users_router():
    router = get_role_router("admin")

    @router.message(StateFilter(AdminMainMenuStates.main_menu), F.text.in_(['👥 Foydalanuvchilar', '👥 Пользователи']))
    @admin_only
    async def user_management_menu(message: Message, state: FSMContext):
        """User management main menu"""
        try:
            lang = await get_user_lang(message.from_user.id)
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
            sent_message = await message.answer(
                text,
                reply_markup=get_user_management_keyboard(lang)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(AdminUserStates.user_management)
            return sent_message
        except Exception as e:
            logger.error(f"Error in user management menu: {e}", exc_info=True)
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            sent_message = await message.answer(error_text)
            await cleanup_user_inline_messages(message.from_user.id)
            return sent_message

    @router.message(F.text.in_(['🔒 Bloklash/Blokdan chiqarish', '🔒 Блокировка/Разблокировка']))
    @admin_only
    async def block_unblock_menu(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        text = (
            "Foydalanuvchini bloklash yoki blokdan chiqarish uchun qidiruv usulini tanlang:" if lang == 'uz' else
            "Выберите способ поиска пользователя для блокировки/разблокировки:"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆔 Telegram ID", callback_data="block_search_by_telegram_id")],
            [InlineKeyboardButton(text="📱 Telefon" if lang == 'uz' else "📱 Телефон", callback_data="block_search_by_phone")]
        ])
        await message.answer(text, reply_markup=keyboard)
        await state.set_state(AdminUserStates.blocking)

    @router.callback_query(F.data.startswith("block_search_by_"), AdminUserStates.blocking)
    @admin_only
    async def block_search_method_selected(call: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(call.from_user.id)
        search_type = call.data.replace('block_search_by_', '')
        await state.update_data(block_search_type=search_type)
        if search_type == "telegram_id":
            text = "Telegram ID ni kiriting:" if lang == 'uz' else "Введите Telegram ID:"
        elif search_type == "phone":
            text = "Telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона:"
        else:
            text = "Noto'g'ri qidiruv turi." if lang == 'uz' else "Неверный тип поиска."
        await call.message.edit_text(text)
        await state.set_state(AdminUserStates.blocking)

    @router.message(AdminUserStates.blocking)
    @admin_only
    async def process_block_unblock_id(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        data = await state.get_data()
        search_type = data.get('block_search_type', 'telegram_id')
        search_value = message.text.strip()
        user = None
        if search_type == 'telegram_id':
            if not search_value.isdigit():
                await message.answer("Telegram ID raqam bo'lishi kerak." if lang == 'uz' else "Telegram ID должен быть числом.")
                return
            user = await get_user_by_telegram_id(int(search_value))
        elif search_type == 'phone':
            user_list = await search_users_by_criteria('phone', search_value)
            user = user_list[0] if user_list else None
        if not user:
            await message.answer("Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден.")
            return
        # Foydalanuvchi haqida to'liq ma'lumot
        status = "Bloklangan" if not user.get('is_active', True) or user.get('role') == 'blocked' else "Faol"
        text = (
            f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
            f"📝 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
            f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
            f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
            f"👤 <b>Joriy rol:</b> {user['role']}\n"
            f"📅 <b>Ro'yxatdan o'tgan:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"🔘 <b>Holati:</b> {status}\n\n"
        ) if lang == 'uz' else (
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"📝 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
            f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
            f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
            f"👤 <b>Текущая роль:</b> {user['role']}\n"
            f"📅 <b>Зарегистрирован:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"🔘 <b>Статус:</b> {status}\n\n"
        )
        if not user.get('is_active', True) or user.get('role') == 'blocked':
            # Blokdan chiqarish tugmasi
            text += "Foydalanuvchi bloklangan. Blokdan chiqarish uchun tugmani bosing:" if lang == 'uz' else "Пользователь заблокирован. Для разблокировки нажмите кнопку ниже:"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔓 Blokdan chiqarish" if lang == 'uz' else "🔓 Разблокировать", callback_data=f"unblock_user:{user['telegram_id']}")]
            ])
        else:
            # Bloklash tugmasi
            text += "Foydalanuvchi faol. Bloklash uchun tugmani bosing:" if lang == 'uz' else "Пользователь активен. Для блокировки нажмите кнопку ниже:"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔒 Bloklash" if lang == 'uz' else "🔒 Блокировать", callback_data=f"block_user:{user['telegram_id']}")]
            ])
        await message.answer(text, reply_markup=keyboard)
        await state.clear()

    @router.callback_query(F.data.startswith("block_user:"))
    @admin_only
    async def block_user(call: CallbackQuery):
        lang = await get_user_lang(call.from_user.id)
        telegram_id = int(call.data.split(":")[-1])
        # Foydalanuvchini bloklash: ro'lini 'blocked' va is_active ni false qilamiz
        success = await update_user_role(telegram_id, 'blocked', call.from_user.id)
        if success:
            await block_unblock_user(telegram_id, 'block', call.from_user.id)
            user = await get_user_by_telegram_id(telegram_id)
            text = (
                f"✅ Foydalanuvchi bloklandi!\n\n" if lang == 'uz' else f"✅ Пользователь заблокирован!\n\n"
            )
            text += (
                f"📝 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"👤 <b>Joriy rol:</b> {user['role']}\n"
                f"📅 <b>Ro'yxatdan o'tgan:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            ) if lang == 'uz' else (
                f"📝 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
                f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"👤 <b>Текущая роль:</b> {user['role']}\n"
                f"📅 <b>Зарегистрирован:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            )
            await call.message.edit_text(text)
            await call.answer("Foydalanuvchi bloklandi!" if lang == 'uz' else "Пользователь заблокирован!")
        else:
            await call.message.edit_text("Bloklashda xatolik yuz berdi." if lang == 'uz' else "Ошибка при блокировке пользователя.")
            await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")

    @router.callback_query(F.data.startswith("unblock_user:"))
    @admin_only
    async def unblock_user(call: CallbackQuery):
        lang = await get_user_lang(call.from_user.id)
        telegram_id = int(call.data.split(":")[-1])
        # Foydalanuvchini blokdan chiqarish: ro'lini avvalgi holatga qaytarish (bu yerda qo'lda tanlash yoki logdan olish mumkin, hozircha 'client' qilamiz)
        # TODO: Agar avvalgi ro'lni saqlash kerak bo'lsa, uni alohida logda saqlash va qaytarish kerak
        success = await update_user_role(telegram_id, 'client', call.from_user.id)
        if success:
            await block_unblock_user(telegram_id, 'unblock', call.from_user.id)
            user = await get_user_by_telegram_id(telegram_id)
            text = (
                f"✅ Foydalanuvchi blokdan chiqarildi!\n\n" if lang == 'uz' else f"✅ Пользователь разблокирован!\n\n"
            )
            text += (
                f"📝 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"👤 <b>Joriy rol:</b> {user['role']}\n"
                f"📅 <b>Ro'yxatdan o'tgan:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            ) if lang == 'uz' else (
                f"📝 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
                f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"👤 <b>Текущая роль:</b> {user['role']}\n"
                f"📅 <b>Зарегистрирован:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            )
            await call.message.edit_text(text)
            await call.answer("Foydalanuvchi blokdan chiqarildi!" if lang == 'uz' else "Пользователь разблокирован!")
        else:
            await call.message.edit_text("Blokdan chiqarishda xatolik yuz berdi." if lang == 'uz' else "Ошибка при разблокировке пользователя.")
            await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")

    @router.message(F.text.in_(["👥 Barcha foydalanuvchilar", "👥 Все пользователи"]))
    @admin_only
    async def list_all_users(message: Message, state: FSMContext):
        """List all users with pagination (first page)"""
        await show_users_page(message, page=1, edit=False)

    @router.callback_query(F.data.startswith("users_page_"))
    @admin_only
    async def users_page_callback(call: CallbackQuery, state: FSMContext):
        """Handle pagination for users list"""
        page = int(call.data.split("_")[-1])
        await show_users_page(call, page=page, edit=True)

    @router.message(F.text.in_(["👤 Xodimlar", "👤 Сотрудники"]))
    @admin_only
    async def list_technicians(message: Message, state: FSMContext):
        """List all technicians with pagination (first page)"""
        await show_technicians_page(message, page=1, edit=False)

    @router.callback_query(F.data.startswith("technicians_page_"))
    @admin_only
    async def technicians_page_callback(call: CallbackQuery, state: FSMContext):
        """Handle pagination for technicians list"""
        page = int(call.data.split("_")[-1])
        await show_technicians_page(call, page=page, edit=True)

    async def show_users_page(event, page=1, edit=False):
        lang = await get_user_lang(event.from_user.id)
        # Get all users (all roles)
        users = await search_users_by_criteria('role', 'client')
        users.extend(await search_users_by_criteria('role', 'technician'))
        users.extend(await search_users_by_criteria('role', 'manager'))
        users.extend(await search_users_by_criteria('role', 'admin'))
        users = sorted(users, key=lambda u: u.get('created_at', ''))
        per_page = 10
        total = len(users)
        max_page = (total + per_page - 1) // per_page
        if total == 0:
            text = "Foydalanuvchilar topilmadi." if lang == 'uz' else "Пользователи не найдены."
            if edit:
                await event.message.edit_text(text)
            else:
                await event.answer(text)
            return
        start = (page - 1) * per_page
        end = start + per_page
        users_to_show = users[start:end]
        if lang == 'uz':
            text = f"👥 <b>Foydalanuvchilar ro'yxati</b> ({start+1}-{min(end, total)} / {total})\n\n"
        else:
            text = f"👥 <b>Список пользователей</b> ({start+1}-{min(end, total)} / {total})\n\n"
        for i, user in enumerate(users_to_show, start+1):
            role_name = {
                'client': 'Mijoz' if lang == 'uz' else 'Клиент',
                'technician': 'Texnik' if lang == 'uz' else 'Техник',
                'manager': 'Menejer' if lang == 'uz' else 'Менеджер',
                'admin': 'Admin' if lang == 'uz' else 'Админ',
                'call_center': 'Call Center',
                'controller': 'Kontrolyor' if lang == 'uz' else 'Контроллер',
                'warehouse': 'Sklad' if lang == 'uz' else 'Склад'
            }.get(user['role'], user['role'])
            if lang == 'uz':
                text += (
                    f"{i}. 👤 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                    f"   📞 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"   🏷️ <b>Rol:</b> {role_name}\n"
                    f"   📅 <b>Ro'yxatdan o'tgan sana:</b> {user['created_at'].strftime('%d.%m.%Y')}\n\n"
                )
            else:
                text += (
                    f"{i}. 👤 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
                    f"   📞 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"   🏷️ <b>Роль:</b> {role_name}\n"
                    f"   📅 <b>Дата регистрации:</b> {user['created_at'].strftime('%d.%m.%Y')}\n\n"
                )
        # Pagination buttons
        keyboard = []
        if page > 1:
            keyboard.append(InlineKeyboardButton(text="⬅️ Oldingi" if lang == 'uz' else "⬅️ Назад", callback_data=f"users_page_{page-1}"))
        if page < max_page:
            keyboard.append(InlineKeyboardButton(text="Keyingi ➡️" if lang == 'uz' else "Далее ➡️", callback_data=f"users_page_{page+1}"))
        markup = InlineKeyboardMarkup(inline_keyboard=[keyboard] if keyboard else [])
        if edit:
            await event.message.edit_text(text, reply_markup=markup)
        else:
            await event.answer(text, reply_markup=markup)

    async def show_technicians_page(event, page=1, edit=False):
        lang = await get_user_lang(event.from_user.id)
        # Xodimlar ro'yxatini olish (technician, manager, controller, warehouse, call_center, admin)
        users = []
        for role in ['technician', 'manager', 'controller', 'warehouse', 'call_center', 'admin']:
            users.extend(await search_users_by_criteria('role', role))
        users = sorted(users, key=lambda u: u.get('created_at', ''))
        per_page = 10
        total = len(users)
        max_page = (total + per_page - 1) // per_page
        if total == 0:
            text = "Xodimlar topilmadi." if lang == 'uz' else "Сотрудники не найдены."
            if edit:
                await event.message.edit_text(text)
            else:
                await event.answer(text)
            return
        start = (page - 1) * per_page
        end = start + per_page
        users_to_show = users[start:end]
        if lang == 'uz':
            text = f"👤 <b>Xodimlar ro'yxati</b> ({start+1}-{min(end, total)} / {total})\n\n"
        else:
            text = f"👤 <b>Список сотрудников</b> ({start+1}-{min(end, total)} / {total})\n\n"
        for i, user in enumerate(users_to_show, start+1):
            if lang == 'uz':
                # Role names in Uzbek
                role_names = {
                    'technician': 'Texnik',
                    'manager': 'Menejer',
                    'controller': 'Kontrolyor',
                    'warehouse': 'Sklad',
                    'call_center': 'Call Center',
                    'admin': 'Admin'
                }
                role_name = role_names.get(user['role'], user['role'])
                text += (
                    f"{i}. 👤 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                    f"   📞 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"   🏷️ <b>Rol:</b> {role_name}\n"
                    f"   📅 <b>Ro'yxatdan o'tgan sana:</b> {user['created_at'].strftime('%d.%m.%Y')}\n\n"
                )
            else:
                # Role names in Russian
                role_names = {
                    'technician': 'Техник',
                    'manager': 'Менеджер',
                    'controller': 'Контроллер',
                    'warehouse': 'Склад',
                    'call_center': 'Колл-центр',
                    'admin': 'Админ'
                }
                role_name = role_names.get(user['role'], user['role'])
                text += (
                    f"{i}. 👤 <b>Имя:</b> {user.get('full_name', 'N/A')}\n"
                    f"   📞 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                    f"   🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                    f"   🏷️ <b>Роль:</b> {role_name}\n"
                    f"   📅 <b>Дата регистрации:</b> {user['created_at'].strftime('%d.%m.%Y')}\n\n"
                )
        # Pagination buttons
        keyboard = []
        if page > 1:
            keyboard.append(InlineKeyboardButton(text="⬅️ Oldingi" if lang == 'uz' else "⬅️ Назад", callback_data=f"technicians_page_{page-1}"))
        if page < max_page:
            keyboard.append(InlineKeyboardButton(text="Keyingi ➡️" if lang == 'uz' else "Далее ➡️", callback_data=f"technicians_page_{page+1}"))
        markup = InlineKeyboardMarkup(inline_keyboard=[keyboard] if keyboard else [])
        if edit:
            await event.message.edit_text(text, reply_markup=markup)
        else:
            await event.answer(text, reply_markup=markup)

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
            await state.set_state(AdminUserStates.waiting_for_search_method)
        except Exception as e:
            logger.error(f"Error in search user menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("change_role_"))
    @admin_only
    async def change_user_role(call: CallbackQuery):
        lang = await get_user_lang(call.from_user.id)
        telegram_id = int(call.data.split("_")[-1])
        text = "Yangi rolni tanlang:" if lang == 'uz' else "Выберите новую роль:"
        roles = [
            ("client", "👤 Mijoz", "👤 Клиент"),
            ("technician", "👨‍🔧 Texnik", "👨‍🔧 Техник"),
            ("manager", "👨‍💼 Menejer", "👨‍💼 Менеджер"),
            ("admin", "🏢 Admin", "🏢 Админ"),
            ("call_center", "📞 Call Center", "📞 Колл-центр"),
            ("controller", "🎯 Kontrolyor", "🎯 Контроллер"),
            ("warehouse", "📦 Sklad", "📦 Склад")
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=uz if lang == 'uz' else ru, callback_data=f"set_role:{role}:{telegram_id}")]
            for role, uz, ru in roles
        ])
        await call.message.edit_text(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("set_role:"))
    @admin_only
    async def confirm_role_change(call: CallbackQuery):
        try:
            lang = await get_user_lang(call.from_user.id)
            parts = call.data.split(":")
            new_role = parts[1]
            telegram_id = int(parts[2])
            
            # Get user info
            user = await get_user_by_telegram_id(telegram_id)
            if not user:
                text = "Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден."
                await call.message.edit_text(text)
                return
                
            # Update user role
            await update_user_role(telegram_id, new_role, call.from_user.id)
            
            # Log the action
            await log_admin_action(
                call.from_user.id,
                "role_change",
                {"user_id": telegram_id, "new_role": new_role, "old_role": user['role']}
            )
            
            success = await update_user_role(telegram_id, new_role, call.from_user.id)
            if success:
                updated_users = await search_users_by_criteria('telegram_id', str(telegram_id))
                updated_user = updated_users[0] if updated_users else user
                text = (
                    f"✅ Rol muvaffaqiyatli o'zgartirildi!\n\n"
                    f"👤 <b>Foydalanuvchi boshqaruvi</b>\n\n"
                    f"📝 <b>Ism:</b> {updated_user.get('full_name', 'N/A')}\n"
                    f"📱 <b>Telefon:</b> {updated_user.get('phone_number', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {updated_user['telegram_id']}\n"
                    f"👤 <b>Joriy rol:</b> {updated_user['role']}\n"
                    f"📅 <b>Ro'yxatdan o'tgan:</b> {updated_user['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Rolni o'zgartirish uchun pastdagi tugmani bosing:"
                ) if lang == 'uz' else (
                    f"✅ Роль успешно изменена!\n\n"
                    f"👤 <b>Управление пользователем</b>\n\n"
                    f"📝 <b>Имя:</b> {updated_user.get('full_name', 'N/A')}\n"
                    f"📱 <b>Телефон:</b> {updated_user.get('phone_number', 'N/A')}\n"
                    f"🆔 <b>Telegram ID:</b> {updated_user['telegram_id']}\n"
                    f"👤 <b>Текущая роль:</b> {updated_user['role']}\n"
                    f"📅 <b>Зарегистрирован:</b> {updated_user['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Для смены роли нажмите кнопку ниже:"
                )
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔄 Rolni o'zgartirish" if lang == 'uz' else "🔄 Изменить роль",
                            callback_data=f"change_role_{updated_user['telegram_id']}"
                        )
                    ]
                ])
                await call.message.edit_text(text, reply_markup=keyboard)
                await call.answer("Rol o'zgartirildi!" if lang == 'uz' else "Роль изменена!")
            else:
                text = "Rolni o'zgartirishda xatolik yuz berdi." if lang == 'uz' else "Ошибка при изменении роли."
                await call.message.edit_text(text)
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
        except Exception as e:
            logger.error(f"Error in confirm_role_change: {e}", exc_info=True)
            lang = await get_user_lang(call.from_user.id)
            text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await call.message.edit_text(text)

    @router.message(AdminUserStates.waiting_for_role_change_id)
    @admin_only
    async def process_role_change_id(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        try:
            telegram_id = int(message.text.strip())
            user = await get_user_by_telegram_id(telegram_id)
            if not user:
                text = "Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден."
                await message.answer(text)
                return
            text = (
                f"👤 <b>Foydalanuvchi:</b> {user.get('full_name', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                f"🏷️ <b>Joriy rol:</b> {user.get('role', 'N/A')}\n\n"
                f"Yangi rolni tanlang:" if lang == 'uz' else
                f"👤 <b>Пользователь:</b> {user.get('full_name', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
                f"🏷️ <b>Текущая роль:</b> {user.get('role', 'N/A')}\n\n"
                f"Выберите новую роль:"
            )
            await message.answer(text, reply_markup=roles_keyboard(user['telegram_id'], lang))
            await state.clear()
        except Exception as e:
            await message.answer("Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка.")

    @router.message(AdminUserStates.waiting_for_role_change_phone)
    @admin_only
    async def process_role_change_phone(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        phone = message.text.strip()
        # Search users by phone (partial match allowed)
        from database.base_queries import search_users
        users = await search_users(phone, limit=5)
        if not users:
            await message.answer("Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден.")
            return
        if len(users) > 1:
            # If multiple users found, show a list
            text = ("Bir nechta foydalanuvchi topildi. Iltimos, aniq telefon raqamini kiriting yoki quyidagilardan tanlang:" if lang == 'uz'
                    else "Найдено несколько пользователей. Пожалуйста, уточните номер или выберите из списка:")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{u.get('full_name', 'N/A')} ({u.get('phone_number', 'N/A')})",
                    callback_data=f"change_role_{u['telegram_id']}"
                )] for u in users
            ])
            await message.answer(text, reply_markup=keyboard)
            return
        user = users[0]
        text = (
            f"👤 <b>Foydalanuvchi:</b> {user.get('full_name', 'N/A')}\n"
            f"📱 <b>Telegram ID:</b> {user['telegram_id']}\n"
            f"📱 <b>Teleфон:</b> {user.get('phone_number', 'N/A')}\n"
            f"🏷️ <b>Joriy rol:</b> {user.get('role', 'N/A')}\n\n"
            f"Yangi rolni tanlang:" if lang == 'uz' else
            f"👤 <b>Пользователь:</b> {user.get('full_name', 'N/A')}\n"
            f"📱 <b>Telegram ID:</b> {user['telegram_id']}\n"
            f"📱 <b>Телефон:</b> {user.get('phone_number', 'N/A')}\n"
            f"🏷️ <b>Текущая роль:</b> {user.get('role', 'N/A')}\n\n"
            f"Выберите новую роль:"
        )
        await message.answer(text, reply_markup=roles_keyboard(user['telegram_id'], lang))
        await state.clear()

    @router.message(F.text.in_(["◀️ Orqaga", "◀️ Назад"]))
    @admin_only
    async def back_to_admin_menu(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        text = "Asosiy admin menyuga qaytdingiz." if lang == 'uz' else "Вы вернулись в главное меню администратора."
        await message.answer(text, reply_markup=get_admin_main_menu(lang))
        await state.set_state(AdminMainMenuStates.main_menu)

    @router.message(F.text.in_(["🔄 Rolni o'zgartirish", "🔄 Изменить роль"]))
    @admin_only
    async def role_change_menu(message: Message, state: FSMContext):
        lang = await get_user_lang(message.from_user.id)
        text = "Rolni o'zgartirish usulini tanlang:" if lang == 'uz' else "Выберите способ смены роли:"
        await message.answer(text, reply_markup=search_user_method_keyboard(lang))
        await state.set_state(AdminUserStates.waiting_for_search_method)

    @router.callback_query(F.data == "search_by_telegram_id", AdminUserStates.waiting_for_search_method)
    @admin_only
    async def role_change_by_telegram_id(call: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(call.from_user.id)
        text = "Foydalanuvchi Telegram ID sini kiriting:" if lang == 'uz' else "Введите Telegram ID пользователя:"
        await call.message.edit_text(text)
        await state.set_state(AdminUserStates.waiting_for_role_change_id)
        await call.answer()

    @router.callback_query(F.data == "search_by_phone", AdminUserStates.waiting_for_search_method)
    @admin_only
    async def role_change_by_phone(call: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(call.from_user.id)
        text = "Foydalanuvchi telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона пользователя:"
        await call.message.edit_text(text)
        await state.set_state(AdminUserStates.waiting_for_role_change_phone)
        await call.answer()

    return router
