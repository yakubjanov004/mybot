from aiogram import F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.warehouse_queries import (
    get_warehouse_user_by_telegram_id, get_pending_warehouse_orders,
    get_in_progress_warehouse_orders, get_completed_warehouse_orders,
    update_order_status_warehouse, mark_order_ready_for_installation
)
from keyboards.warehouse_buttons import orders_menu, order_status_keyboard
from states.warehouse_states import WarehouseStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_warehouse_orders_router():
    router = get_role_router("warehouse")

    @router.message(F.text.in_(["📋 Buyurtmalar boshqaruvi", "📋 Управление заказами"]))
    async def orders_management_handler(message: Message, state: FSMContext):
        """Handle orders management"""
        try:
            user = await get_warehouse_user_by_telegram_id(message.from_user.id)
            if not user:
                return
            
            lang = user.get('language', 'uz')
            orders_text = "📋 Buyurtmalar boshqaruvi" if lang == 'uz' else "📋 Управление заказами"
            
            await message.answer(
                orders_text,
                reply_markup=orders_menu(lang)
            )
            await state.set_state(WarehouseStates.orders_menu)
            
        except Exception as e:
            logger.error(f"Error in orders management: {str(e)}")

    @router.callback_query(F.data == "pending_orders")
    async def pending_orders_handler(callback: CallbackQuery, state: FSMContext):
        """Show pending orders"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            orders = await get_pending_warehouse_orders()
            
            if orders:
                pending_text = "⏳ Kutilayotgan buyurtmalar:" if lang == 'uz' else "⏳ Ожидающие заказы:"
                text = f"{pending_text}\n\n"
                
                for order in orders:
                    text += f"🔹 **#{order['id']}** - {order.get('client_name', 'Noma\'lum')}\n"
                    text += f"   📝 {order['description'][:50]}{'...' if len(order['description']) > 50 else ''}\n"
                    text += f"   📅 {order['created_at'].strftime('%d.%m.%Y %H:%M') if order['created_at'] else 'N/A'}\n"
                    text += f"   📊 Status: {order['status']}\n"
                    if order.get('client_phone'):
                        text += f"   📞 {order['client_phone']}\n"
                    text += "\n"
                    
                    # Limit text length
                    if len(text) > 3500:
                        text += "... va boshqalar"
                        break
            else:
                text = "📭 Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет ожидающих заказов"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            await inline_message_manager.hide(callback.from_user.id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Error getting pending orders: {str(e)}")
            error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "in_progress_orders")
    async def in_progress_orders_handler(callback: CallbackQuery, state: FSMContext):
        """Show in progress orders"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            orders = await get_in_progress_warehouse_orders()
            
            if orders:
                progress_text = "🔄 Jarayondagi buyurtmalar:" if lang == 'uz' else "🔄 Заказы в процессе:"
                text = f"{progress_text}\n\n"
                
                for order in orders:
                    text += f"🔹 **#{order['id']}** - {order.get('client_name', 'Noma\'lum')}\n"
                    text += f"   📝 {order['description'][:50]}{'...' if len(order['description']) > 50 else ''}\n"
                    text += f"   👨‍🔧 Texnik: {order.get('technician_name', 'Tayinlanmagan')}\n"
                    text += f"   📅 {order['created_at'].strftime('%d.%m.%Y %H:%M') if order['created_at'] else 'N/A'}\n"
                    text += f"   📊 Status: {order['status']}\n"
                    if order.get('client_phone'):
                        text += f"   📞 {order['client_phone']}\n"
                    text += "\n"
                    
                    # Limit text length
                    if len(text) > 3500:
                        text += "... va boshqalar"
                        break
            else:
                text = "📭 Jarayondagi buyurtmalar yo'q" if lang == 'uz' else "📭 Нет заказов в процессе"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            await inline_message_manager.hide(callback.from_user.id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Error getting in progress orders: {str(e)}")
            error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "completed_orders")
    async def completed_orders_handler(callback: CallbackQuery, state: FSMContext):
        """Show completed orders"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            orders = await get_completed_warehouse_orders(10)  # Last 10 completed orders
            
            if orders:
                completed_text = "✅ Bajarilgan buyurtmalar:" if lang == 'uz' else "✅ Выполненные заказы:"
                text = f"{completed_text}\n\n"
                
                for order in orders:
                    text += f"🔹 **#{order['id']}** - {order.get('client_name', 'Noma\'lum')}\n"
                    text += f"   📝 {order['description'][:50]}{'...' if len(order['description']) > 50 else ''}\n"
                    text += f"   👨‍🔧 Texnik: {order.get('technician_name', 'Noma\'lum')}\n"
                    text += f"   📅 Yaratilgan: {order['created_at'].strftime('%d.%m.%Y') if order['created_at'] else 'N/A'}\n"
                    text += f"   ✅ Tugallangan: {order['completed_at'].strftime('%d.%m.%Y') if order['completed_at'] else 'N/A'}\n"
                    if order.get('client_phone'):
                        text += f"   📞 {order['client_phone']}\n"
                    text += "\n"
                    
                    # Limit text length
                    if len(text) > 3500:
                        text += "... va boshqalar"
                        break
            else:
                text = "📭 Bajarilgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет выполненных заказов"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            await inline_message_manager.hide(callback.from_user.id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Error getting completed orders: {str(e)}")
            error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data.startswith("mark_ready_"))
    async def mark_order_ready_handler(callback: CallbackQuery, state: FSMContext):
        """Mark order as ready for installation"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            order_id = int(callback.data.split("_")[-1])
            
            success = await mark_order_ready_for_installation(order_id, user['id'])
            
            if success:
                success_text = f"✅ #{order_id} buyurtma o'rnatishga tayyor deb belgilandi!" if lang == 'uz' else f"✅ Заказ #{order_id} отмечен как готов к установке!"
                await callback.message.edit_text(success_text)
                logger.info(f"Order {order_id} marked ready by warehouse user {user['id']}")
            else:
                error_text = "❌ Buyurtmani belgilashda xatolik" if lang == 'uz' else "❌ Ошибка при отметке заказа"
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error marking order ready: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data.startswith("update_order_status_"))
    async def update_order_status_handler(callback: CallbackQuery, state: FSMContext):
        """Update order status"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            # Parse callback data: update_order_status_{order_id}_{status}
            parts = callback.data.split("_")
            order_id = int(parts[3])
            new_status = parts[4]
            
            success = await update_order_status_warehouse(order_id, new_status, user['id'])
            
            if success:
                status_names = {
                    'confirmed': 'Tasdiqlangan' if lang == 'uz' else 'Подтвержден',
                    'in_progress': 'Jarayonda' if lang == 'uz' else 'В процессе',
                    'completed': 'Bajarilgan' if lang == 'uz' else 'Выполнен',
                    'cancelled': 'Bekor qilingan' if lang == 'uz' else 'Отменен'
                }
                
                status_name = status_names.get(new_status, new_status)
                success_text = f"✅ #{order_id} buyurtma holati '{status_name}' ga o'zgartirildi!" if lang == 'uz' else f"✅ Статус заказа #{order_id} изменен на '{status_name}'!"
                await callback.message.edit_text(success_text)
                logger.info(f"Order {order_id} status updated to {new_status} by warehouse user {user['id']}")
            else:
                error_text = "❌ Holatni o'zgartirishda xatolik" if lang == 'uz' else "❌ Ошибка при изменении статуса"
                await callback.message.edit_text(error_text)
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.callback_query(F.data == "orders_by_status")
    async def orders_by_status_handler(callback: CallbackQuery, state: FSMContext):
        """Show orders filtering by status"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            filter_text = "📊 Holatga ko'ra filtrlash:" if lang == 'uz' else "📊 Фильтр по статусу:"
            
            await callback.message.edit_text(
                filter_text,
                reply_markup=order_status_keyboard(lang)
            )
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error in orders by status: {str(e)}")

    @router.callback_query(F.data.startswith("filter_orders_"))
    async def filter_orders_handler(callback: CallbackQuery, state: FSMContext):
        """Filter orders by specific status"""
        try:
            user = await get_warehouse_user_by_telegram_id(callback.from_user.id)
            lang = user.get('language', 'uz')
            
            status = callback.data.split("_")[-1]
            orders = await get_warehouse_orders_by_status([status])
            
            status_names = {
                'new': 'Yangi' if lang == 'uz' else 'Новые',
                'confirmed': 'Tasdiqlangan' if lang == 'uz' else 'Подтвержденные',
                'in_progress': 'Jarayonda' if lang == 'uz' else 'В процессе',
                'completed': 'Bajarilgan' if lang == 'uz' else 'Выполненные',
                'cancelled': 'Bekor qilingan' if lang == 'uz' else 'Отмененные'
            }
            
            status_name = status_names.get(status, status)
            
            if orders:
                filter_text = f"📊 {status_name} buyurtmalar:" if lang == 'uz' else f"📊 {status_name} заказы:"
                text = f"{filter_text}\n\n"
                
                for order in orders:
                    text += f"🔹 **#{order['id']}** - {order.get('client_name', 'Noma\'lum')}\n"
                    text += f"   📝 {order['description'][:50]}{'...' if len(order['description']) > 50 else ''}\n"
                    text += f"   📅 {order['created_at'].strftime('%d.%m.%Y %H:%M') if order['created_at'] else 'N/A'}\n"
                    if order.get('technician_name'):
                        text += f"   👨‍🔧 {order['technician_name']}\n"
                    if order.get('client_phone'):
                        text += f"   📞 {order['client_phone']}\n"
                    text += "\n"
                    
                    # Limit text length
                    if len(text) > 3500:
                        text += "... va boshqalar"
                        break
            else:
                text = f"📭 {status_name} buyurtmalar yo'q" if lang == 'uz' else f"📭 Нет {status_name.lower()} заказов"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await callback.answer()
            await inline_message_manager.hide(callback.from_user.id, callback.message.message_id)
            
        except Exception as e:
            logger.error(f"Error filtering orders: {str(e)}")
            error_text = "Filtrlashda xatolik" if lang == 'uz' else "Ошибка при фильтрации"
            await callback.message.edit_text(error_text)
            await callback.answer()

    return router
