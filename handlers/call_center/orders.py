from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    get_client_by_phone, create_client, create_order_from_call, log_call, get_pending_orders, get_order_by_id, accept_order, reject_order
)
from keyboards.call_center_buttons import (
    order_types_keyboard, call_status_keyboard, new_order_reply_menu
)
from states.call_center import CallCenterOrderStates
from utils.logger import logger
from utils.role_router import get_role_router

def get_call_center_orders_router():
    router = get_role_router("call_center")

    @router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
    async def reply_new_order(message: Message, state: FSMContext):
        """Start new order creation from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterOrderStates.new_order_phone)
        lang = user.get('language', 'uz')
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
        await message.answer(
            text,
            reply_markup=new_order_reply_menu(user['language'])
        )

    @router.callback_query(F.data == "new_order")
    async def new_order_start(callback: CallbackQuery, state: FSMContext):
        """Start creating new order"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        await state.set_state(CallCenterOrderStates.new_order_phone)
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
        await callback.message.edit_text(
            text,
            reply_markup=new_order_reply_menu(user['language'])
        )

    @router.message(StateFilter(CallCenterOrderStates.new_order_phone))
    async def get_client_phone(message: Message, state: FSMContext):
        """Get client phone and check if exists"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        phone = message.text.strip()
        
        # Validate phone format
        if not phone.startswith('998'):
            text = "❌ Noto'g'ri telefon format. Masalan: 998901234567" if lang == 'uz' else "❌ Неверный формат телефона. Например: 998901234567"
            await message.answer(text)
            return
        
        try:
            client = await get_client_by_phone(phone)
            
            if client:
                # Existing client
                await state.update_data(client_id=client['id'], client_phone=phone)
                found_text = "✅ Mavjud mijoz topildi:" if lang == 'uz' else "✅ Найден существующий клиент:"
                text = f"{found_text}\n\n"
                text += f"👤 {client['full_name']}\n"
                text += f"📞 {client['phone_number']}\n"
                if client.get('address'):
                    text += f"📍 {client['address']}\n"
                
                # Show client's order history
                from database.call_center_queries import get_orders_by_client
                orders = await get_orders_by_client(client['id'], limit=3)
                if orders:
                    recent_text = "📋 So'nggi buyurtmalar:" if lang == 'uz' else "📋 Последние заказы:"
                    text += f"\n{recent_text}\n"
                    for order in orders:
                        status_emoji = "✅" if order['status'] == 'completed' else "⏳" if order['status'] in ['new', 'pending'] else "🔧"
                        text += f"{status_emoji} {order.get('zayavka_type', 'Xizmat')} - {order['status']}\n"
                
                await state.set_state(CallCenterOrderStates.select_service_type)
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
            else:
                # New client
                await state.update_data(client_phone=phone)
                await state.set_state(CallCenterOrderStates.new_client_name)
                text = "👤 Yangi mijoz. Ismini kiriting:" if lang == 'uz' else "👤 Новый клиент. Введите имя:"
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error getting client by phone: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(CallCenterOrderStates.new_client_name))
    async def get_client_name(message: Message, state: FSMContext):
        """Get new client name"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(client_name=message.text.strip())
        await state.set_state(CallCenterOrderStates.new_client_address)
        text = "📍 Mijoz manzilini kiriting:" if lang == 'uz' else "📍 Введите адрес клиента:"
        await message.answer(text)

    @router.message(StateFilter(CallCenterOrderStates.new_client_address))
    async def get_client_address(message: Message, state: FSMContext):
        """Get client address and create client"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        data = await state.get_data()
        
        try:
            client_data = {
                'full_name': data['client_name'],
                'phone_number': data['client_phone'],
                'address': message.text.strip(),
                'language': user['language']
            }
            
            client_id = await create_client(client_data)
            
            if client_id:
                await state.update_data(client_id=client_id)
                await state.set_state(CallCenterOrderStates.select_service_type)
                text = "✅ Mijoz muvaffaqiyatli yaratildi!\n\n🔧 Xizmat turini tanlang:" if lang == 'uz' else "✅ Клиент успешно создан!\n\n🔧 Выберите тип услуги:"
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
            else:
                text = "❌ Mijozni yaratishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при создании клиента."
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.callback_query(F.data.startswith("service_type_"))
    async def select_service_type(callback: CallbackQuery, state: FSMContext):
        """Select service type"""
        service_type = callback.data.split("_", 2)[2]
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(service_type=service_type)
        await state.set_state(CallCenterOrderStates.order_description)
        text = "📝 Buyurtma tavsifini kiriting:" if lang == 'uz' else "📝 Введите описание заказа:"
        await callback.message.edit_text(text)

    @router.message(StateFilter(CallCenterOrderStates.order_description))
    async def get_order_description(message: Message, state: FSMContext):
        """Get order description"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(description=message.text.strip())
        await state.set_state(CallCenterOrderStates.order_priority)
        text = "🎯 Buyurtma ustuvorligini tanlang:" if lang == 'uz' else "🎯 Выберите приоритет заказа:"
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
        
        try:
            order_data = {
                'client_id': data['client_id'],
                'service_type': data['service_type'],
                'description': data['description'],
                'phone_number': data['client_phone'],
                'status': 'new',
                'created_by': user['id']
            }
            
            order_id = await create_order_from_call(order_data)
            
            if order_id:
                # Log the call
                call_log_data = {
                    'user_id': data['client_id'],
                    'phone_number': data['client_phone'],
                    'duration': 0,  # Will be updated later
                    'result': 'order_created',
                    'notes': f"Order #{order_id} created",
                    'created_by': user['id']
                }
                await log_call(call_log_data)
                
                success_text = "✅ Buyurtma muvaffaqiyatli yaratildi!" if lang == 'uz' else "✅ Заказ успешно создан!"
                order_id_text = "Buyurtma ID" if lang == 'uz' else "ID заказа"
                service_text = "Xizmat" if lang == 'uz' else "Услуга"
                priority_text = "Ustuvorlik" if lang == 'uz' else "Приоритет"
                
                text = f"{success_text}\n\n"
                text += f"🆔 {order_id_text}: #{order_id}\n"
                text += f"🔧 {service_text}: {data['service_type']}\n"
                text += f"🎯 {priority_text}: {priority}\n"
                text += f"📞 Telefon: {data['client_phone']}"
                
                await callback.message.edit_text(text)
                
                logger.info(f"New order #{order_id} created by call center operator {user['id']}")
            else:
                text = "❌ Buyurtmani yaratishda xatolik yuz berdi." if lang == 'uz' else "❌ Ошибка при создании заказа."
                await callback.message.edit_text(text)
            
            await state.set_state(CallCenterOrderStates.main_menu)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    @router.message(F.text.in_(["⏳ Kutilayotgan", "⏳ Ожидающие"]))
    async def show_pending_orders(message: Message, state: FSMContext):
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        orders = await get_pending_orders()
        if orders:
            text = ("⏳ Kutilayotgan buyurtmalar:\n\n" if lang == 'uz' else "⏳ Ожидающие заказы:\n\n")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"#{order['id']} | {order['client_name']} | 🕒 {order['created_at'].strftime('%H:%M')}",
                        callback_data=f"pending_order_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=("Qabul qilish" if lang == 'uz' else "Принять"),
                        callback_data=f"accept_order_{order['id']}"
                    )
                ] for order in orders
            ] + [[InlineKeyboardButton(text=("Orqaga" if lang == 'uz' else "Назад"), callback_data="pending_orders_back")]])
            await message.answer(text, reply_markup=keyboard)
        else:
            text = ("📭 Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет ожидающих заказов")
            await message.answer(text)

    @router.callback_query(F.data.startswith("pending_order_"))
    async def show_pending_order_details(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        order = await get_order_by_id(order_id)
        if not order:
            await callback.answer(("Buyurtma topilmadi" if lang == 'uz' else "Заказ не найден"), show_alert=True)
            return
        text = (
            f"🆔 Buyurtma ID: #{order['id']}\n"
            f"👤 Mijoz: {order['client_name']}\n"
            f"📞 Telefon: {order['phone_number']}\n"
            f"📝 Tavsif: {order['description']}\n"
            f"🕒 Yaratilgan: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            if lang == 'uz' else
            f"🆔 ID заказа: #{order['id']}\n"
            f"👤 Клиент: {order['client_name']}\n"
            f"📞 Телефон: {order['phone_number']}\n"
            f"📝 Описание: {order['description']}\n"
            f"🕒 Создан: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=("Qabul qilish" if lang == 'uz' else "Принять"),
                    callback_data=f"accept_order_{order['id']}"
                ),
                InlineKeyboardButton(
                    text=("Bekor qilish" if lang == 'uz' else "Отклонить"),
                    callback_data=f"reject_order_{order['id']}"
                ),
                InlineKeyboardButton(
                    text=("Orqaga" if lang == 'uz' else "Назад"),
                    callback_data="pending_orders_back"
                )
            ]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)

    @router.callback_query(F.data.startswith("accept_order_"))
    async def accept_pending_order(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        success = await accept_order(order_id, user['id'])
        if success:
            text = ("✅ Buyurtma qabul qilindi!" if lang == 'uz' else "✅ Заказ принят!")
        else:
            text = ("❌ Buyurtmani qabul qilib bo‘lmadi." if lang == 'uz' else "❌ Не удалось принять заказ.")
        await callback.answer(text, show_alert=True)
        # Optionally, refresh the pending orders list

    @router.callback_query(F.data.startswith("reject_order_"))
    async def reject_pending_order(callback: CallbackQuery, state: FSMContext):
        order_id = int(callback.data.split("_")[-1])
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        success = await reject_order(order_id, user['id'])
        if success:
            text = ("❌ Buyurtma bekor qilindi!" if lang == 'uz' else "❌ Заказ отклонён!")
        else:
            text = ("❌ Buyurtmani bekor qilib bo‘lmadi." if lang == 'uz' else "❌ Не удалось отклонить заказ.")
        await callback.answer(text, show_alert=True)
        # Optionally, refresh the pending orders list

    @router.callback_query(F.data == "pending_orders_back")
    async def back_to_pending_orders(callback: CallbackQuery, state: FSMContext):
        # Re-show the pending orders list
        user = await get_user_by_telegram_id(callback.from_user.id)
        lang = user.get('language', 'uz')
        orders = await get_pending_orders()
        if orders:
            text = ("⏳ Kutilayotgan buyurtmalar:\n\n" if lang == 'uz' else "⏳ Ожидающие заказы:\n\n")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"#{order['id']} | {order['client_name']} | 🕒 {order['created_at'].strftime('%H:%M')}",
                        callback_data=f"pending_order_{order['id']}"
                    ),
                    InlineKeyboardButton(
                        text=("Qabul qilish" if lang == 'uz' else "Принять"),
                        callback_data=f"accept_order_{order['id']}"
                    )
                ] for order in orders
            ] + [[InlineKeyboardButton(text=("Orqaga" if lang == 'uz' else "Назад"), callback_data="pending_orders_back")]])
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            text = ("📭 Kutilayotgan buyurtmalar yo'q" if lang == 'uz' else "📭 Нет ожидающих заказов")
            await callback.message.edit_text(text)

    return router
