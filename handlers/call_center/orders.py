from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from database.base_queries import get_user_by_telegram_id
from database.call_center_queries import (
    get_client_by_phone, create_client, create_order_from_call, log_call
)
from keyboards.call_center_buttons import (
    new_order_menu, order_types_keyboard, call_status_keyboard
)
from states.call_center import CallCenterStates
from utils.logger import logger

def get_call_center_orders_router():
    router = Router()

    @router.message(F.text.in_(["🆕 Yangi buyurtma", "🆕 Новый заказ"]))
    async def reply_new_order(message: Message, state: FSMContext):
        """Start new order creation from reply keyboard"""
        user = await get_user_by_telegram_id(message.from_user.id)
        if not user or user['role'] != 'call_center':
            lang = user.get('language', 'uz') if user else 'uz'
            text = "Sizda ruxsat yo'q." if lang == 'uz' else "У вас нет доступа."
            await message.answer(text)
            return
        
        await state.set_state(CallCenterStates.new_order_phone)
        lang = user.get('language', 'uz')
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
        await message.answer(
            text,
            reply_markup=new_order_menu(user['language'])
        )

    @router.callback_query(F.data == "new_order")
    async def new_order_start(callback: CallbackQuery, state: FSMContext):
        """Start creating new order"""
        user = await get_user_by_telegram_id(callback.from_user.id)
        if not user or user['role'] != 'call_center':
            await callback.answer("Access denied", show_alert=True)
            return
        
        lang = user.get('language', 'uz')
        
        await state.set_state(CallCenterStates.new_order_phone)
        text = "📞 Mijoz telefon raqamini kiriting:" if lang == 'uz' else "📞 Введите номер телефона клиента:"
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
            text = "❌ Noto'g'ri telefon format. Masalan: +998901234567" if lang == 'uz' else "❌ Неверный формат телефона. Например: +998901234567"
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
                
                await state.set_state(CallCenterStates.select_service_type)
                await message.answer(
                    text,
                    reply_markup=order_types_keyboard(user['language'])
                )
            else:
                # New client
                await state.update_data(client_phone=phone)
                await state.set_state(CallCenterStates.new_client_name)
                text = "👤 Yangi mijoz. Ismini kiriting:" if lang == 'uz' else "👤 Новый клиент. Введите имя:"
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error getting client by phone: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await message.answer(error_text)

    @router.message(StateFilter(CallCenterStates.new_client_name))
    async def get_client_name(message: Message, state: FSMContext):
        """Get new client name"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(client_name=message.text.strip())
        await state.set_state(CallCenterStates.new_client_address)
        text = "📍 Mijoz manzilini kiriting:" if lang == 'uz' else "📍 Введите адрес клиента:"
        await message.answer(text)

    @router.message(StateFilter(CallCenterStates.new_client_address))
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
                await state.set_state(CallCenterStates.select_service_type)
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
        await state.set_state(CallCenterStates.order_description)
        text = "📝 Buyurtma tavsifini kiriting:" if lang == 'uz' else "📝 Введите описание заказа:"
        await callback.message.edit_text(text)

    @router.message(StateFilter(CallCenterStates.order_description))
    async def get_order_description(message: Message, state: FSMContext):
        """Get order description"""
        user = await get_user_by_telegram_id(message.from_user.id)
        lang = user.get('language', 'uz')
        
        await state.update_data(description=message.text.strip())
        await state.set_state(CallCenterStates.order_priority)
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
            
            await state.set_state(CallCenterStates.main_menu)
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            error_text = "Xatolik yuz berdi" if lang == 'uz' else "Произошла ошибка"
            await callback.message.edit_text(error_text)
            await callback.answer()

    return router
