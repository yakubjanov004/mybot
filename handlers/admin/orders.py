from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from functools import wraps
import logging
from datetime import datetime, timedelta

from database.admin_queries import (
    is_admin, get_orders_management_stats, get_filtered_orders,
    bulk_assign_orders, log_admin_action
)
from database.base_queries import (
    get_zayavka_by_id, update_zayavka_status,
    assign_zayavka_to_technician,
    get_user_by_telegram_id, get_user_lang
)
from database.technician_queries import get_available_technicians
from keyboards.admin_buttons import get_orders_management_keyboard
from states.admin_states import AdminStates
from utils.inline_cleanup import (
    answer_and_cleanup, safe_delete_message, cleanup_user_inline_messages
)
from utils.logger import setup_logger
from utils.role_checks import admin_only
from loader import inline_message_manager
from aiogram.filters import StateFilter

# Setup logger
logger = setup_logger('bot.admin.orders')

def get_admin_orders_router():
    router = Router()
    
    @router.message(StateFilter(AdminStates.main_menu), F.text.in_(["📝 Zayavkalar", "📝 Заявки"]))
    @admin_only
    async def orders_menu(message: Message, state: FSMContext):
        """Orders management main menu"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get orders management stats
            stats = await get_orders_management_stats()
            
            if lang == 'uz':
                text = (
                    f"📝 <b>Zayavkalar boshqaruvi</b>\n\n"
                    f"📊 <b>Statistika:</b>\n"
                )
                for status_stat in stats.get('by_status', []):
                    status_name = {
                        'new': '🆕 Yangi',
                        'pending': '⏳ Kutilmoqda',
                        'assigned': '👨‍🔧 Tayinlangan',
                        'in_progress': '🔄 Jarayonda',
                        'completed': '✅ Bajarilgan',
                        'cancelled': '❌ Bekor qilingan'
                    }.get(status_stat['status'], status_stat['status'])
                    text += f"• {status_name}: <b>{status_stat['count']}</b>\n"
                
                text += (
                    f"\n🚨 <b>Diqqat talab qiladi:</b>\n"
                    f"• Tayinlanmagan: <b>{stats.get('unassigned', 0)}</b>\n"
                    f"• Kechikkan: <b>{stats.get('overdue', 0)}</b>\n\n"
                    f"Kerakli amalni tanlang:"
                )
            else:
                text = (
                    f"📝 <b>Управление заявками</b>\n\n"
                    f"📊 <b>Статистика:</b>\n"
                )
                for status_stat in stats.get('by_status', []):
                    status_name = {
                        'new': '🆕 Новые',
                        'pending': '⏳ Ожидающие',
                        'assigned': '👨‍🔧 Назначенные',
                        'in_progress': '🔄 В процессе',
                        'completed': '✅ Выполненные',
                        'cancelled': '❌ Отмененные'
                    }.get(status_stat['status'], status_stat['status'])
                    text += f"• {status_name}: <b>{status_stat['count']}</b>\n"
                
                text += (
                    f"\n🚨 <b>Требуют внимания:</b>\n"
                    f"• Неназначенные: <b>{stats.get('unassigned', 0)}</b>\n"
                    f"• Просроченные: <b>{stats.get('overdue', 0)}</b>\n\n"
                    f"Выберите действие:"
                )
            
            sent_message = await message.answer(
                text,
                reply_markup=get_orders_management_keyboard(lang)
            )
            await inline_message_manager.track(message.from_user.id, sent_message.message_id)
            await state.set_state(AdminStates.orders)
            
        except Exception as e:
            logger.error(f"Error in orders management menu: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🆕 Yangi zayavkalar", "🆕 Новые заявки"]))
    @admin_only
    async def show_new_orders(message: Message):
        """Show new orders"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get new orders
            orders = await get_filtered_orders({'status': 'new'})
            
            if not orders:
                text = "Yangi zayavkalar yo'q." if lang == 'uz' else "Новых заявок нет."
                await message.answer(text)
                return
            
            if lang == 'uz':
                text = f"🆕 <b>Yangi zayavkalar</b> ({len(orders)} ta)\n\n"
            else:
                text = f"🆕 <b>Новые заявки</b> ({len(orders)} шт.)\n\n"
            
            for order in orders[:10]:  # Show first 10
                text += (
                    f"🆔 <b>#{order['id']}</b>\n"
                    f"👤 {order.get('client_name', 'N/A')}\n"
                    f"📱 {order.get('client_phone', 'N/A')}\n"
                    f"📍 {order.get('address', 'N/A')}\n"
                    f"📝 {order.get('description', 'N/A')[:50]}...\n"
                    f"📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
                
                # Add management buttons
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👨‍🔧 Tayinlash" if lang == 'uz' else "👨‍🔧 Назначить",
                            callback_data=f"assign_order_{order['id']}"
                        ),
                        InlineKeyboardButton(
                            text="📋 Batafsil" if lang == 'uz' else "📋 Подробно",
                            callback_data=f"order_details_{order['id']}"
                        )
                    ]
                ])
                
                await message.answer(text, reply_markup=keyboard)
                text = ""  # Reset for next order
            
            if len(orders) > 10:
                remaining_text = f"\n... va yana {len(orders) - 10} ta zayavka" if lang == 'uz' else f"\n... и еще {len(orders) - 10} заявок"
                await message.answer(remaining_text)
            
        except Exception as e:
            logger.error(f"Error showing new orders: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["⏳ Kutilayotgan zayavkalar", "⏳ Ожидающие заявки"]))
    @admin_only
    async def show_pending_orders(message: Message):
        """Show pending orders"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get pending orders
            orders = await get_filtered_orders({'status': 'pending'})
            
            if not orders:
                text = "Kutilayotgan zayavkalar yo'q." if lang == 'uz' else "Ожидающих заявок нет."
                await message.answer(text)
                return
            
            await show_orders_list(message, orders, "pending", lang)
            
        except Exception as e:
            logger.error(f"Error showing pending orders: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🔄 Jarayondagi zayavkalar", "🔄 Заявки в процессе"]))
    @admin_only
    async def show_in_progress_orders(message: Message):
        """Show in progress orders"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get in progress orders
            orders = await get_filtered_orders({'status': 'in_progress'})
            
            if not orders:
                text = "Jarayondagi zayavkalar yo'q." if lang == 'uz' else "Заявок в процессе нет."
                await message.answer(text)
                return
            
            await show_orders_list(message, orders, "in_progress", lang)
            
        except Exception as e:
            logger.error(f"Error showing in progress orders: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    @router.message(F.text.in_(["🚨 Tayinlanmagan zayavkalar", "🚨 Неназначенные заявки"]))
    @admin_only
    async def show_unassigned_orders(message: Message):
        """Show unassigned orders"""
        try:
            await safe_delete_message(message.bot, message.chat.id, message.message_id)
            lang = await get_user_lang(message.from_user.id)
            
            # Get unassigned orders
            orders = await get_filtered_orders({'technician_id': 0})
            
            if not orders:
                text = "Tayinlanmagan zayavkalar yo'q." if lang == 'uz' else "Неназначенных заявок нет."
                await message.answer(text)
                return
            
            await show_orders_list(message, orders, "unassigned", lang)
            
        except Exception as e:
            logger.error(f"Error showing unassigned orders: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)

    async def show_orders_list(message, orders, order_type, lang):
        """Helper function to show orders list"""
        try:
            type_names = {
                'pending': ('Kutilayotgan zayavkalar', 'Ожидающие заявки'),
                'in_progress': ('Jarayondagi zayavkalar', 'Заявки в процессе'),
                'unassigned': ('Tayinlanmagan zayavkalar', 'Неназначенные заявки')
            }
            
            title = type_names.get(order_type, ('Zayavkalar', 'Заявки'))
            header = title[0] if lang == 'uz' else title[1]
            
            text = f"📋 <b>{header}</b> ({len(orders)} ta)\n\n" if lang == 'uz' else f"📋 <b>{header}</b> ({len(orders)} шт.)\n\n"
            
            for i, order in enumerate(orders[:5], 1):  # Show first 5
                text += (
                    f"{i}. 🆔 <b>#{order['id']}</b>\n"
                    f"   👤 {order.get('client_name', 'N/A')}\n"
                    f"   📱 {order.get('client_phone', 'N/A')}\n"
                    f"   📍 {order.get('address', 'N/A')}\n"
                    f"   📅 {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
                
                if order.get('technician_name'):
                    text += f"   👨‍🔧 {order['technician_name']}\n"
                
                text += "\n"
            
            if len(orders) > 5:
                text += f"... va yana {len(orders) - 5} ta" if lang == 'uz' else f"... и еще {len(orders) - 5} шт."
            
            # Add bulk actions keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👨‍🔧 Ommaviy tayinlash" if lang == 'uz' else "👨‍🔧 Массовое назначение",
                        callback_data=f"bulk_assign_{order_type}"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing orders list: {e}")

    @router.callback_query(F.data.startswith("assign_order_"))
    @admin_only
    async def assign_order(call: CallbackQuery):
        """Assign order to technician"""
        try:
            await answer_and_cleanup(call, cleanup_after=True)
            lang = await get_user_lang(call.from_user.id)
            
            order_id = int(call.data.split("_")[-1])
            
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
                        callback_data=f"confirm_assign_{order_id}_{tech['id']}"
                    )
                ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error assigning order: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("confirm_assign_"))
    @admin_only
    async def confirm_assign_order(call: CallbackQuery):
        """Confirm order assignment"""
        try:
            lang = await get_user_lang(call.from_user.id)
            
            parts = call.data.split("_")
            order_id = int(parts[2])
            technician_id = int(parts[3])
            
            # Assign order
            success = await assign_zayavka_to_technician(order_id, technician_id, call.from_user.id)
            
            if success:
                # Log admin action
                await log_admin_action(call.from_user.id, "assign_order", {
                    "order_id": order_id,
                    "technician_id": technician_id
                })
                
                text = f"✅ Zayavka #{order_id} texnikga tayinlandi." if lang == 'uz' else f"✅ Заявка #{order_id} назначена технику."
                await call.answer("Tayinlandi!" if lang == 'uz' else "Назначено!")
            else:
                text = "Zayavkani tayinlashda xatolik." if lang == 'uz' else "Ошибка при назначении заявки."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
            await call.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error confirming order assignment: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("order_details_"))
    @admin_only
    async def show_order_details(call: CallbackQuery):
        """Show detailed order information"""
        try:
            await answer_and_cleanup(call, cleanup_after=True)
            lang = await get_user_lang(call.from_user.id)
            
            order_id = int(call.data.split("_")[-1])
            
            # Get order details
            order = await get_zayavka_by_id(order_id)
            
            if not order:
                text = "Zayavka topilmadi." if lang == 'uz' else "Заявка не найдена."
                await call.message.edit_text(text)
                return
            
            if lang == 'uz':
                text = (
                    f"📋 <b>Zayavka #{order['id']}</b>\n\n"
                    f"👤 <b>Mijoz:</b> {order.get('user_name', 'N/A')}\n"
                    f"📱 <b>Telefon:</b> {order.get('client_phone', 'N/A')}\n"
                    f"📍 <b>Manzil:</b> {order.get('address', 'N/A')}\n"
                    f"📝 <b>Tavsif:</b> {order.get('description', 'N/A')}\n"
                    f"📊 <b>Status:</b> {order['status']}\n"
                    f"📅 <b>Yaratilgan:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
                
                if order.get('technician_name'):
                    text += f"👨‍🔧 <b>Texnik:</b> {order['technician_name']}\n"
                    text += f"📱 <b>Texnik tel:</b> {order.get('technician_phone', 'N/A')}\n"
                
                if order.get('assigned_at'):
                    text += f"📅 <b>Tayinlangan:</b> {order['assigned_at'].strftime('%d.%m.%Y %H:%M')}\n"
                
                if order.get('completed_at'):
                    text += f"✅ <b>Bajarilgan:</b> {order['completed_at'].strftime('%d.%m.%Y %H:%M')}\n"
            else:
                text = (
                    f"📋 <b>Заявка #{order['id']}</b>\n\n"
                    f"👤 <b>Клиент:</b> {order.get('user_name', 'N/A')}\n"
                    f"📱 <b>Телефон:</b> {order.get('client_phone', 'N/A')}\n"
                    f"📍 <b>Адрес:</b> {order.get('address', 'N/A')}\n"
                    f"📝 <b>Описание:</b> {order.get('description', 'N/A')}\n"
                    f"📊 <b>Статус:</b> {order['status']}\n"
                    f"📅 <b>Создана:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
                
                if order.get('technician_name'):
                    text += f"👨‍🔧 <b>Техник:</b> {order['technician_name']}\n"
                    text += f"📱 <b>Тел. техника:</b> {order.get('technician_phone', 'N/A')}\n"
                
                if order.get('assigned_at'):
                    text += f"📅 <b>Назначена:</b> {order['assigned_at'].strftime('%d.%m.%Y %H:%M')}\n"
                
                if order.get('completed_at'):
                    text += f"✅ <b>Выполнена:</b> {order['completed_at'].strftime('%d.%m.%Y %H:%M')}\n"
            
            # Add action buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            
            if order['status'] in ['new', 'pending']:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text="👨‍🔧 Tayinlash" if lang == 'uz' else "👨‍🔧 Назначить",
                        callback_data=f"assign_order_{order['id']}"
                    )
                ])
            
            if order['status'] != 'completed':
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text="📊 Status o'zgartirish" if lang == 'uz' else "📊 Изменить статус",
                        callback_data=f"change_status_{order['id']}"
                    )
                ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error showing order details: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

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
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

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
                await log_admin_action(call.from_user.id, "change_order_status", {
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
            else:
                text = "Statusni o'zgartirishda xatolik." if lang == 'uz' else "Ошибка при изменении статуса."
                await call.answer("Xatolik!" if lang == 'uz' else "Ошибка!")
            
            await call.message.edit_text(text)
            
        except Exception as e:
            logger.error(f"Error setting order status: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

    @router.callback_query(F.data.startswith("bulk_assign_"))
    @admin_only
    async def bulk_assign_orders(call: CallbackQuery):
        """Bulk assign orders"""
        try:
            lang = await get_user_lang(call.from_user.id)
            order_type = call.data.split("_")[-1]
            
            # Get available technicians
            technicians = await get_available_technicians()
            
            if not technicians:
                text = "Mavjud texniklar yo'q." if lang == 'uz' else "Нет доступных техников."
                await call.message.edit_text(text)
                return
            
            text = "Ommaviy tayinlash uchun texnikni tanlang:" if lang == 'uz' else "Выберите техника для массового назначения:"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            for tech in technicians[:10]:
                keyboard.inline_keyboard.append([
                    InlineKeyboardButton(
                        text=f"👨‍🔧 {tech['full_name']} ({tech.get('active_tasks', 0)} vazifa)",
                        callback_data=f"bulk_confirm_{order_type}_{tech['id']}"
                    )
                ])
            
            await call.message.edit_text(text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in bulk assign orders: {e}")
            await call.answer("Xatolik yuz berdi!" if await get_user_lang(call.from_user.id) == 'uz' else "Произошла ошибка!")

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
                    f"📋 <b>Заявка #{order['id']}</b>\n\n"
                    f"👤 <b>Клиент:</b> {order.get('user_name', 'N/A')}\n"
                    f"📱 <b>Телефон:</b> {order.get('client_phone', 'N/A')}\n"
                    f"📍 <b>Адрес:</b> {order.get('address', 'N/A')}\n"
                    f"📝 <b>Описание:</b> {order.get('description', 'N/A')}\n"
                    f"📊 <b>Статус:</b> {order['status']}\n"
                    f"📅 <b>Создана:</b> {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
                )
            
            if order.get('technician_name'):
                tech_text = f"👨‍🔧 <b>Texnik:</b> {order['technician_name']}\n" if lang == 'uz' else f"👨‍🔧 <b>Техник:</b> {order['technician_name']}\n"
                text += tech_text
            
            # Add management buttons
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📋 Batafsil" if lang == 'uz' else "📋 Подробно",
                        callback_data=f"order_details_{order['id']}"
                    )
                ]
            ])
            
            await message.answer(text, reply_markup=keyboard)
            await state.clear()
            
        except Exception as e:
            logger.error(f"Error processing order search: {e}")
            lang = await get_user_lang(message.from_user.id)
            error_text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
            await message.answer(error_text)
            await state.clear()

    return router
