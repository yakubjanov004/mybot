from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.queries import (
    get_user_by_telegram_id, get_all_orders, get_technician_performance,
    get_system_statistics, get_orders_by_date_range, assign_order_to_technician,
    get_all_technicians, get_order_details, update_order_priority,
    get_orders_by_status, assign_zayavka_to_technician
)
from keyboards.controllers_buttons import (
    controllers_main_menu, orders_control_menu, technicians_menu,
    reports_menu, order_priority_keyboard, technician_assignment_keyboard
)
from states.controllers_states import ControllersStates
from utils.i18n import get_text
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["🎛️ Controller", "🎛️ Контроллер", "🎛️ Nazoratchi"]))
async def controllers_start(message: Message, state: FSMContext):
    """Controllers main menu"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'controller':
        await message.answer(get_text("access_denied", user['language'] if user else 'ru'))
        return
    
    await state.set_state(ControllersStates.main_menu)
    await message.answer(
        get_text("controllers_welcome", user['language']),
        reply_markup=controllers_main_menu(user['language'])
    )

@router.callback_query(F.data == "orders_control")
async def orders_control(callback: CallbackQuery, state: FSMContext):
    """Orders control and monitoring"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    orders = await get_all_orders(limit=20)
    
    text = get_text("orders_overview", user['language']) + "\n\n"
    
    status_counts = {}
    for order in orders:
        status = order['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        text += f"• {get_text(f'status_{status}', user['language'])}: {count}\n"
    
    text += "\n" + get_text("recent_orders", user['language']) + ":\n"
    for order in orders[:10]:
        priority_icon = "🔴" if order.get('priority') == 'high' else "🟡" if order.get('priority') == 'medium' else "🟢"
        text += f"{priority_icon} #{order['id']} - {order['client_name']} ({order['status']})\n"
    
    await state.set_state(ControllersStates.orders_control)
    await callback.message.edit_text(
        text,
        reply_markup=orders_control_menu(user['language'])
    )

@router.callback_query(F.data == "technicians_control")
async def technicians_control(callback: CallbackQuery, state: FSMContext):
    """Technicians performance monitoring"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    technicians = await get_all_technicians()
    
    text = get_text("technicians_overview", user['language']) + "\n\n"
    
    for tech in technicians:
        performance = await get_technician_performance(tech['id'])
        status_icon = "🟢" if tech['is_active'] else "🔴"
        text += f"{status_icon} {tech['full_name']}\n"
        text += f"   📋 {get_text('active_orders', user['language'])}: {performance['active_orders']}\n"
        text += f"   ✅ {get_text('completed_today', user['language'])}: {performance['completed_today']}\n"
        text += f"   ⭐ {get_text('rating', user['language'])}: {performance['avg_rating']:.1f}\n\n"
    
    await state.set_state(ControllersStates.technicians_control)
    await callback.message.edit_text(
        text,
        reply_markup=technicians_menu(user['language'])
    )

@router.callback_query(F.data == "system_reports")
async def system_reports(callback: CallbackQuery, state: FSMContext):
    """System reports and analytics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    stats = await get_system_statistics()
    
    text = f"📊 {get_text('system_reports', user['language'])}\n\n"
    text += f"📈 {get_text('total_orders', user['language'])}: {stats['total_orders']}\n"
    text += f"✅ {get_text('completed_orders', user['language'])}: {stats['completed_orders']}\n"
    text += f"⏳ {get_text('pending_orders', user['language'])}: {stats['pending_orders']}\n"
    text += f"👥 {get_text('active_clients', user['language'])}: {stats['active_clients']}\n"
    text += f"🔧 {get_text('active_technicians', user['language'])}: {stats['active_technicians']}\n"
    text += f"💰 {get_text('revenue_today', user['language'])}: {stats['revenue_today']} сум\n"
    text += f"📅 {get_text('avg_completion_time', user['language'])}: {stats['avg_completion_time']} ч\n"
    
    await state.set_state(ControllersStates.reports_menu)
    await callback.message.edit_text(
        text,
        reply_markup=reports_menu(user['language'])
    )

@router.callback_query(F.data.startswith("order_priority_"))
async def order_priority_control(callback: CallbackQuery, state: FSMContext):
    """Control order priorities"""
    order_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(callback.from_user.id)
    order = await get_order_details(order_id)
    
    if not order:
        await callback.answer(get_text("order_not_found", user['language']))
        return
    
    text = f"🎯 {get_text('order_priority_control', user['language'])} #{order['id']}\n\n"
    text += f"👤 {get_text('client', user['language'])}: {order['client_name']}\n"
    text += f"🔧 {get_text('service', user['language'])}: {order['service_type']}\n"
    text += f"📊 {get_text('current_priority', user['language'])}: {order.get('priority', 'normal')}\n"
    text += f"📅 {get_text('created', user['language'])}: {order['created_at']}\n"
    
    await state.update_data(current_order_id=order_id)
    await callback.message.edit_text(
        text,
        reply_markup=order_priority_keyboard(user['language'])
    )

@router.callback_query(F.data.startswith("set_priority_"))
async def set_order_priority(callback: CallbackQuery, state: FSMContext):
    """Set order priority"""
    priority = callback.data.split("_")[2]
    data = await state.get_data()
    order_id = data.get('current_order_id')
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    if not order_id:
        await callback.answer(get_text("error_occurred", user['language']))
        return
    
    success = await update_order_priority(order_id, priority)
    
    if success:
        await callback.answer(get_text("priority_updated", user['language']))
        logger.info(f"Order {order_id} priority updated to {priority} by controller {user['id']}")
    else:
        await callback.answer(get_text("error_occurred", user['language']))

@router.callback_query(F.data == "assign_technicians")
async def assign_technicians_menu(callback: CallbackQuery, state: FSMContext):
    """Show technician assignment menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    unassigned_orders = await get_orders_by_status(['new', 'pending'])
    
    text = get_text("unassigned_orders", user['language']) + "\n\n"
    for order in unassigned_orders:
        text += f"🔹 #{order['id']} - {order['client_name']}\n"
        text += f"   {order['service_type']} - {order['address']}\n\n"
    
    await state.set_state(ControllersStates.assign_technicians)
    await callback.message.edit_text(text)

@router.callback_query(F.data.startswith("assign_order_"))
async def assign_order_to_tech(callback: CallbackQuery, state: FSMContext):
    """Assign order to technician"""
    order_id = int(callback.data.split("_")[2])
    user = await get_user_by_telegram_id(callback.from_user.id)
    technicians = await get_all_technicians(available_only=True)
    
    text = f"👨‍🔧 {get_text('select_technician', user['language'])} #{order_id}:\n\n"
    
    await state.update_data(assign_order_id=order_id)
    await callback.message.edit_text(
        text,
        reply_markup=technician_assignment_keyboard(user['language'], technicians)
    )

@router.callback_query(F.data.startswith("assign_tech_"))
async def confirm_technician_assignment(callback: CallbackQuery, state: FSMContext):
    """Confirm technician assignment"""
    tech_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    order_id = data.get('assign_order_id')
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    if not order_id:
        await callback.answer(get_text("error_occurred", user['language']))
        return
    
    success = await assign_order_to_technician(order_id, tech_id)
    
    if success:
        await callback.answer(get_text("technician_assigned", user['language']))
        logger.info(f"Order {order_id} assigned to technician {tech_id} by controller {user['id']}")
    else:
        await callback.answer(get_text("error_occurred", user['language']))

@router.callback_query(F.data == "controllers_back")
async def controllers_back(callback: CallbackQuery, state: FSMContext):
    """Go back to controllers main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(ControllersStates.main_menu)
    await callback.message.edit_text(
        get_text("controllers_welcome", user['language']),
        reply_markup=controllers_main_menu(user['language'])
    )
