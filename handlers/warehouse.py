from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from database.queries import (
    get_user_by_telegram_id, get_inventory_items, add_inventory_item,
    update_inventory_item, get_low_stock_items, get_orders_by_status,
   get_warehouse_statistics, export_warehouse_data
)
from keyboards.warehouse_buttons import (
    warehouse_main_menu, inventory_menu, orders_menu, order_status_keyboard,
    inventory_actions_keyboard, warehouse_detailed_statistics_menu,
    inventory_detailed_list_menu, export_format_keyboard
)
from states.warehouse_states import WarehouseStates
from utils.logger import logger
from handlers.language import show_language_selection, process_language_change, get_user_lang

router = Router()

@router.message(F.text.in_(["📦 Warehouse", "📦 Склад", "📦 Ombor"]))
async def warehouse_start(message: Message, state: FSMContext):
    """Warehouse main menu"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        lang = user.get('language', 'uz') if user else 'uz'
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    
    await state.set_state(WarehouseStates.main_menu)
    lang = user.get('language', 'uz')
    welcome_text = "Ombor paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!"
    await message.answer(
        welcome_text,
        reply_markup=warehouse_main_menu(user['language'])
    )

@router.message(F.text.in_(["📦 Inventarizatsiya boshqaruvi", "📦 Управление инвентаризацией"]))
async def inventory_management_handler(message: Message, state: FSMContext):
    """Handle inventory management"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        return
    
    lang = user.get('language', 'uz')
    inventory_text = "Inventarizatsiya boshqaruvi" if lang == 'uz' else "Управление инвентаризацией"
    await message.answer(
        inventory_text,
        reply_markup=inventory_detailed_list_menu(lang)
    )

@router.callback_query(F.data == "view_inventory_list")
async def view_inventory_list(callback: CallbackQuery, state: FSMContext):
    """View inventory list"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        items = await get_inventory_items()
        
        if items:
            inventory_text = "Inventar ro'yxati:" if lang == 'uz' else "Список инвентаря:"
            text = f"📋 {inventory_text}\n\n"
            
            for item in items:
                status_icon = "✅" if item['quantity'] > item.get('min_quantity', 0) else "⚠️"
                text += f"{status_icon} {item['name']}\n"
                text += f"   📦 Miqdor: {item['quantity']} {item.get('unit', 'dona')}\n"
                text += f"   💰 Narx: {item.get('price', 0)} so'm\n"
                if item.get('min_quantity'):
                    text += f"   ⚠️ Min: {item['min_quantity']}\n"
                text += "\n"
        else:
            text = "Inventar ro'yxati bo'sh" if lang == 'uz' else "Список инвентаря пуст"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error viewing inventory list: {str(e)}")
        error_text = "Inventar ro'yxatini olishda xatolik" if lang == 'uz' else "Ошибка при получении списка инвентаря"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "add_inventory_item")
async def add_inventory_item_handler(callback: CallbackQuery, state: FSMContext):
    """Start adding inventory item"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(WarehouseStates.adding_item_name)
    text = "Mahsulot nomini kiriting:" if lang == 'uz' else "Введите название товара:"
    await callback.message.edit_text(text)
    await callback.answer()

@router.message(StateFilter(WarehouseStates.adding_item_name))
async def get_item_name(message: Message, state: FSMContext):
    """Get item name"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.update_data(item_name=message.text)
    await state.set_state(WarehouseStates.adding_item_quantity)
    text = "Miqdorni kiriting:" if lang == 'uz' else "Введите количество:"
    await message.answer(text)

@router.message(StateFilter(WarehouseStates.adding_item_quantity))
async def get_item_quantity(message: Message, state: FSMContext):
    """Get item quantity"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        quantity = int(message.text)
        await state.update_data(item_quantity=quantity)
        await state.set_state(WarehouseStates.adding_item_price)
        text = "Narxni kiriting (so'm):" if lang == 'uz' else "Введите цену (сум):"
        await message.answer(text)
    except ValueError:
        text = "Noto'g'ri miqdor. Raqam kiriting." if lang == 'uz' else "Неверное количество. Введите число."
        await message.answer(text)

@router.message(StateFilter(WarehouseStates.adding_item_price))
async def get_item_price(message: Message, state: FSMContext):
    """Get item price and save item"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        price = float(message.text)
        data = await state.get_data()
        
        item_data = {
            'name': data['item_name'],
            'quantity': data['item_quantity'],
            'price': price,
            'added_by': user['id']
        }
        
        item_id = await add_inventory_item(item_data)
        
        if item_id:
            success_text = "Mahsulot muvaffaqiyatli qo'shildi!" if lang == 'uz' else "Товар успешно добавлен!"
            await message.answer(success_text)
            logger.info(f"Inventory item added by warehouse user {user['id']}: {item_data}")
        else:
            error_text = "Mahsulot qo'shishda xatolik" if lang == 'uz' else "Ошибка при добавлении товара"
            await message.answer(error_text)
        
        await state.set_state(WarehouseStates.main_menu)
        
    except ValueError:
        text = "Noto'g'ri narx. Raqam kiriting." if lang == 'uz' else "Неверная цена. Введите число."
        await message.answer(text)

@router.callback_query(F.data == "update_inventory_item")
async def update_inventory_item_handler(callback: CallbackQuery, state: FSMContext):
    """Start updating inventory item"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        items = await get_inventory_items()
        
        if items:
            text = "Yangilanadigan mahsulotni tanlang:\n\n"
            for i, item in enumerate(items[:10], 1):  # Show first 10 items
                text += f"{i}. {item['name']} (Miqdor: {item['quantity']})\n"
            
            text += "\nMahsulot raqamini kiriting:"
            await callback.message.edit_text(text)
            await state.update_data(available_items=items)
            await state.set_state(WarehouseStates.selecting_item_to_update)
        else:
            text = "Yangilanadigan mahsulotlar yo'q" if lang == 'uz' else "Нет товаров для обновления"
            await callback.message.edit_text(text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in update inventory item: {str(e)}")
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.message(StateFilter(WarehouseStates.selecting_item_to_update))
async def select_item_to_update(message: Message, state: FSMContext):
    """Select item to update"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        item_number = int(message.text)
        data = await state.get_data()
        items = data.get('available_items', [])
        
        if 1 <= item_number <= len(items):
            selected_item = items[item_number - 1]
            await state.update_data(selected_item=selected_item)
            
            text = f"Tanlangan mahsulot: {selected_item['name']}\n"
            text += f"Joriy miqdor: {selected_item['quantity']}\n\n"
            text += "Yangi miqdorni kiriting:"
            
            await message.answer(text)
            await state.set_state(WarehouseStates.updating_item_quantity)
        else:
            text = "Noto'g'ri raqam. Qaytadan kiriting." if lang == 'uz' else "Неверный номер. Введите снова."
            await message.answer(text)
    except ValueError:
        text = "Noto'g'ri format. Raqam kiriting." if lang == 'uz' else "Неверный формат. Введите число."
        await message.answer(text)

@router.message(StateFilter(WarehouseStates.updating_item_quantity))
async def update_item_quantity(message: Message, state: FSMContext):
    """Update item quantity"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        new_quantity = int(message.text)
        data = await state.get_data()
        selected_item = data.get('selected_item')
        
        if selected_item:
            success = await update_inventory_item(selected_item['id'], {'quantity': new_quantity})
            
            if success:
                success_text = f"Mahsulot miqdori yangilandi!\n"
                success_text += f"Mahsulot: {selected_item['name']}\n"
                success_text += f"Yangi miqdor: {new_quantity}"
                await message.answer(success_text)
                logger.info(f"Inventory item {selected_item['id']} updated by warehouse user {user['id']}")
            else:
                error_text = "Yangilashda xatolik" if lang == 'uz' else "Ошибка при обновлении"
                await message.answer(error_text)
        
        await state.set_state(WarehouseStates.main_menu)
        
    except ValueError:
        text = "Noto'g'ri miqdor. Raqam kiriting." if lang == 'uz' else "Неверное количество. Введите число."
        await message.answer(text)

@router.callback_query(F.data == "low_stock_report")
async def low_stock_report_handler(callback: CallbackQuery, state: FSMContext):
    """Show low stock report"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        low_stock_items = await get_low_stock_items()
        
        if low_stock_items:
            report_text = "Kam zaxira hisoboti:" if lang == 'uz' else "Отчет о низком запасе:"
            text = f"⚠️ {report_text}\n\n"
            
            for item in low_stock_items:
                text += f"🔴 {item['name']}\n"
                text += f"   📦 Joriy: {item['quantity']} {item.get('unit', 'dona')}\n"
                text += f"   ⚠️ Minimal: {item.get('min_quantity', 0)}\n"
                text += f"   📉 Kamomad: {item.get('min_quantity', 0) - item['quantity']}\n\n"
        else:
            text = "Kam zaxira mahsulotlari yo'q" if lang == 'uz' else "Нет товаров с низким запасом"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in low stock report: {str(e)}")
        error_text = "Hisobotni olishda xatolik" if lang == 'uz' else "Ошибка при получении отчета"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.message(F.text.in_(["📋 Buyurtmalar boshqaruvi", "📋 Управление заказами"]))
async def orders_management_handler(message: Message, state: FSMContext):
    """Handle orders management"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        return
    
    lang = user.get('language', 'uz')
    orders_text = "Buyurtmalar boshqaruvi" if lang == 'uz' else "Управление заказами"
    await message.answer(
        orders_text,
        reply_markup=orders_menu(lang)
    )

@router.callback_query(F.data == "pending_orders")
async def pending_orders_handler(callback: CallbackQuery, state: FSMContext):
    """Show pending orders"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        orders = await get_orders_by_status(['new', 'confirmed'])
        
        if orders:
            pending_text = "Kutilayotgan buyurtmalar:" if lang == 'uz' else "Ожидающие заказы:"
            text = f"⏳ {pending_text}\n\n"
            
            for order in orders:
                text += f"🔹 #{order['id']} - {order['client_name']}\n"
                text += f"   📝 {order['description']}\n"
                text += f"   📅 {order['created_at']}\n"
                text += f"   📊 {order['status']}\n\n"
        else:
            text = "Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "Нет ожидающих заказов"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting pending orders: {str(e)}")
        error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "in_progress_orders")
async def in_progress_orders_handler(callback: CallbackQuery, state: FSMContext):
    """Show in progress orders"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        orders = await get_orders_by_status(['in_progress'])
        
        if orders:
            progress_text = "Jarayondagi buyurtmalar:" if lang == 'uz' else "Заказы в процессе:"
            text = f"🔄 {progress_text}\n\n"
            
            for order in orders:
                text += f"🔹 #{order['id']} - {order['client_name']}\n"
                text += f"   📝 {order['description']}\n"
                text += f"   👨‍🔧 Texnik: {order.get('technician_name', 'Tayinlanmagan')}\n"
                text += f"   📅 {order['created_at']}\n\n"
        else:
            text = "Jarayondagi buyurtmalar yo'q" if lang == 'uz' else "Нет заказов в процессе"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting in progress orders: {str(e)}")
        error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "completed_orders")
async def completed_orders_handler(callback: CallbackQuery, state: FSMContext):
    """Show completed orders"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        orders = await get_orders_by_status(['completed'])
        
        if orders:
            completed_text = "Bajarilgan buyurtmalar:" if lang == 'uz' else "Выполненные заказы:"
            text = f"✅ {completed_text}\n\n"
            
            for order in orders[-10:]:  # Show last 10 completed orders
                text += f"🔹 #{order['id']} - {order['client_name']}\n"
                text += f"   📝 {order['description']}\n"
                text += f"   👨‍🔧 Texnik: {order.get('technician_name', 'Noma\'lum')}\n"
                text += f"   ✅ Yakunlangan: {order.get('completed_at', 'N/A')}\n\n"
        else:
            text = "Bajarilgan buyurtmalar yo'q" if lang == 'uz' else "Нет выполненных заказов"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting completed orders: {str(e)}")
        error_text = "Buyurtmalarni olishda xatolik" if lang == 'uz' else "Ошибка при получении заказов"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.message(F.text.in_(["📊 Sklad statistikasi", "📊 Статистика склада"]))
async def warehouse_statistics_handler(message: Message, state: FSMContext):
    """Handle warehouse statistics"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        return
    
    lang = user.get('language', 'uz')
    stats_text = "Sklad statistikasi" if lang == 'uz' else "Статистика склада"
    await message.answer(
        stats_text,
        reply_markup=warehouse_detailed_statistics_menu(lang)
    )

@router.callback_query(F.data.startswith("warehouse_stats_"))
async def warehouse_statistics_detailed_handler(callback: CallbackQuery, state: FSMContext):
    """Handle detailed warehouse statistics"""
    stats_type = callback.data.split("_")[2]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        if stats_type == "daily":
            stats = await get_warehouse_statistics(period='daily')
            title = "Kunlik hisobot" if lang == 'uz' else "Ежедневный отчет"
        elif stats_type == "weekly":
            stats = await get_warehouse_statistics(period='weekly')
            title = "Haftalik hisobot" if lang == 'uz' else "Недельный отчет"
        elif stats_type == "monthly":
            stats = await get_warehouse_statistics(period='monthly')
            title = "Oylik hisobot" if lang == 'uz' else "Месячный отчет"
        elif stats_type == "turnover":
            stats = await get_warehouse_statistics(period='turnover')
            title = "Inventar aylanishi" if lang == 'uz' else "Оборот инвентаря"
        
        # Format statistics text
        items_added_text = "Qo'shilgan mahsulotlar" if lang == 'uz' else "Добавленные товары"
        items_issued_text = "Berilgan mahsulotlar" if lang == 'uz' else "Выданные товары"
        total_value_text = "Umumiy qiymat" if lang == 'uz' else "Общая стоимость"
        low_stock_text = "Kam zaxira" if lang == 'uz' else "Низкий запас"
        
        text = f"📊 {title}\n\n"
        text += f"📦 {items_added_text}: {stats.get('items_added', 0)}\n"
        text += f"📤 {items_issued_text}: {stats.get('items_issued', 0)}\n"
        text += f"💰 {total_value_text}: {stats.get('total_value', 0)} so'm\n"
        text += f"⚠️ {low_stock_text}: {stats.get('low_stock_count', 0)}\n"
        
        if stats_type == "turnover":
            turnover_rate_text = "Aylanish tezligi" if lang == 'uz' else "Скорость оборота"
            text += f"🔄 {turnover_rate_text}: {stats.get('turnover_rate', 0)}%\n"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in warehouse statistics: {str(e)}")
        error_text = "Statistikani olishda xatolik" if lang == 'uz' else "Ошибка при получении статистики"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "warehouse_export_data")
async def warehouse_export_data_handler(callback: CallbackQuery, state: FSMContext):
    """Handle data export request"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    export_text = "Eksport formatini tanlang:" if lang == 'uz' else "Выберите формат экспорта:"
    await callback.message.edit_text(
        export_text,
        reply_markup=export_format_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("export_"))
async def export_data_handler(callback: CallbackQuery, state: FSMContext):
    """Handle data export in selected format"""
    export_format = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        # Export data in selected format
        file_path = await export_warehouse_data(export_format)
        
        if file_path:
            exporting_text = "Ma'lumotlar eksport qilinmoqda..." if lang == 'uz' else "Экспорт данных..."
            await callback.message.edit_text(exporting_text)
            
            # Send file to user
            with open(file_path, 'rb') as file:
                await callback.message.answer_document(
                    document=file,
                    caption=f"Ombor ma'lumotlari ({export_format.upper()})" if lang == 'uz' else f"Данные склада ({export_format.upper()})"
                )
            
            success_text = "Ma'lumotlar muvaffaqiyatli eksport qilindi!" if lang == 'uz' else "Данные успешно экспортированы!"
            await callback.message.edit_text(success_text)
            
            logger.info(f"Warehouse data exported by user {user['id']} in {export_format} format")
        else:
            error_text = "Eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте"
            await callback.message.edit_text(error_text)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error exporting warehouse data: {str(e)}")
        error_text = "Eksport qilishda xatolik" if lang == 'uz' else "Ошибка при экспорте"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "warehouse_back")
async def warehouse_back_handler(callback: CallbackQuery, state: FSMContext):
    """Go back to warehouse main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(WarehouseStates.main_menu)
    welcome_text = "Ombor paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!"
    await callback.message.edit_text(
        welcome_text,
        reply_markup=warehouse_main_menu(user['language'])
    )
    await callback.answer()

@router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Изменить язык"]))
async def warehouse_change_language(message: Message, state: FSMContext):
    """Change language for warehouse"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        return
    
    success = await show_language_selection(message, "warehouse", state)
    if not success:
        lang = user.get('language', 'uz')
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(error_text)

@router.callback_query(F.data.startswith("warehouse_lang_"))
async def process_warehouse_language_change(callback: CallbackQuery, state: FSMContext):
    """Process warehouse language change"""
    try:
        await process_language_change(
            call=callback,
            role="warehouse",
            get_main_keyboard_func=warehouse_main_menu,
            state=state
        )
        await state.set_state(WarehouseStates.main_menu)
    except Exception as e:
        logger.error(f"Warehouse tilni o'zgartirishda xatolik: {str(e)}")
        lang = await get_user_lang(callback.from_user.id)
        error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await callback.message.answer(error_text)
        await callback.answer()

@router.callback_query(F.data == "inventory_list_all")
async def inventory_list_all_handler(callback: CallbackQuery, state: FSMContext):
    """Show all inventory items"""
    await view_inventory_list(callback, state)

@router.callback_query(F.data == "inventory_list_low_stock")
async def inventory_list_low_stock_handler(callback: CallbackQuery, state: FSMContext):
    """Show low stock items"""
    await low_stock_report_handler(callback, state)

@router.callback_query(F.data == "inventory_list_out_of_stock")
async def inventory_list_out_of_stock_handler(callback: CallbackQuery, state: FSMContext):
    """Show out of stock items"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        items = await get_inventory_items()
        out_of_stock_items = [item for item in items if item['quantity'] == 0]
        
        if out_of_stock_items:
            out_of_stock_text = "Tugagan mahsulotlar:" if lang == 'uz' else "Закончившиеся товары:"
            text = f"❌ {out_of_stock_text}\n\n"
            
            for item in out_of_stock_items:
                text += f"🔴 {item['name']}\n"
                text += f"   📦 Miqdor: 0 {item.get('unit', 'dona')}\n"
                text += f"   💰 Narx: {item.get('price', 0)} so'm\n\n"
        else:
            text = "Tugagan mahsulotlar yo'q" if lang == 'uz' else "Нет закончившихся товаров"
        
        await callback.message.edit_text(text)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting out of stock items: {str(e)}")
        error_text = "Ma'lumotlarni olishda xatolik" if lang == 'uz' else "Ошибка при получении данных"
        await callback.message.edit_text(error_text)
        await callback.answer()

@router.callback_query(F.data == "inventory_search")
async def inventory_search_handler(callback: CallbackQuery, state: FSMContext):
    """Start inventory search"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(WarehouseStates.searching_inventory)
    search_text = "Qidiruv so'zini kiriting:" if lang == 'uz' else "Введите поисковый запрос:"
    await callback.message.edit_text(search_text)
    await callback.answer()

@router.message(StateFilter(WarehouseStates.searching_inventory))
async def process_inventory_search(message: Message, state: FSMContext):
    """Process inventory search"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    search_query = message.text.strip().lower()
    
    try:
        items = await get_inventory_items()
        found_items = [
            item for item in items 
            if search_query in item['name'].lower() or 
               search_query in item.get('description', '').lower()
        ]
        
        if found_items:
            search_results_text = "Qidiruv natijalari:" if lang == 'uz' else "Результаты поиска:"
            text = f"🔍 {search_results_text}\n\n"
            
            for item in found_items:
                status_icon = "✅" if item['quantity'] > 0 else "❌"
                text += f"{status_icon} {item['name']}\n"
                text += f"   📦 Miqdor: {item['quantity']} {item.get('unit', 'dona')}\n"
                text += f"   💰 Narx: {item.get('price', 0)} so'm\n\n"
        else:
            text = "Hech narsa topilmadi" if lang == 'uz' else "Ничего не найдено"
        
        await message.answer(text)
        await state.set_state(WarehouseStates.main_menu)
        
    except Exception as e:
        logger.error(f"Error in inventory search: {str(e)}")
        error_text = "Qidirishda xatolik" if lang == 'uz' else "Ошибка при поиске"
        await message.answer(error_text)
        await state.set_state(WarehouseStates.main_menu)
