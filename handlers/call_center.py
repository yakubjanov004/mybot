from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime
#test
from database.queries import (
    get_user_by_telegram_id, create_order, get_client_by_phone,
    create_client, get_orders_by_client, 
    get_call_center_stats, get_pending_calls, create_call_log,
    search_clients, create_feedback, get_client_feedback,
    create_chat_session, get_active_chat_sessions
)
from keyboards.call_center_buttons import (
    call_center_main_menu, new_order_menu, client_search_menu,
    order_types_keyboard, call_status_keyboard,
    call_center_main_menu_reply
)
from keyboards.feedback_buttons import (
    get_rating_keyboard,
    get_feedback_comment_keyboard,
    get_feedback_complete_keyboard
)
from keyboards.support_chat_buttons import (
    get_chat_start_keyboard,
    get_chat_actions_keyboard,
    get_chat_close_confirm_keyboard
)
from states.call_center import CallCenterStates
from utils.logger import logger

router = Router()

@router.message(F.text.in_(["📞 Call Center", "📞 Колл-центр"]))
async def call_center_start(message: Message, state: FSMContext):
    """Call center main menu"""
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user or user['role'] != 'call_center':
        lang = user.get('language', 'uz')
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    await state.set_state(CallCenterStates.main_menu)
    lang = user.get('language', 'uz')
    welcome_text = "Call center paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель call center!"
    await message.answer(
        welcome_text,
        reply_markup=call_center_main_menu_reply(user['language'])
    )

@router.callback_query(F.data == "new_order")
async def new_order_start(callback: CallbackQuery, state: FSMContext):
    """Start creating new order"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(CallCenterStates.new_order_phone)
    text = "Mijoz telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона клиента:"
    await callback.message.edit_text(
        text,
        reply_markup=new_order_menu(user['language'])
    )

@router.message(StateFilter(CallCenterStates.new_order_phone))
async def get_client_phone(message: Message, state: FSMContext):
    """Get client phone and check if exists"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    phone = message.text.strip()
    
    # Validate phone format
    if not phone.startswith('+') and not phone.startswith('998'):
        text = "Noto'g'ri telefon format." if lang == 'uz' else "Неверный формат телефона."
        await message.answer(text)
        return
    
    client = await get_client_by_phone(phone)
    
    if client:
        # Existing client
        await state.update_data(client_id=client['id'], client_phone=phone)
        found_text = "Mavjud mijoz topildi:" if lang == 'uz' else "Найден существующий клиент:"
        text = f"{found_text}\n\n"
        text += f"👤 {client['full_name']}\n"
        text += f"📞 {client['phone']}\n"
        text += f"📍 {client['address']}\n"
        
        # Show client's order history
        orders = await get_orders_by_client(client['id'], limit=5)
        if orders:
            recent_text = "So'nggi buyurtmalar:" if lang == 'uz' else "Последние заказы:"
            text += f"\n📋 {recent_text}\n"
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
        text = "Mijoz ismini kiriting:" if lang == 'uz' else "Введите имя клиента:"
        await message.answer(text)

@router.message(StateFilter(CallCenterStates.new_client_name))
async def get_client_name(message: Message, state: FSMContext):
    """Get new client name"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.update_data(client_name=message.text)
    await state.set_state(CallCenterStates.new_client_address)
    text = "Mijoz manzilini kiriting:" if lang == 'uz' else "Введите адрес клиента:"
    await message.answer(text)

@router.message(StateFilter(CallCenterStates.new_client_address))
async def get_client_address(message: Message, state: FSMContext):
    """Get client address and create client"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
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
        text = "Mijoz muvaffaqiyatli yaratildi!" if lang == 'uz' else "Клиент успешно создан!"
        await message.answer(
            text,
            reply_markup=order_types_keyboard(user['language'])
        )
    else:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await message.answer(text)

@router.callback_query(F.data.startswith("service_type_"))
async def select_service_type(callback: CallbackQuery, state: FSMContext):
    """Select service type"""
    service_type = callback.data.split("_")[2]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.update_data(service_type=service_type)
    await state.set_state(CallCenterStates.order_description)
    text = "Buyurtma tavsifini kiriting:" if lang == 'uz' else "Введите описание заказа:"
    await callback.message.edit_text(text)

@router.message(StateFilter(CallCenterStates.order_description))
async def get_order_description(message: Message, state: FSMContext):
    """Get order description"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.update_data(description=message.text)
    await state.set_state(CallCenterStates.order_priority)
    text = "Buyurtma ustuvorligini tanlang:" if lang == 'uz' else "Выберите приоритет заказа:"
    await message.answer(
        text,
        reply_markup=call_status_keyboard(user['language'])
    )

@router.callback_query(F.data.startswith("priority_"))
async def set_order_priority(callback: CallbackQuery, state: FSMContext):
    """Set order priority and create order"""
    priority = callback.data.split("_")[1]
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
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
        
        success_text = "Buyurtma muvaffaqiyatli yaratildi!" if lang == 'uz' else "Заказ успешно создан!"
        order_id_text = "Buyurtma ID" if lang == 'uz' else "ID заказа"
        service_text = "Xizmat" if lang == 'uz' else "Услуга"
        priority_text = "Ustuvorlik" if lang == 'uz' else "Приоритет"
        
        text = f"✅ {success_text}\n\n"
        text += f"🆔 {order_id_text}: #{order_id}\n"
        text += f"🔧 {service_text}: {data['service_type']}\n"
        text += f"🎯 {priority_text}: {priority}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=call_center_main_menu(user['language'])
        )
        
        logger.info(f"New order #{order_id} created by call center operator {user['id']}")
    else:
        text = "Xatolik yuz berdi." if lang == 'uz' else "Произошла ошибка."
        await callback.message.edit_text(text)
    
    await state.set_state(CallCenterStates.main_menu)

@router.callback_query(F.data == "client_search")
async def client_search(callback: CallbackQuery, state: FSMContext):
    """Client search menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(CallCenterStates.client_search)
    text = "Qidiruv so'rovini kiriting:" if lang == 'uz' else "Введите поисковый запрос:"
    await callback.message.edit_text(
        text,
        reply_markup=client_search_menu(user['language'])
    )

@router.message(StateFilter(CallCenterStates.client_search))
async def search_client(message: Message, state: FSMContext):
    """Search for client"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    query = message.text.strip()
    
    # Search by phone or name
    clients = await search_clients(query)
    
    if clients:
        results_text = "Qidiruv natijalari:" if lang == 'uz' else "Результаты поиска:"
        text = f"{results_text}\n\n"
        for client in clients[:10]:  # Limit to 10 results
            text += f"👤 {client['full_name']}\n"
            text += f"📞 {client['phone']}\n"
            text += f"📍 {client['address']}\n"
            
            # Show recent orders
            orders = await get_orders_by_client(client['id'], limit=3)
            if orders:
                recent_text = "So'nggi buyurtmalar:" if lang == 'uz' else "Последние заказы:"
                text += f"📋 {recent_text}\n"
                for order in orders:
                    text += f"  • {order['service_type']} - {order['status']}\n"
            text += "\n"
    else:
        text = "Mijozlar topilmadi." if lang == 'uz' else "Клиенты не найдены."
    
    await message.answer(text)

@router.callback_query(F.data == "call_statistics")
async def call_statistics(callback: CallbackQuery, state: FSMContext):
    """Show call center statistics"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    stats = await get_call_center_stats(user['id'])
    
    stats_text = "Call center statistikasi" if lang == 'uz' else "Статистика call center"
    calls_today_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
    orders_today_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
    avg_duration_text = "O'rtacha qo'ng'iroq vaqti" if lang == 'uz' else "Среднее время звонка"
    successful_text = "Muvaffaqiyatli qo'ng'iroqlar" if lang == 'uz' else "Успешные звонки"
    conversion_text = "Konversiya darajasi" if lang == 'uz' else "Коэффициент конверсии"
    
    text = f"📊 {stats_text}\n\n"
    text += f"📞 {calls_today_text}: {stats['calls_today']}\n"
    text += f"📋 {orders_today_text}: {stats['orders_today']}\n"
    text += f"⏱️ {avg_duration_text}: {stats['avg_call_duration']} мин\n"
    text += f"✅ {successful_text}: {stats['successful_calls']}%\n"
    text += f"🎯 {conversion_text}: {stats['conversion_rate']}%\n"
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "pending_calls")
async def show_pending_calls(callback: CallbackQuery, state: FSMContext):
    """Show pending calls and callbacks"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    pending_calls = await get_pending_calls()
    
    pending_text = "Kutilayotgan qo'ng'iroqlar" if lang == 'uz' else "Ожидающие звонки"
    text = f"📞 {pending_text}\n\n"
    
    if pending_calls:
        for call in pending_calls:
            text += f"📞 {call['client_phone']} - {call['client_name']}\n"
            text += f"⏰ {call['scheduled_time']}\n"
            text += f"📝 {call['notes']}\n\n"
    else:
        text += "Kutilayotgan qo'ng'iroqlar yo'q." if lang == 'uz' else "Ожидающих звонков нет."
    
    await callback.message.edit_text(text)

@router.callback_query(F.data == "call_center_back")
async def call_center_back(callback: CallbackQuery, state: FSMContext):
    """Go back to call center main menu"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(CallCenterStates.main_menu)
    welcome_text = "Call center paneliga xush kelibsiz!" if lang == 'uz' else "Добро пожаловать в панель call center!"
    await callback.message.edit_text(
        welcome_text,
        reply_markup=call_center_main_menu(user['language'])
    )

@router.callback_query(F.data == "request_feedback")
async def request_client_feedback(callback: CallbackQuery, state: FSMContext):
    """Request feedback from client"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    data = await state.get_data()
    
    if not data.get('client_id'):
        text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
        await callback.answer(text, show_alert=True)
        return
    
    # Check if recent feedback exists
    recent_feedback = await get_client_feedback(data['client_id'])
    if recent_feedback and (datetime.now() - recent_feedback['created_at']).days < 7:
        text = "Mijoz yaqinda fikr bildirgan" if lang == 'uz' else "Клиент недавно оставил отзыв"
        await callback.answer(text, show_alert=True)
        return
    
    await state.set_state(CallCenterStates.waiting_feedback)
    text = "Mijozdan baholash so'raldi" if lang == 'uz' else "Запрошена оценка от клиента"
    await callback.message.edit_text(
        text,
        reply_markup=get_rating_keyboard(str(data['client_id']))
    )

@router.callback_query(lambda c: c.data.startswith('feedback:rate:'))
async def process_feedback_rating(callback: CallbackQuery, state: FSMContext):
    """Process feedback rating"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    _, _, request_id, rating = callback.data.split(':')
    
    await state.update_data(feedback_rating=rating)
    
    text = "Qo'shimcha izoh qoldirmoqchimisiz?" if lang == 'uz' else "Хотите оставить комментарий?"
    await callback.message.edit_text(
        text,
        reply_markup=get_feedback_comment_keyboard(request_id)
    )

@router.callback_query(lambda c: c.data.startswith('feedback:comment:'))
async def start_feedback_comment(callback: CallbackQuery, state: FSMContext):
    """Start feedback comment process"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    
    await state.set_state(CallCenterStates.feedback_comment)
    text = "Izohingizni kiriting:" if lang == 'uz' else "Введите ваш комментарий:"
    await callback.message.edit_text(text)

@router.message(StateFilter(CallCenterStates.feedback_comment))
async def save_feedback_comment(message: Message, state: FSMContext):
    """Save feedback with comment"""
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    data = await state.get_data()
    
    feedback_data = {
        'client_id': data['client_id'],
        'rating': int(data['feedback_rating']),
        'comment': message.text,
        'operator_id': user['id']
    }
    
    await create_feedback(feedback_data)
    await state.set_state(CallCenterStates.main_menu)
    
    text = "Rahmat! Fikr-mulohaza saqlandi" if lang == 'uz' else "Спасибо! Отзыв сохранен"
    await message.answer(
        text,
        reply_markup=get_feedback_complete_keyboard()
    )

@router.callback_query(F.data == "start_chat")
async def start_support_chat(callback: CallbackQuery, state: FSMContext):
    """Start support chat session"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    data = await state.get_data()
    
    if not data.get('client_id'):
        text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
        await callback.answer(text, show_alert=True)
        return
    
    # Check active chat sessions
    active_chats = await get_active_chat_sessions(data['client_id'])
    if active_chats:
        text = "Mijoz bilan faol chat mavjud" if lang == 'uz' else "Есть активный чат с клиентом"
        await callback.answer(text, show_alert=True)
        return
    
    # Create new chat session
    chat_data = {
        'client_id': data['client_id'],
        'operator_id': user['id'],
        'status': 'active'
    }
    chat_id = await create_chat_session(chat_data)
    
    if chat_id:
        await state.update_data(chat_id=chat_id)
        await state.set_state(CallCenterStates.in_chat)
        text = "Chat sessiyasi boshlandi" if lang == 'uz' else "Сессия чата начата"
        await callback.message.edit_text(
            text,
            reply_markup=get_chat_actions_keyboard(str(chat_id), str(data['client_id']))
        )
    else:
        text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await callback.answer(text, show_alert=True)

@router.message(StateFilter(CallCenterStates.in_chat))
async def process_chat_message(message: Message, state: FSMContext):
    """Process chat message"""
    data = await state.get_data()
    if not data.get('chat_id'):
        return
    
    # Here you would implement the logic to:
    # 1. Save the message to database
    # 2. Forward message to client
    # 3. Update chat status
    # This depends on your specific requirements

@router.callback_query(F.data.startswith("chat:close:"))
async def confirm_close_chat(callback: CallbackQuery, state: FSMContext):
    """Confirm closing chat"""
    user = await get_user_by_telegram_id(callback.from_user.id)
    lang = user.get('language', 'uz')
    _, _, chat_id = callback.data.split(':')
    
    text = "Chatni yopishni tasdiqlaysizmi?" if lang == 'uz' else "Подтверждаете закрытие чата?"
    await callback.message.edit_text(
        text,
        reply_markup=get_chat_close_confirm_keyboard(chat_id, str(user['id']))
    )

@router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
async def reply_new_order(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    await state.set_state(CallCenterStates.new_order_phone)
    text = "Mijoz telefon raqamini kiriting:" if lang == 'uz' else "Введите номер телефона клиента:"
    await message.answer(
        text,
        reply_markup=new_order_menu(user['language'])
    )

@router.message(F.text.in_(["🔍 Mijoz qidirish", "🔍 Поиск клиента"]))
async def reply_client_search(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    await state.set_state(CallCenterStates.client_search)
    text = "Qidiruv so'rovini kiriting:" if lang == 'uz' else "Введите поисковый запрос:"
    await message.answer(
        text,
        reply_markup=client_search_menu(user['language'])
    )

@router.message(F.text.in_(["⭐️ Baholash", "⭐️ Оценка"]))
async def reply_feedback(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    data = await state.get_data()
    if not data.get('client_id'):
        text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
        await message.answer(text)
        return
    recent_feedback = await get_client_feedback(data['client_id'])
    if recent_feedback and (datetime.now() - recent_feedback['created_at']).days < 7:
        text = "Mijoz yaqinda fikr bildirgan" if lang == 'uz' else "Клиент недавно оставил отзыв"
        await message.answer(text)
        return
    await state.set_state(CallCenterStates.waiting_feedback)
    text = "Mijozdan baholash so'raldi" if lang == 'uz' else "Запрошена оценка от клиента"
    await message.answer(
        text,
        reply_markup=get_rating_keyboard(str(data['client_id']))
    )

@router.message(F.text.in_(["💬 Chat", "💬 Чат"]))
async def reply_chat(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    data = await state.get_data()
    if not data.get('client_id'):
        text = "Avval mijozni tanlang" if lang == 'uz' else "Сначала выберите клиента"
        await message.answer(text)
        return
    active_chats = await get_active_chat_sessions(data['client_id'])
    if active_chats:
        text = "Mijoz bilan faol chat mavjud" if lang == 'uz' else "Есть активный чат с клиентом"
        await message.answer(text)
        return
    chat_data = {
        'client_id': data['client_id'],
        'operator_id': user['id'],
        'status': 'active'
    }
    chat_id = await create_chat_session(chat_data)
    if chat_id:
        await state.update_data(chat_id=chat_id)
        await state.set_state(CallCenterStates.in_chat)
        text = "Chat sessiyasi boshlandi" if lang == 'uz' else "Сессия чата начата"
        await message.answer(
            text,
            reply_markup=get_chat_actions_keyboard(str(chat_id), str(data['client_id']))
        )
    else:
        text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
        await message.answer(text)

@router.message(F.text.in_(["📊 Statistika", "📊 Статистика"]))
async def reply_statistics(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    stats = await get_call_center_stats(user['id'])
    stats_text = "Call center statistikasi" if lang == 'uz' else "Статистика call center"
    calls_today_text = "Bugungi qo'ng'iroqlar" if lang == 'uz' else "Звонки сегодня"
    orders_today_text = "Bugungi buyurtmalar" if lang == 'uz' else "Заказы сегодня"
    avg_duration_text = "O'rtacha qo'ng'iroq vaqti" if lang == 'uz' else "Среднее время звонка"
    successful_text = "Muvaffaqiyatli qo'ng'iroqlar" if lang == 'uz' else "Успешные звонки"
    conversion_text = "Konversiya darajasi" if lang == 'uz' else "Коэффициент конверсии"
    text = f"📊 {stats_text}\n\n"
    text += f"📞 {calls_today_text}: {stats['calls_today']}\n"
    text += f"📋 {orders_today_text}: {stats['orders_today']}\n"
    text += f"⏱️ {avg_duration_text}: {stats['avg_call_duration']} мин\n"
    text += f"✅ {successful_text}: {stats['successful_calls']}%\n"
    text += f"🎯 {conversion_text}: {stats['conversion_rate']}%\n"
    await message.answer(text)

@router.message(F.text.in_(["⏳ Kutilayotgan", "⏳ Ожидающие"]))
async def reply_pending_calls(message: Message, state: FSMContext):
    user = await get_user_by_telegram_id(message.from_user.id)
    lang = user.get('language', 'uz')
    if not user or user['role'] != 'call_center':
        text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
        await message.answer(text)
        return
    pending_calls = await get_pending_calls()
    pending_text = "Kutilayotgan qo'ng'iroqlar" if lang == 'uz' else "Ожидающие звонки"
    text = f"📞 {pending_text}\n\n"
    if pending_calls:
        for call in pending_calls:
            text += f"📞 {call['client_phone']} - {call['client_name']}\n"
            text += f"⏰ {call['scheduled_time']}\n"
            text += f"📝 {call['notes']}\n\n"
    else:
        text += "Kutilayotgan qo'ng'iroqlar yo'q." if lang == 'uz' else "Ожидающих звонков нет."
    await message.answer(text)
