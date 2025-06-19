from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.queries import (
    get_user_by_telegram_id, create_order, get_client_by_phone,
    create_client, get_orders_by_client, update_order_status,
    get_call_center_stats, get_pending_calls, create_call_log,
    search_clients
)
from keyboards.call_center_buttons import (
    call_center_main_menu, new_order_menu, client_search_menu,
    order_types_keyboard, call_status_keyboard
)
from states.call_center import CallCenterStates
from utils.i18n import get_text
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📞 Call Center", "📞 Колл-центр", "📞 Qo'ng'iroq markazi"]))
async def call_center_start(message: Message, state: FSMContext):
    """Call center main menu"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'call_center':
        await message.answer(get_text("access_denied", user['language'] if user else 'ru'))
        return
    
    await state.set_state(CallCenterStates.main_menu)
    await message.answer(
        get_text("call_center_welcome", user['language']),
        reply_markup=call_center_main_menu(user['language'])
    )

@router.callback_query(F.data == "new_order")
async def new_order_start(callback: CallbackQuery, state: FSMContext):
    """Start creating new order"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(CallCenterStates.new_order_phone)
    await callback.message.edit_text(
        get_text("enter_client_phone", user['language']),
        reply_markup=new_order_menu(user['language'])
    )

@router.message(StateFilter(CallCenterStates.new_order_phone))
async def get_client_phone(message: Message, state: FSMContext):
    """Get client phone and check if exists"""
    user = await get_user_by_telegram_id(message.from_user.id)
    phone = message.text.strip()
    
    # Validate phone format
    if not phone.startswith('+') and not phone.startswith('998'):
        await message.answer(get_text("invalid_phone_format", user['language']))
        return
    
    client = await get_client_by_phone(phone)
    
    if client:
        # Existing client
        await state.update_data(client_id=client['id'], client_phone=phone)
        text = f"{get_text('existing_client_found', user['language'])}:\n\n"
        text += f"👤 {client['full_name']}\n"
        text += f"📞 {client['phone']}\n"
        text += f"📍 {client['address']}\n"
        
        # Show client's order history
        orders = await get_orders_by_client(client['id'], limit=5)
        if orders:
            text += f"\n📋 {get_text('recent_orders', user['language'])}:\n"
            for order in orders:
                text += f"• {order['service_type']} - {order['status']} ({order['created_at']})\n"
        
        await state.set_state(CallCenterStates.select_service_type)
        await message.answer(
            text,
            reply_markup=order_types_keyboard(user['language'])
        )
    else:
        # New client
        await state.update_data(client_phone=phone)
        await state.set_state(CallCenterStates.new_client_name)
        await message.answer(get_text("enter_client_name", user['language']))

@router.message(StateFilter(CallCenterStates.new_client_name))
async def get_client_name(message: Message, state: FSMContext):
    """Get new client name"""
    user = await get_user_by_telegram_id(message.from_user.id)
    
    await state.update_data(client_name=message.text)
    await state.set_state(CallCenterStates.new_client_address)
    await message.answer(get_text("enter_client_address", user['language']))

@router.message(StateFilter(CallCenterStates.new_client_address))
async def get_client_address(message: Message, state: FSMContext):
    """Get client address and create client"""
    user = await get_user_by_telegram_id(message.from_user.id)
    data = await state.get_data()
    
    client_data = {
        'full_name': data['client_name'],
        'phone': data['client_phone'],
        'address': message.text,
        'language': user['language']
    }
    
    client_id = await create_client(client_data)
    
    if client_id:
        await state.update_data(client_id=client_id)
        await state.set_state(CallCenterStates.select_service_type)
        await message.answer(
            get_text("client_created_successfully", user['language']),
            reply_markup=order_types_keyboard(user['language'])
        )
    else:
        await message.answer(get_text("error_occurred", user['language']))

@router.callback_query(F.data.startswith("service_type_"))
async def select_service_type(callback: CallbackQuery, state: FSMContext):
    """Select service type"""
    service_type = callback.data.split("_")[2]
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.update_data(service_type=service_type)
    await state.set_state(CallCenterStates.order_description)
    await callback.message.edit_text(
        get_text("enter_order_description", user['language'])
    )

@router.message(StateFilter(CallCenterStates.order_description))
async def get_order_description(message: Message, state: FSMContext):
    """Get order description"""
    user = await get_user_by_telegram_id(message.from_user.id)
    
    await state.update_data(description=message.text)
    await state.set_state(CallCenterStates.order_priority)
    await message.answer(
        get_text("select_order_priority", user['language']),
        reply_markup=call_status_keyboard(user['language'])
    )

@router.callback_query(F.data.startswith("priority_"))
async def set_order_priority(callback: CallbackQuery, state: FSMContext):
    """Set order priority and create order"""
    priority = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    data = await state.get_data()
    
    order_data = {
        'client_id': data['client_id'],
        'service_type': data['service_type'],
        'description': data['description'],
        'priority': priority,
        'status': 'new',
        'created_by': user['id']
    }
    
    order_id = await create_order(order_data)
    
    if order_id:
        # Log the call
        call_log_data = {
            'client_phone': data['client_phone'],
            'operator_id': user['id'],
            'call_type': 'incoming',
            'result': 'order_created',
            'order_id': order_id
        }
        await create_call_log(call_log_data)
        
        text = f"✅ {get_text('order_created_successfully', user['language'])}\n\n"
        text += f"🆔 {get_text('order_id', user['language'])}: #{order_id}\n"
        text += f"🔧 {get_text('service', user['language'])}: {data['service_type']}\n"
        text += f"🎯 {get_text('priority', user['language'])}: {priority}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=call_center_main_menu(user['language'])
        )
        
        logger.info(f"New order #{order_id} created by call center operator {user['id']}")
    else:
        await callback.message.edit_text(get_text("error_occurred", user['language']))
    
    await state.set_state(CallCenterStates.main_menu)

@router.callback_query(F.data == "client_search")
async def client_search(callback: CallbackQuery, state: FSMContext):
    """Client search menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(CallCenterStates.client_search)
    await callback.message.edit_text(
        get_text("enter_search_query", user['language']),
        reply_markup=client_search_menu(user['language'])
    )

@router.message(StateFilter(CallCenterStates.client_search))
async def search_client(message: Message, state: FSMContext):
    """Search for client"""
    user = await get_user_by_telegram_id(message.from_user.id)
    query = message.text.strip()
    
    # Search by phone or name
    clients = await search_clients(query)
    
    if clients:
        text = f"{get_text('search_results', user['language'])}:\n\n"
        for client in clients[:10]:  # Limit to 10 results
            text += f"👤 {client['full_name']}\n"
            text += f"📞 {client['phone']}\n"
            text += f"📍 {client['address']}\n"
            
            # Show recent orders
            orders = await get_orders_by_client(client['id'], limit=3)
            if orders:
                text += f"📋 {get_text('recent_orders', user['language'])}:\n"
                for order in orders:
                    text += f"  • {order['service_type']} - {order['status']}\n"
            text += "\n"
    else:
        text = get_text("no_clients_found", user['language'])
    
    await message.answer(text)

@router.callback_query(F.data == "call_statistics")
async def call_statistics(callback: CallbackQuery, state: FSMContext):
    """Show call center statistics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    stats = await get_call_center_stats(user['id'])
    
    text = f"📊 {get_text('call_center_statistics', user['language'])}\n\n"
    text += f"📞 {get_text('calls_today', user['language'])}: {stats['calls_today']}\n"
    text += f"📋 {get_text('orders_created_today', user['language'])}: {stats['orders_today']}\n"
    text += f"⏱️ {get_text('avg_call_duration', user['language'])}: {stats['avg_call_duration']} мин\n"
    text += f"✅ {get_text('successful_calls', user['language'])}: {stats['successful_calls']}%\n"
    text += f"🎯 {get_text('conversion_rate', user['language'])}: {stats['conversion_rate']}%\n"
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "pending_calls")
async def show_pending_calls(callback: CallbackQuery, state: FSMContext):
    """Show pending calls and callbacks"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    pending_calls = await get_pending_calls()
    
    text = f"📞 {get_text('pending_calls', user['language'])}\n\n"
    
    if pending_calls:
        for call in pending_calls:
            text += f"📞 {call['client_phone']} - {call['client_name']}\n"
            text += f"⏰ {call['scheduled_time']}\n"
            text += f"📝 {call['notes']}\n\n"
    else:
        text += get_text("no_pending_calls", user['language'])
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "call_center_back")
async def call_center_back(callback: CallbackQuery, state: FSMContext):
    """Go back to call center main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    
    await state.set_state(CallCenterStates.main_menu)
    await callback.message.edit_text(
        get_text("call_center_welcome", user['language']),
        reply_markup=call_center_main_menu(user['language'])
    )
