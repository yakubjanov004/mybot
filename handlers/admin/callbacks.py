from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from filters.role_filter import RoleFilter
from database.admin_queries import (
    search_users_by_criteria, update_user_role, block_unblock_user
)
from database.base_queries import get_user_lang, get_zayavka_by_id
from database.technician_queries import get_available_technicians
from states.admin_states import AdminStates
from utils.inline_cleanup import cleanup_user_inline_messages
from utils.logger import setup_logger
from utils.role_router import get_role_router
from keyboards.admin_buttons import get_admin_main_menu

logger = setup_logger('bot.admin.callbacks')

def get_admin_callbacks_router():
    router = get_role_router("admin")

    @router.callback_query(RoleFilter("admin"), F.data.startswith("search_by_"))
    async def search_method_selected(call: CallbackQuery, state: FSMContext):
        """Handle search method selection."""
        try:
            await cleanup_user_inline_messages(call.from_user.id)
            lang = await get_user_lang(call.from_user.id)
            search_type = call.data.replace('search_by_', '')
            await state.update_data(search_type=search_type)

            if search_type == "telegram_id":
                text = "Telegram ID ni kiriting:" if lang == 'uz' else "Введите Telegram ID:"
                await call.message.edit_text(text)
                await state.set_state(AdminStates.waiting_for_search_value)
            elif search_type == "phone":
                text = "Telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона:"
                await call.message.edit_text(text)
                await state.set_state(AdminStates.waiting_for_search_value)
            else:
                text = "Noto'g'ri qidiruv turi." if lang == 'uz' else "Неверный тип поиска."
                await call.message.edit_text(text)

        except Exception as e:
            logger.error(f"Error in search method selection: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("manage_user_"))
    async def manage_user(call: CallbackQuery):
        """Manage a specific user."""
        try:
            await cleanup_user_inline_messages(call.from_user.id)
            lang = await get_user_lang(call.from_user.id)
            telegram_id = int(call.data.split("_")[-1])
            users = await search_users_by_criteria('telegram_id', str(telegram_id))

            if not users:
                text = "Foydalanuvchi topilmadi." if lang == 'uz' else "Пользователь не найден."
                await call.message.edit_text(text)
                return

            user = users[0]
            text = (
                f"👤 <b>Foydalanuvchi boshqaruvi</b>\n\n"
                f"📝 <b>Ism:</b> {user.get('full_name', 'N/A')}\n"
                f"📱 <b>Telefon:</b> {user.get('phone_number', 'N/A')}\n"
                f"🆔 <b>Telegram ID:</b> {user['telegram_id']}\n"
                f"👤 <b>Joriy rol:</b> {user['role']}\n"
                f"📅 <b>Ro'yxatdan o'tgan:</b> {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Amalni tanlang:"
            ) if lang == 'uz' else (
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
                        text="🔄 Rolni o'zgartirish" if lang == 'uz' else "🔄 Изменить роль",
                        callback_data=f"change_role_{telegram_id}"
                    )
                ]
            ])
            await call.message.edit_text(text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error managing user: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("change_role_"))
    async def change_user_role(call: CallbackQuery):
        """Show roles as inline buttons for role change."""
        try:
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

        except Exception as e:
            logger.error(f"Error in change user role: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("set_role:"))
    async def confirm_role_change(call: CallbackQuery):
        """Confirm and apply the role change."""
        try:
            lang = await get_user_lang(call.from_user.id)
            _, new_role, telegram_id_str = call.data.split(":")
            telegram_id = int(telegram_id_str)

            success = await update_user_role(telegram_id, new_role, call.from_user.id)
            if success:
                await call.answer("Rol o'zgartirildi!" if lang == 'uz' else "Роль изменена!")
                await manage_user(call)  # Refresh user info
            else:
                text = "Rolni o'zgartirishda xatolik yuz berdi." if lang == 'uz' else "Ошибка при изменении роли."
                await call.message.edit_text(text)
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")

        except Exception as e:
            logger.error(f"Error confirming role change: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("block_user_"))
    async def block_user(call: CallbackQuery):
        """Block a user."""
        await _toggle_user_block(call, 'block')


    @router.callback_query(RoleFilter("admin"), F.data.startswith("unblock_user_"))
    async def unblock_user(call: CallbackQuery):
        """Unblock a user."""
        await _toggle_user_block(call, 'unblock')


    async def _toggle_user_block(call: CallbackQuery, action: str):
        """Helper to block or unblock a user."""
        try:
            lang = await get_user_lang(call.from_user.id)
            telegram_id = int(call.data.split("_")[-1])

            success = await block_unblock_user(telegram_id, action, call.from_user.id)
            if success:
                if action == 'block':
                    text = "✅ Foydalanuvchi bloklandi." if lang == 'uz' else "✅ Пользователь заблокирован."
                    answer_text = "Foydalanuvchi bloklandi!" if lang == 'uz' else "Пользователь заблокирован!"
                else:
                    text = "✅ Foydalanuvchi blokdan chiqarildi." if lang == 'uz' else "✅ Пользователь разблокирован."
                    answer_text = "Foydalanuvchi blokdan chiqarildi!" if lang == 'uz' else "Пользователь разблокирован!"
                
                await call.answer(answer_text)
                await call.message.edit_text(text)
            else:
                error_text = "Amalni bajarishda xatolik." if lang == 'uz' else "Ошибка при выполнении действия."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
                await call.message.edit_text(error_text)

        except Exception as e:
            logger.error(f"Error toggling user block (action: {action}): {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("assign_order_"))
    async def assign_order(call: CallbackQuery):
        """Assign order to technician"""
        try:
            lang = await get_user_lang(call.from_user.id)
            order_id = int(call.data.split("_")[-1])
            technicians = await get_available_technicians()

            if not technicians:
                text = "Mavjud texniklar yo'q." if lang == 'uz' else "Нет доступных техников."
                await call.message.edit_text(text)
                return

            text = "Texnikni tanlang:" if lang == 'uz' else "Выберите техника:"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"👨‍🔧 {tech['full_name']} ({tech.get('active_tasks', 0)} vazifa)",
                    callback_data=f"confirm_assign_{order_id}_{tech['id']}"
                )] for tech in technicians[:10]
            ])
            await call.message.edit_text(text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error assigning order: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("confirm_assign_"))
    async def confirm_assign_order(call: CallbackQuery):
        """Confirm order assignment"""
        try:
            lang = await get_user_lang(call.from_user.id)
            parts = call.data.split("_")
            order_id, technician_id = int(parts[2]), int(parts[3])

            success = await assign_zayavka_to_technician(order_id, technician_id, call.from_user.id)
            if success:
                text = f"✅ Zayavka #{order_id} texnikga tayinlandi." if lang == 'uz' else f"✅ Заявка #{order_id} назначена технику."
                await call.answer("Tayinlandi!" if lang == 'uz' else "Назначено!")
            else:
                text = "Zayavkani tayinlashda xatolik." if lang == 'uz' else "Ошибка при назначении заявки."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
            await call.message.edit_text(text)

        except Exception as e:
            logger.error(f"Error confirming order assignment: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("order_details_"))
    async def show_order_details(call: CallbackQuery):
        """Show detailed order information"""
        try:
            lang = await get_user_lang(call.from_user.id)
            order_id = int(call.data.split("_")[-1])
            order = await get_zayavka_by_id(order_id)

            if not order:
                await call.message.edit_text("Zayavka topilmadi." if lang == 'uz' else "Заявка не найдена.")
                return

            text = "..."  # Populate with order details as before
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            # Add buttons as before
            
            await call.message.edit_text(text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error showing order details: {e}", exc_info=True)
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")


    @router.callback_query(RoleFilter("admin"), F.data.startswith("change_status_"))
    async def change_order_status(call: CallbackQuery):
        """Change order status"""
        # Implementation from orders.py
        pass


    @router.callback_query(RoleFilter("admin"), F.data.startswith("set_status_"))
    async def set_order_status(call: CallbackQuery):
        """Set order status"""
        # Implementation from orders.py
        pass


    @router.callback_query(RoleFilter("admin"), F.data.in_(["back", "orqaga", "назад"]))
    async def admin_back(call: CallbackQuery, state: FSMContext):
        lang = await get_user_lang(call.from_user.id)
        text = "Admin paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в админ-панель!"
        await call.message.edit_text(text, reply_markup=get_admin_main_menu(lang))
        await state.set_state(AdminStates.main_menu)
        await call.answer()

    return router