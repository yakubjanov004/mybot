from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.queries import (
    get_user_by_telegram_id, get_orders_by_status, update_zayavka_status,
    get_materials, 
    get_order_details
)
from keyboards.warehouse_buttons import (
    warehouse_main_menu, inventory_menu, orders_menu,
    order_status_keyboard
)
from states.warehouse_states import WarehouseStates
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📦 Warehouse", "📦 Склад", "📦 Ombor"]))
async def warehouse_start(message: Message, state: FSMContext):
    await state.clear()
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        lang = user.get('language', 'uz') if user else 'uz'
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    await state.set_state(WarehouseStates.main_menu)
    lang = user.get('language', 'uz')
    welcome_text = "Warehouse paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!"
    await message.answer(
        welcome_text,
        reply_markup=warehouse_main_menu(user['language'])
    )

@router.callback_query(F.data == "warehouse_inventory")
async def warehouse_inventory(callback: CallbackQuery, state: FSMContext):
    """Show inventory management"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    inventory_items = await get_materials()
    
    list_text = "Inventar ro'yxati:" if lang == 'uz' else "Список инвентаря:"
    text = list_text + "\n\n"
    for item in inventory_items:
        status = "✅" if item['stock'] > 0 else "⚠️"
        text += f"{status} {item['name']}: {item['stock']} {item.get('unit', '')}\n"
    
    await state.set_state(WarehouseStates.inventory_menu)
    await callback.message.edit_text(
        text,
        reply_markup=inventory_menu(user['language'])
    )

@router.callback_query(F.data == "warehouse_orders")
async def warehouse_orders(callback: CallbackQuery, state: FSMContext):
    """Show orders for warehouse processing"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    orders = await get_orders_by_status(['confirmed', 'in_progress'])
    
    orders_text = "Warehouse buyurtmalari:" if lang == 'uz' else "Заказы склада:"
    text = orders_text + "\n\n"
    for order in orders:
        text += f"🔹 #{order['id']} - {order['client_name']}\n"
        text += f"   {order['service_type']} - {order['status']}\n\n"
    
    await state.set_state(WarehouseStates.orders_menu)
    await callback.message.edit_text(
        text,
        reply_markup=orders_menu(user['language'])
    )

@router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery, state: FSMContext):
    """Show detailed order information"""
    order_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    order = await get_order_details(order_id)
    
    if not order:
        text = "Buyurtma topilmadi." if lang == 'uz' else "Заказ не найден."
        await callback.answer(text)
        return
    
    details_text = "Buyurtma ma'lumotlari" if lang == 'uz' else "Детали заказа"
    client_text = "Mijoz" if lang == 'uz' else "Клиент"
    phone_text = "Telefon" if lang == 'uz' else "Телефон"
    service_text = "Xizmat" if lang == 'uz' else "Услуга"
    address_text = "Manzil" if lang == 'uz' else "Адрес"
    date_text = "Sana" if lang == 'uz' else "Дата"
    status_text = "Holat" if lang == 'uz' else "Статус"
    parts_text = "Kerakli qismlar" if lang == 'uz' else "Необходимые детали"
    
    text = f"📋 {details_text} #{order['id']}\n\n"
    text += f"👤 {client_text}: {order['client_name']}\n"
    text += f"📞 {phone_text}: {order['client_phone']}\n"
    text += f"🔧 {service_text}: {order['service_type']}\n"
    text += f"📍 {address_text}: {order['address']}\n"
    text += f"📅 {date_text}: {order['created_at']}\n"
    text += f"📊 {status_text}: {order['status']}\n"
    
    if order['parts_needed']:
        text += f"\n🔧 {parts_text}:\n{order['parts_needed']}\n"
    
    await state.update_data(current_order_id=order_id)
    await callback.message.edit_text(
        text,
        reply_markup=order_status_keyboard(user['language'], order['status'])
    )

@router.callback_query(F.data.startswith("update_order_status_"))
async def update_order_status_handler(callback: CallbackQuery, state: FSMContext):
    """Update order status"""
    new_status = callback.data.split("_")[3]
    data = await state.get_data()
    order_id = data.get('current_order_id')
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    if not order_id:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)
        return
    
    try:
        await update_zayavka_status(order_id, new_status, user['id'])
        text = "Holat yangilandi." if lang == 'uz' else "Статус обновлен."
        await callback.answer(text)
        logger.info(f"Order {order_id} status updated to {new_status} by warehouse user {user['id']}")
    except Exception as e:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.answer(text)
        logger.error(f"Order status update error: {e}")

@router.callback_query(F.data == "add_inventory_item")
async def add_inventory_item_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new inventory item"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(WarehouseStates.add_item_name)
    text = "Mahsulot nomini kiriting:" if lang == 'uz' else "Введите название товара:"
    await callback.message.edit_text(text)

@router.message(StateFilter(WarehouseStates.add_item_name))
async def add_inventory_item_name(message: Message, state: FSMContext):
    """Get inventory item name"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.update_data(item_name=message.text)
    await state.set_state(WarehouseStates.add_item_quantity)
    text = "Mahsulot miqdorini kiriting:" if lang == 'uz' else "Введите количество товара:"
    await message.answer(text)

@router.message(StateFilter(WarehouseStates.add_item_quantity))
async def add_inventory_item_quantity(message: Message, state: FSMContext):
    """Get inventory item quantity"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    try:
        quantity = int(message.text)
        await state.update_data(item_quantity=quantity)
        await state.set_state(WarehouseStates.add_item_unit)
        text = "O'lchov birligini kiriting:" if lang == 'uz' else "Введите единицу измерения:"
        await message.answer(text)
    except ValueError:
        text = "Noto'g'ri raqam." if lang == 'uz' else "Неверное число."
        await message.answer(text)

@router.message(StateFilter(WarehouseStates.add_item_unit))
async def add_inventory_item_unit(message: Message, state: FSMContext):
    """Get inventory item unit and save"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    data = await state.get_data()
    
    item_data = {
        'name': data['item_name'],
        'quantity': data['item_quantity'],
        'unit': message.text,
        'min_quantity': 5  # Default minimum quantity
    }
    
    success = await add_inventory_item(item_data)
    
    if success:
        text = "Mahsulot muvaffaqiyatli qo'shildi!" if lang == 'uz' else "Товар успешно добавлен!"
        await message.answer(
            text,
            reply_markup=warehouse_main_menu(user['language'])
        )
        logger.info(f"New inventory item added: {item_data['name']} by user {user['id']}")
    else:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await message.answer(text)
    
    await state.set_state(WarehouseStates.main_menu)

@router.callback_query(F.data == "warehouse_stats")
async def warehouse_statistics(callback: CallbackQuery, state: FSMContext):
    """Show warehouse statistics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    stats = await get_warehouse_stats()
    
    stats_text = "Warehouse statistikasi" if lang == 'uz' else "Статистика склада"
    total_items_text = "Jami mahsulotlar" if lang == 'uz' else "Всего товаров"
    low_stock_text = "Kam mahsulotlar" if lang == 'uz' else "Товары с низким запасом"
    pending_text = "Kutilayotgan buyurtmalar" if lang == 'uz' else "Ожидающие заказы"
    completed_text = "Bugun bajarilgan" if lang == 'uz' else "Завершено сегодня"
    
    text = f"📊 {stats_text}\n\n"
    text += f"📦 {total_items_text}: {stats['total_items']}\n"
    text += f"⚠️ {low_stock_text}: {stats['low_stock_items']}\n"
    text += f"📋 {pending_text}: {stats['pending_orders']}\n"
    text += f"✅ {completed_text}: {stats['completed_today']}\n"
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "warehouse_back")
async def warehouse_back(callback: CallbackQuery, state: FSMContext):
    """Go back to warehouse main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(WarehouseStates.main_menu)
    welcome_text = "Warehouse paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель склада!"
    await callback.message.edit_text(
        welcome_text,
        reply_markup=warehouse_main_menu(user['language'])
    )
