from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.queries import (
    get_user_by_telegram_id, get_orders_by_status, update_order_status,
    get_inventory_items, update_inventory_item, add_inventory_item,
    get_order_details, get_warehouse_stats
)
from keyboards.warehouse_buttons import (
    warehouse_main_menu, inventory_menu, orders_menu,
    order_status_keyboard, inventory_actions_keyboard
)
from states.warehouse_states import WarehouseStates
from utils.i18n import get_text
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📦 Warehouse", "📦 Склад", "📦 Ombor"]))
async def warehouse_start(message: Message, state: FSMContext):
    """Warehouse main menu"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        await message.answer(get_text("access_denied", user['language'] if user else 'ru'))
        return
    
    await state.set_state(WarehouseStates.main_menu)
    await message.answer(
        get_text("warehouse_welcome", user['language']),
        reply_markup=warehouse_main_menu(user['language'])
    )

@router.callback_query(F.data == "warehouse_inventory")
async def warehouse_inventory(callback: CallbackQuery, state: FSMContext):
    """Show inventory management"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    inventory_items = await get_inventory_items()
    
    text = get_text("inventory_list", user['language']) + "\n\n"
    for item in inventory_items:
        status = "✅" if item['quantity'] > item['min_quantity'] else "⚠️"
        text += f"{status} {item['name']}: {item['quantity']} {item['unit']}\n"
    
    await state.set_state(WarehouseStates.inventory_menu)
    await callback.message.edit_text(
        text,
        reply_markup=inventory_menu(user['language'])
    )

@router.callback_query(F.data == "warehouse_orders")
async def warehouse_orders(callback: CallbackQuery, state: FSMContext):
    """Show orders for warehouse processing"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    orders = await get_orders_by_status(['confirmed', 'in_progress'])
    
    text = get_text("warehouse_orders", user['language']) + "\n\n"
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
    order = await get_order_details(order_id)
    
    if not order:
        await callback.answer(get_text("order_not_found", user['language']))
        return
    
    text = f"📋 {get_text('order_details', user['language'])} #{order['id']}\n\n"
    text += f"👤 {get_text('client', user['language'])}: {order['client_name']}\n"
    text += f"📞 {get_text('phone', user['language'])}: {order['client_phone']}\n"
    text += f"🔧 {get_text('service', user['language'])}: {order['service_type']}\n"
    text += f"📍 {get_text('address', user['language'])}: {order['address']}\n"
    text += f"📅 {get_text('date', user['language'])}: {order['created_at']}\n"
    text += f"📊 {get_text('status', user['language'])}: {order['status']}\n"
    
    if order['parts_needed']:
        text += f"\n🔧 {get_text('parts_needed', user['language'])}:\n{order['parts_needed']}\n"
    
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
    
    if not order_id:
        await callback.answer(get_text("error_occurred", user['language']))
        return
    
    success = await update_order_status(order_id, new_status, user['id'])
    
    if success:
        await callback.answer(get_text("status_updated", user['language']))
        logger.info(f"Order {order_id} status updated to {new_status} by warehouse user {user['id']}")
    else:
        await callback.answer(get_text("error_occurred", user['language']))

@router.callback_query(F.data == "add_inventory_item")
async def add_inventory_item_start(callback: CallbackQuery, state: FSMContext):
    """Start adding new inventory item"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(WarehouseStates.add_item_name)
    await callback.message.edit_text(
        get_text("enter_item_name", user['language'])
    )

@router.message(StateFilter(WarehouseStates.add_item_name))
async def add_inventory_item_name(message: Message, state: FSMContext):
    """Get inventory item name"""
    user = await get_user_by_telegram_id(message.from_user.id)
    
    await state.update_data(item_name=message.text)
    await state.set_state(WarehouseStates.add_item_quantity)
    await message.answer(get_text("enter_item_quantity", user['language']))

@router.message(StateFilter(WarehouseStates.add_item_quantity))
async def add_inventory_item_quantity(message: Message, state: FSMContext):
    """Get inventory item quantity"""
    user = await get_user_by_telegram_id(message.from_user.id)
    
    try:
        quantity = int(message.text)
        await state.update_data(item_quantity=quantity)
        await state.set_state(WarehouseStates.add_item_unit)
        await message.answer(get_text("enter_item_unit", user['language']))
    except ValueError:
        await message.answer(get_text("invalid_number", user['language']))

@router.message(StateFilter(WarehouseStates.add_item_unit))
async def add_inventory_item_unit(message: Message, state: FSMContext):
    """Get inventory item unit and save"""
    user = await get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    
    item_data = {
        'name': data['item_name'],
        'quantity': data['item_quantity'],
        'unit': message.text,
        'min_quantity': 5  # Default minimum quantity
    }
    
    success = await add_inventory_item(item_data)
    
    if success:
        await message.answer(
            get_text("item_added_successfully", user['language']),
            reply_markup=warehouse_main_menu(user['language'])
        )
        logger.info(f"New inventory item added: {item_data['name']} by user {user['id']}")
    else:
        await message.answer(get_text("error_occurred", user['language']))
    
    await state.set_state(WarehouseStates.main_menu)

@router.callback_query(F.data == "warehouse_stats")
async def warehouse_statistics(callback: CallbackQuery, state: FSMContext):
    """Show warehouse statistics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    stats = await get_warehouse_stats()
    
    text = f"📊 {get_text('warehouse_statistics', user['language'])}\n\n"
    text += f"📦 {get_text('total_items', user['language'])}: {stats['total_items']}\n"
    text += f"⚠️ {get_text('low_stock_items', user['language'])}: {stats['low_stock_items']}\n"
    text += f"📋 {get_text('pending_orders', user['language'])}: {stats['pending_orders']}\n"
    text += f"✅ {get_text('completed_today', user['language'])}: {stats['completed_today']}\n"
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "warehouse_back")
async def warehouse_back(callback: CallbackQuery, state: FSMContext):
    """Go back to warehouse main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(WarehouseStates.main_menu)
    await callback.message.edit_text(
        get_text("warehouse_welcome", user['language']),
        reply_markup=warehouse_main_menu(user['language'])
    )
