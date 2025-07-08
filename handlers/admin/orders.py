from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging
from datetime import datetime, timedelta

from database.admin_queries import (
    get_orders_management_stats, get_filtered_orders, bulk_assign_orders, log_admin_action
)
from database.base_queries import (
    get_zayavka_by_id, update_zayavka_status, assign_zayavka_to_technician,
    get_user_by_telegram_id, get_user_lang
)
from database.technician_queries import get_available_technicians
from keyboards.admin_buttons import (
    get_zayavka_main_keyboard,
    get_zayavka_status_filter_keyboard,
    get_zayavka_filter_menu_keyboard,
    get_zayavka_section_keyboard
)
from states.admin_states import AdminStates
from utils.inline_cleanup import (
    answer_and_cleanup, safe_delete_message, cleanup_user_inline_messages
)
from utils.logger import setup_logger
from utils.role_router import get_role_router
from utils.role_checks import admin_only
from loader import inline_message_manager
from aiogram.filters import StateFilter

def format_order(order: dict, lang: str) -> str:
    """Format order details in both Uzbek and Russian"""
    return (
        f"🆔 #{order['id']}\n"
        f"👤 {order.get('client_name', 'N/A')}\n"
        f"📱 {order.get('client_phone', 'N/A')}\n"
        f"📍 {order.get('address', 'N/A')}\n"
        f"📝 {order.get('title', 'N/A')}\n"
        f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{"Holat: " if lang == 'uz' else "Статус: "}"
        f"{order.get('status', 'N/A')}\n\n"
        f"{"Texnik: " if lang == 'uz' else "Техник: "}"
        f"{order.get('technician_name', 'N/A')}\n\n"
        f"{"Qo'shimcha ma'lumotlar: " if lang == 'uz' else "Дополнительная информация: "}"
        f"{order.get('description', 'N/A')}")

# Setup logger
logger = setup_logger('bot.admin.orders')

def get_admin_orders_router():
    router = get_role_router("admin")
    
    @router.message(StateFilter(AdminStates.main_menu), F.text.in_(["📝 Zayavkalar", "📝 Заявки"]))
    @admin_only
    async def orders_menu(message: Message, state: FSMContext):
        """Show orders menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get orders statistics
            stats = await get_orders_management_stats()
            
            if lang == 'uz':
                text = "📊 <b>Zayavkalar statistikasi</b>\n\n"
                text += f"Yangi: {stats.get('new', 0)}\n"
                text += f"Jarayonda: {stats.get('in_progress', 0)}\n"
                text += f"Bajarilgan: {stats.get('completed', 0)}\n"
                text += f"Bekor qilingan: {stats.get('cancelled', 0)}\n\n"
                text += "Zayavkalar bo'yicha qidirish va filtrlash uchun quyidagi tugmalardan foydalaning:"
            else:
                text = "📊 <b>Статистика заявок</b>\n\n"
                text += f"Новые: {stats.get('new', 0)}\n"
                text += f"В процессе: {stats.get('in_progress', 0)}\n"
                text += f"Выполненные: {stats.get('completed', 0)}\n"
                text += f"Отменённые: {stats.get('cancelled', 0)}\n\n"
                text += "Для поиска и фильтрации заявок используйте следующие кнопки:"
            
            sent_message = await message.answer(
                text,
                reply_markup=get_zayavka_main_keyboard(lang)
            )
            
            # Save message ID for cleanup
            await state.update_data(last_message_id=sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Error in orders menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(['📂 Holat bo\'yicha', '📂 По статусу']))
    @admin_only
    async def handle_status_menu(message: Message, state: FSMContext):
        """Handle status menu"""
        try:
            lang = await get_user_lang(message.from_user.id)
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            text = "📂 <b>Holat bo'yicha qidirish</b>\n\n" if lang == 'uz' else "📂 <b>Поиск по статусу</b>\n\n"
            text += "Holatni tanlang:" if lang == 'uz' else "Выберите статус:"
            
            # Switch to section keyboard
            sent_message = await message.answer(
                text,
                reply_markup=get_zayavka_section_keyboard(lang)
            )
            await state.update_data(last_message_id=sent_message.message_id)
            
            # Show inline keyboard with pagination
            await message.answer(
                text,
                reply_markup=get_zayavka_status_filter_keyboard(lang, page=1, total_pages=1)
            )
            
        except Exception as e:
            logger.error(f"Error in status menu handler: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text == "🔍 Qidirish / Filtrlash")
    @admin_only
    async def handle_filter_menu(message: Message, state: FSMContext):
        """Handle filter menu selection"""
        try:
            lang = await get_user_lang(message.from_user.id)
            back_text = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            
            text = "🔍 <b>Qidirish / Filtrlash</b>\n\n" if lang == 'uz' else "🔍 <b>Поиск / Фильтр</b>\n\n"
            text += "Qidirish turini tanlang:" if lang == 'uz' else "Выберите тип поиска:"
            
            # Switch to section keyboard
            sent_message = await message.answer(
                text,
                reply_markup=get_zayavka_section_keyboard(lang)
            )
            await state.update_data(last_message_id=sent_message.message_id)
            
            # Show inline keyboard with pagination
            await message.answer(
                text,
                reply_markup=get_zayavka_filter_menu_keyboard(lang, page=1, total_pages=2, admin=True)
            )
            
        except Exception as e:
            logger.error(f"Error in filter menu handler: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("zayavka:status:"))
    @admin_only
    async def handle_status_selection(callback: CallbackQuery, state: FSMContext):
        """Handle status selection from inline keyboard"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            data = callback.data.split(':')[2:]
            action = data[0]
            
            if action in ["prev", "next"]:
                current_page = int(data[1])
                new_page = current_page - 1 if action == "prev" else current_page + 1
                
                # Get orders for the selected status
                state_data = await state.get_data()
                status = state_data.get('selected_status')
                orders = await get_filtered_orders(status=status)
                
                if not orders:
                    text = "Zayavkalar topilmadi." if lang == 'uz' else "Заявки не найдены."
                    await callback.message.edit_text(text)
                    return
                
                # Show first 10 orders
                text = "Zayavkalar:\n\n" if lang == 'uz' else "Заявки:\n\n"
                for order in orders[:10]:
                    text += format_order(order, lang)
                    text += "\n\n"
                
                await callback.message.edit_reply_markup(
                    reply_markup=get_zayavka_status_filter_keyboard(lang, page=new_page, total_pages=1)
                )
                await callback.answer()
                return

            # Get orders for the selected status
            status = data[1]
            orders = await get_filtered_orders(filters={'status': status})
            
            if not orders:
                text = "Zayavkalar topilmadi." if lang == 'uz' else "Заявки не найдены."
                await callback.message.edit_text(text)
                return
                
            # Show first 10 orders
            text = "Zayavkalar:\n\n" if lang == 'uz' else "Заявки:\n\n"
            for order in orders[:10]:
                text += format_order(order, lang)
                text += "\n\n"
                
            await state.update_data(selected_status=status)
            await callback.message.edit_reply_markup(
                reply_markup=get_zayavka_status_filter_keyboard(lang, page=1, total_pages=1)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in status selection handler: {e}")
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data.startswith("zayavka:filter:"))
    @admin_only
    async def handle_filter_selection(callback: CallbackQuery, state: FSMContext):
        """Handle filter selection from inline keyboard"""
        try:
            lang = await get_user_lang(callback.from_user.id)
            data = callback.data.split(':')[2:]
            action = data[0]
            
            if action in ["prev", "next"]:
                current_page = int(data[1])
                new_page = current_page - 1 if action == "prev" else current_page + 1
                
                # Get current filter type from state
                state_data = await state.get_data()
                active_filter = state_data.get('filter_type')
                
                await callback.message.edit_reply_markup(
                    reply_markup=get_zayavka_filter_menu_keyboard(lang, page=new_page, active_filter=active_filter, admin=True)
                )
                await callback.answer()
                return

            filter_map = {
                'username': "🔤 FIO / Username",
                'id': "🔢 Zayavka ID",
                'date': "📆 Sana oraliq",
                'category': "🏷 Kategoriya",
                'technician': "👨‍🔧 Texnik"
            }
        
            filter_type = filter_map.get(action)
            if not filter_type:
                raise ValueError("Invalid filter type")
                
            text = {
                'uz': {
                    'username': " 🔡 <b>FIO / Username bo'yicha qidirish</b>\n\n",
                    'id': " 🔢 <b>Zayavka ID bo'yicha qidirish</b>\n\n",
                    'date': " 📅 <b>Sana oraliq bo'yicha qidirish</b>\n\n",
                    'category': " 🏷 <b>Kategoriya bo'yicha qidirish</b>\n\n",
                    'technician': " 👨‍🔧 <b>Texnik bo'yicha qidirish</b>\n\n"
                },
                'ru': {
                    'username': " 🔡 <b>Поиск по ФИО / Username</b>\n\n",
                    'id': " 🔢 <b>Поиск по ID заявки</b>\n\n",
                    'date': " 📅 <b>Поиск по дате</b>\n\n",
                    'category': " 🏷 <b>Поиск по категории</b>\n\n",
                    'technician': " 👨‍🔧 <b>Поиск по технику</b>\n\n"
                }
            }
        
            text = text[lang][action]
            text += "Kerakli ma'lumotni kiriting:" if lang == 'uz' else "Введите нужную информацию:"
        
            # Set state based on filter type
            if action in ["date", "category"]:
                await state.set_state(AdminStates.filtering_selected)
            else:
                await state.set_state(AdminStates.filtering)
        
            await callback.message.edit_text(text)
            
            # Send new message with filter keyboard (replace with edit_text for inline UX)
            await callback.message.edit_text(
                "Qidirish turini tanlang:" if lang == 'uz' else "Выберите тип поиска:",
                reply_markup=get_zayavka_filter_menu_keyboard(lang, active_filter=action if action in ["date", "category"] else None, admin=True)
            )
            await state.update_data(filter_type=action)
            await callback.answer()
        
        except Exception as e:
            logger.error(f"Error in filter selection handler: {e}")
            lang = await get_user_lang(callback.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await callback.message.edit_text(error_text)

    @router.callback_query(F.data.startswith("bulk_assign_"))
    @admin_only
    async def bulk_assign_orders(call: CallbackQuery, state: FSMContext):
        """Bulk assign orders to technician"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            order_type = call.data.split("_")[2]
            
            # Get available technicians
            technicians = await get_available_technicians()
            
            if not technicians:
                text = "Mavjud texniklar yo'q." if lang == 'uz' else "Нет доступных техников."
                await call.message.edit_text(text)
                return
            
            text = "Texnikni tanlang:" if lang == 'uz' else "Выберите техника:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for tech in technicians[:10]:  # Show first 10
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"👨‍🔧 {tech['full_name']} ({tech.get('active_tasks', 0)} vazifa)",
                        callback_data=f"bulk_confirm_{order_type}_{tech['id']}"
                    )
                ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
        
        except Exception as e:
            logger.error(f"Error in bulk assign: {e}")
            lang = await get_user_lang(call.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await call.message.edit_text(error_text)
            return

    @router.callback_query(F.data.startswith("order_details_"))
    @admin_only
    async def show_order_details(call: CallbackQuery, state: FSMContext):
        """Show order details"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            order_id = int(call.data.split("_")[-1])
            
            # Get order details
            order = await get_zayavka_by_id(order_id)
            
            if not order:
                text = "Zayavka topilmadi." if lang == 'uz' else "Заявка не найдена."
                await call.message.edit_text(text)
                return

            text = (
                "Zayavka ma'lumotlari:\n\n"
                f"🆔 #{order['id']}\n"
                f"👤 {order.get('client_name', 'N/A')}\n"
                f"📱 {order.get('client_phone', 'N/A')}\n"
                f"📍 {order.get('address', 'N/A')}\n"
                f"📝 {order.get('title', 'N/A')}\n"
                f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
                "Holat: " if lang == 'uz' else "Статус: "
                f"{order.get('status', 'N/A')}\n\n"
                "Texnik: " if lang == 'uz' else "Техник: "
                f"{order.get('technician_name', 'N/A')}\n\n"
                "Qo'shimcha ma'lumotlar: " if lang == 'uz' else "Дополнительная информация: "
                f"{order.get('description', 'N/A')}")
        
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Batafsil" if lang == 'uz' else "📋 Подробно",
                        callback_data=f"order_details_{order['id']}"
                    )
                ]
            ])
        
            await call.message.edit_text(text, reply_markup=keyboard)
            return
        except Exception as e:
            logger.error(f"Error showing order details: {e}")
            lang = await get_user_lang(call.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await call.message.edit_text(error_text)

    @router.callback_query(F.data.startswith("change_status_"))
    @admin_only
    async def change_order_status(call: CallbackQuery):
        """Change order status"""
        try:
            lang = await get_user_lang(call.from_user.id)
            order_id = int(call.data.split("_")[-1])
            
            text = "Yangi statusni tanlang:" if lang == 'uz' else "Выберите новый статус:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⏳ Kutilmoqda" if lang == 'uz' else "⏳ Ожидает",
                        callback_data=f"set_status_{order_id}_pending"
                    ),
                    InlineKeyboardButton(
                        text="🔄 Jarayonda" if lang == 'uz' else "🔄 В процессе",
                        callback_data=f"set_status_{order_id}_in_progress"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✅ Bajarilgan" if lang == 'uz' else "✅ Выполнено",
                        callback_data=f"set_status_{order_id}_completed"
                    ),
                    InlineKeyboardButton(
                        text="❌ Bekor qilingan" if lang == 'uz' else "❌ Отменено",
                        callback_data=f"set_status_{order_id}_cancelled"
                    )
                ]
            ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error changing order status: {e}")
            lang = await get_user_lang(call.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await call.message.edit_text(error_text)

    @router.callback_query(F.data.startswith("set_status_"))
    @admin_only
    async def set_order_status(call: CallbackQuery):
        """Set order status"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            parts = call.data.split("_")
            order_id = int(parts[2])
            new_status = parts[3]
            
            # Update order status
            success = await update_zayavka_status(order_id, new_status, call.from_user.id)
            
            if success:
                # Log admin action
                await log_admin_action(call.from_user.id, "update_status", {
                    "order_id": order_id,
                    "new_status": new_status
                })
                
                status_names = {
                    'pending': ('Kutilmoqda', 'Ожидает'),
                    'in_progress': ('Jarayonda', 'В процессе'),
                    'completed': ('Bajarilgan', 'Выполнено'),
                    'cancelled': ('Bekor qilingan', 'Отменено')
                }
                
                status_name = status_names.get(new_status, (new_status, new_status))
                status_text = status_name[0] if lang == 'uz' else status_name[1]
                
                text = f"✅ Zayavka #{order_id} statusi '{status_text}' ga o'zgartirildi." if lang == 'uz' else f"✅ Статус заявки #{order_id} изменен на '{status_text}'."
                await call.answer("Status o'zgartirildi!" if lang == 'uz' else "Статус изменен!")
                
                await call.message.delete()
            else:
                text = "Statusni o'zgartirishda xatolik." if lang == 'uz' else "Ошибка при изменении статуса."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
                
                # Show error message and return to previous menu
                await call.message.edit_text(text)
        
        except Exception as e:
            logger.error(f"Error setting order status: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")
            
            # Show error message and return to previous menu
            lang = await get_user_lang(call.from_user.id)
            text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await call.message.edit_text(text)

    @router.callback_query(F.data.startswith("bulk_confirm_"))
    @admin_only
    async def confirm_bulk_assign(call: CallbackQuery, state: FSMContext):
        """
        Texnikni tanlashdan so'ng, barcha tanlangan buyurtmalarni shu texnikka biriktiradi.
        """
        try:
            lang = await get_user_lang(call.from_user.id)
            parts = call.data.split("_")
            order_type = parts[2]
            technician_id = int(parts[3])

            # order_id larni state dan olish (masalan, 'selected_order_ids' deb saqlangan bo'lishi mumkin)
            data = await state.get_data()
            order_ids = data.get("selected_order_ids", [])

            if not order_ids:
                await call.answer("Buyurtmalar topilmadi." if lang == 'uz' else "Заявки не найдены.", show_alert=True)
                return

            # Bulk biriktirish
            result = await bulk_assign_orders(order_ids, technician_id, call.from_user.id)

            if result:
                text = "Buyurtmalar texnikka biriktirildi." if lang == 'uz' else "Заявки назначены технику."
            else:
                text = "Biriktirishda xatolik." if lang == 'uz' else "Ошибка при назначении."

            await call.message.edit_text(text)
            await call.answer()
        except Exception as e:
            logger.error(f"Error in confirm_bulk_assign: {e}")
            await call.answer("Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка.", show_alert=True)

    @router.message(F.text.in_(["🔍 Zayavka qidirish", "🔍 Поиск заявки"]))
    @admin_only
    async def search_orders_menu(message: Message, state: FSMContext):
        """Search orders menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            text = "Zayavka ID sini kiriting:" if lang == 'uz' else "Введите ID заявки:"
            
            await message.answer(text)
            await state.set_state(AdminStates.waiting_for_order_id)
        
        except Exception as e:
            logger.error(f"Error in search orders menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(AdminStates.waiting_for_order_id)
    @admin_only
    async def process_order_search(message: Message, state: FSMContext):
        """Process order search"""
        try:
            lang = await get_user_lang(message.from_user.id)
            
            try:
                order_id = int(message.text.strip())
            except ValueError:
                text = "Noto'g'ri format. Raqam kiriting." if lang == 'uz' else "Неверный формат. Введите число."
                await message.answer(text)
                return
            
            # Get order details
            order = await get_zayavka_by_id(order_id)
            
            if not order:
                text = f"#{order_id} raqamli zayavka topilmadi." if lang == 'uz' else f"Заявка #{order_id} не найдена."
                await message.answer(text)
                await state.clear()
                return
            
            # Show order details (reuse the function from callback)
            if lang == 'uz':
                text = (
                    f"🔍 <b>Qidiruv natijasi</b>\n\n"
                    f"📋 <b>Zayavka #{order['id']}</b>\n\n"
                    f"👤 <b>Mijoz:</b> {order.get('user_name', 'N/A')}\n"
                    f"📱 <b>Telefon:</b> {order.get('client_phone', 'N/A')}\n"
                    f"📍 <b>Manzil:</b> {order.get('address', 'N/A')}\n"
                    f"📝 <b>Tavsif:</b> {order.get('description', 'N/A')}\n"
                    f"📊 <b>Status:</b> {order['status']}\n"
                    f"📅 <b>Yaratilgan:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
            else:
                text = (
                    f"🔍 <b>Результат поиска</b>\n\n"
                    f"📋 <b>Заявка #{order_id}</b>\n\n"
                    f"👤 <b>Клиент:</b> {order.get('user_name', 'N/A')}\n"
                    f"📱 <b>Телефон:</b> {order.get('client_phone', 'N/A')}\n"
                    f"📍 <b>Адрес:</b> {order.get('address', 'N/A')}\n"
                    f"📝 <b>Описание:</b> {order.get('description', 'N/A')}\n"
                    f"📊 <b>Статус:</b> {order['status']}\n"
                    f"📅 <b>Создана:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
            
            # Add management buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Batafsil" if lang == 'uz' else "📋 Подробно",
                        callback_data=f"order_details_{order_id}"
                    )
                ]
            ])
            
            # Add back button
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="◀️ Orqaga" if lang == 'uz' else "◀️ Назад",
                    callback_data="back_to_orders"
                )
            ])
            
            await message.answer(text, reply_markup=keyboard)
            await state.clear()
        
        except Exception as e:
            logger.error(f"Error in order search: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)
            await state.clear()

    return router